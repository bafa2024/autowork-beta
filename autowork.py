import asyncio
import aiohttp
from typing import List, Dict, Optional  # This line should be there
from datetime import datetime, timedelta
import random
import json
from rich.console import Console
from rich.table import Table
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import Project, Bid, init_db
from rate_limiter import RateLimiter
from utils import log_info, log_error, log_success

console = Console()

class AutoWork:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.db_engine = None
        self.db_session = None
        self.rate_limiter = RateLimiter(
            settings.api_rate_limit_per_second,
            settings.api_rate_limit_per_hour,
            settings.api_rate_limit_per_day
        )
        self.base_url = "https://www.freelancer.com/api"
        self.headers = {
            "Freelancer-OAuth-V1": settings.freelancer_oauth_token
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self.db_engine, self.db_session = await init_db(settings.database_url)
        await self.rate_limiter.load_tracking()
        return self
        
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
        if self.db_engine:
            await self.db_engine.dispose()
    
    async def fetch_projects(self, query: str, limit: int = 100) -> List[Dict]:
        """Fetch projects for a specific query"""
        can_request, reason = await self.rate_limiter.can_make_request()
        if not can_request:
            log_error(f"Rate limited: {reason}")
            return []
        
        params = {
            "query": query,
            "limit": limit,
            "offset": 0,
            "job_details": True,
            "user_details": True,
            "full_description": True,
            "user_reputation": True,
            "countries[]": settings.target_countries,
            "min_avg_price": settings.min_project_budget,
            "sort_field": "time_submitted",
            "compact": True
        }
        
        try:
            await self.rate_limiter.record_request()
            
            async with self.session.get(
                f"{self.base_url}/projects/0.1/projects/active/",
                headers=self.headers,
                params=params
            ) as response:
                
                if response.status == 429:
                    log_error("API rate limited (429)")
                    return []
                
                if response.status != 200:
                    log_error(f"API error: {response.status}")
                    return []
                
                data = await response.json()
                projects = data.get("result", {}).get("projects", [])
                
                log_success(f"Fetched {len(projects)} projects for '{query}'")
                return projects
                
        except Exception as e:
            log_error(f"Error fetching projects: {e}")
            return []
    
    async def fetch_all_projects(self) -> List[Dict]:
        """Fetch projects for all priority skills"""
        all_projects = []
        seen_ids = set()
        
        # Create tasks for concurrent fetching
        tasks = []
        for skill in settings.priority_skills:
            task = self.fetch_projects(skill)
            tasks.append(task)
            
            # Batch requests to avoid overwhelming the API
            if len(tasks) >= 5:
                results = await asyncio.gather(*tasks)
                for projects in results:
                    for project in projects:
                        if project["id"] not in seen_ids:
                            all_projects.append(project)
                            seen_ids.add(project["id"])
                
                tasks = []
                await asyncio.sleep(2)  # Delay between batches
        
        # Process remaining tasks
        if tasks:
            results = await asyncio.gather(*tasks)
            for projects in results:
                for project in projects:
                    if project["id"] not in seen_ids:
                        all_projects.append(project)
                        seen_ids.add(project["id"])
        
        return all_projects
    
    def is_elite_project(self, project: Dict) -> bool:
        """Determine if a project is elite"""
        budget_min = project.get("budget", {}).get("minimum", 0)
        
        # Elite criteria
        if budget_min >= 500:
            return True
        
        if project.get("upgrades", {}).get("featured", False):
            return True
            
        if project.get("upgrades", {}).get("urgent", False):
            return True
            
        return False
    
    def should_bid_on_project(self, project: Dict) -> bool:
        """Determine if we should bid on this project"""
        # Check budget
        budget_min = project.get("budget", {}).get("minimum", 0)
        if budget_min < settings.min_project_budget:
            return False
        
        # Check bid count
        bid_count = project.get("bid_stats", {}).get("bid_count", 0)
        if bid_count > settings.max_existing_bids:
            return False
        
        # Check age
        time_submitted = project.get("time_submitted", 0)
        project_age = datetime.now() - datetime.fromtimestamp(time_submitted)
        if project_age > timedelta(hours=24):
            return False
        
        # Check skills match
        project_skills = [job["name"].lower() for job in project.get("jobs", [])]
        our_skills = [skill.lower() for skill in settings.priority_skills]
        
        matching_skills = set(project_skills) & set(our_skills)
        return len(matching_skills) > 0
    
    async def save_project(self, project: Dict, search_keyword: str):
        """Save project to database"""
        async with self.db_session() as session:
            # Check if project already exists
            existing = await session.execute(
                select(Project).where(Project.project_id == project["id"])
            )
            if existing.scalar_one_or_none():
                return
            
            # Create new project record
            db_project = Project(
                project_id=project["id"],
                title=project.get("title", ""),
                description=project.get("description", ""),
                budget_min=project.get("budget", {}).get("minimum", 0),
                budget_max=project.get("budget", {}).get("maximum", 0),
                currency=project.get("currency", {}).get("code", "USD"),
                bid_count=project.get("bid_stats", {}).get("bid_count", 0),
                skills=[job["name"] for job in project.get("jobs", [])],
                country=project.get("location", {}).get("country", {}).get("name", ""),
                search_keyword=search_keyword,
                is_elite=self.is_elite_project(project),
                time_submitted=datetime.fromtimestamp(project.get("time_submitted", 0)),
                raw_data=project
            )
            
            session.add(db_project)
            await session.commit()
    
    def calculate_bid_amount(self, project: Dict) -> float:
        """Calculate appropriate bid amount - always bid at minimum budget"""
        budget_min = project.get("budget", {}).get("minimum", 0)
        
        # Always bid at the minimum budget amount
        return budget_min
    
    def generate_bid_description(self, project: Dict) -> str:
        """Generate bid description"""
        skills = [job["name"] for job in project.get("jobs", [])][:3]
        skills_text = ", ".join(skills)
        
        template = random.choice(settings.bid_templates)
        return template.format(skills=skills_text)
    
    def estimate_project_duration(self, project: Dict) -> int:
        """Estimate project duration in days"""
        budget = project.get("budget", {}).get("minimum", 0)
        
        if budget < 100:
            return 3
        elif budget < 200:
            return 5
        elif budget < 500:
            return 7
        elif budget < 1000:
            return 10
        else:
            return 14
    
    async def place_bid(self, project: Dict) -> Dict:
        """Place a bid on a project"""
        can_request, reason = await self.rate_limiter.can_make_request()
        if not can_request:
            return {"success": False, "error": f"Rate limited: {reason}"}
        
        bid_data = {
            "project_id": project["id"],
            "bidder_id": settings.freelancer_user_id,
            "amount": self.calculate_bid_amount(project),
            "period": self.estimate_project_duration(project),
            "milestone_percentage": 100,
            "description": self.generate_bid_description(project)
        }
        
        try:
            await self.rate_limiter.record_request()
            
            async with self.session.post(
                f"{self.base_url}/projects/0.1/bids/",
                headers={**self.headers, "Content-Type": "application/json"},
                json=bid_data
            ) as response:
                
                response_data = await response.json()
                
                # Save bid record
                async with self.db_session() as session:
                    db_bid = Bid(
                        project_id=project["id"],
                        bid_id=response_data.get("result", {}).get("id"),
                        amount=bid_data["amount"],
                        period=bid_data["period"],
                        description=bid_data["description"],
                        status="success" if response.status in [200, 201] else "failed",
                        response_data=response_data
                    )
                    session.add(db_bid)
                    await session.commit()
                
                if response.status in [200, 201]:
                    log_success(f"✓ Bid placed on: {project['title']}")
                    return {"success": True, "bid_id": response_data.get("result", {}).get("id")}
                else:
                    log_error(f"✗ Failed to bid: {response_data.get('message', 'Unknown error')}")
                    return {"success": False, "error": response_data.get("message", "Unknown error")}
                    
        except Exception as e:
            log_error(f"Error placing bid: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_unbid_projects(self, limit: int = 10) -> List[Dict]:
        """Get projects we haven't bid on yet"""
        async with self.db_session() as session:
            # Get projects without bids
            result = await session.execute(
                select(Project)
                .outerjoin(Bid, Project.project_id == Bid.project_id)
                .where(
                    and_(
                        Bid.id.is_(None),
                        Project.created_at > datetime.now() - timedelta(hours=24)
                    )
                )
                .order_by(Project.is_elite.desc(), Project.created_at.desc())
                .limit(limit)
            )
            
            projects = result.scalars().all()
            return [p.raw_data for p in projects]
    
    async def process_batch_fetch(self):
        """Fetch and store projects in batch mode"""
        log_info("Starting batch project fetch...")
        
        projects = await self.fetch_all_projects()
        
        # Save projects to database
        for project in projects:
            for skill in settings.priority_skills:
                project_skills = [job["name"].lower() for job in project.get("jobs", [])]
                if skill.lower() in project_skills:
                    await self.save_project(project, skill)
                    break
        
        log_success(f"Batch fetch complete. Processed {len(projects)} projects.")
        
        # Show summary
        await self.show_summary()
    
    async def process_batch_bid(self, max_bids: int = 5):
        """Place bids on unbid projects"""
        log_info(f"Starting batch bid process (max: {max_bids})...")
        
        # Get unbid projects
        projects = await self.get_unbid_projects(max_bids)
        
        if not projects:
            log_info("No unbid projects found.")
            return
        
        # Filter projects we should bid on
        eligible_projects = [p for p in projects if self.should_bid_on_project(p)]
        
        log_info(f"Found {len(eligible_projects)} eligible projects to bid on.")
        
        # Place bids
        success_count = 0
        for project in eligible_projects:
            result = await self.place_bid(project)
            if result["success"]:
                success_count += 1
            
            # Small delay between bids
            await asyncio.sleep(2)
        
        log_success(f"Batch bid complete. Successfully bid on {success_count} projects.")
    
    async def show_summary(self):
        """Show current system summary"""
        async with self.db_session() as session:
            # Get counts
            total_projects = await session.execute(
                select(Project).count()
            )
            total_count = total_projects.scalar()
            
            today_projects = await session.execute(
                select(Project)
                .where(Project.created_at > datetime.now() - timedelta(days=1))
                .count()
            )
            today_count = today_projects.scalar()
            
            total_bids = await session.execute(
                select(Bid).count()
            )
            bid_count = total_bids.scalar()
            
            successful_bids = await session.execute(
                select(Bid)
                .where(Bid.status == "success")
                .count()
            )
            success_count = successful_bids.scalar()
        
        # Create summary table
        table = Table(title="AutoWork Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Projects", str(total_count))
        table.add_row("Projects (24h)", str(today_count))
        table.add_row("Total Bids", str(bid_count))
        table.add_row("Successful Bids", str(success_count))
        
        # Add rate limit status
        status = await self.rate_limiter.get_status()
        table.add_row("API Calls (Hour)", f"{status['requests_last_hour']}/{settings.api_rate_limit_per_hour}")
        table.add_row("API Calls (Day)", f"{status['requests_last_day']}/{settings.api_rate_limit_per_day}")
        
        console.print(table)