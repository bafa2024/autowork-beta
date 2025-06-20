import asyncio
from datetime import datetime, timedelta
from typing import Set, List, Dict
import json
import os
from rich.console import Console
from rich.live import Live
from rich.table import Table

from autowork import AutoWork
from utils import log_info, log_error, log_success
from config import settings

console = Console()

class RealtimeMonitor:
    def __init__(self):
        self.seen_projects: Set[int] = set()
        self.stats = {
            "projects_checked": 0,
            "new_projects_found": 0,
            "bids_attempted": 0,
            "bids_successful": 0,
            "start_time": datetime.now()
        }
        self.load_seen_projects()
    
    def load_seen_projects(self):
        """Load previously seen projects"""
        if os.path.exists("seen_projects.json"):
            with open("seen_projects.json", "r") as f:
                data = json.load(f)
                self.seen_projects = set(data)
    
    def save_seen_projects(self):
        """Save seen projects to file"""
        recent_projects = list(self.seen_projects)[-10000:]
        with open("seen_projects.json", "w") as f:
            json.dump(recent_projects, f)
    
    def generate_status_table(self) -> Table:
        """Generate status table for display"""
        table = Table(title="AutoWork Realtime Monitor")
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        runtime = datetime.now() - self.stats["start_time"]
        table.add_row("Runtime", str(runtime).split('.')[0])
        table.add_row("Projects Checked", str(self.stats["projects_checked"]))
        table.add_row("New Projects Found", str(self.stats["new_projects_found"]))
        table.add_row("Bids Attempted", str(self.stats["bids_attempted"]))
        table.add_row("Bids Successful", str(self.stats["bids_successful"]))
        
        if self.stats["bids_attempted"] > 0:
            success_rate = (self.stats["bids_successful"] / self.stats["bids_attempted"]) * 100
            table.add_row("Success Rate", f"{success_rate:.1f}%")
        
        return table
    
    async def check_for_new_projects(self, autowork: AutoWork) -> List[Dict]:
        """Check for new projects"""
        all_projects = []
        
        priority_skills = settings.priority_skills[:5]
        
        for skill in priority_skills:
            projects = await autowork.fetch_projects(skill, limit=20)
            all_projects.extend(projects)
            await asyncio.sleep(1)
        
        new_projects = []
        for project in all_projects:
            if project["id"] not in self.seen_projects:
                self.seen_projects.add(project["id"])
                new_projects.append(project)
                
                time_submitted = datetime.fromtimestamp(project.get("time_submitted", 0))
                project_age = datetime.now() - time_submitted
                
                if project_age < timedelta(minutes=settings.bid_immediately_threshold_minutes):
                    project["is_very_new"] = True
        
        self.stats["projects_checked"] += len(all_projects)
        self.stats["new_projects_found"] += len(new_projects)
        
        return new_projects
    
    async def process_new_project(self, autowork: AutoWork, project: Dict):
        """Process a new project"""
        log_info(f"\n[NEW] {project['title']}")
        log_info(f"Budget: ${project['budget']['minimum']} - ${project['budget']['maximum']}")
        log_info(f"Skills: {', '.join([j['name'] for j in project['jobs'][:5]])}")
        
        await autowork.save_project(project, "realtime")
        
        if not autowork.should_bid_on_project(project):
            log_info("→ Skipping: Doesn't meet criteria")
            return
        
        if project.get("is_very_new", False):
            log_success("→ VERY NEW PROJECT! Bidding immediately...")
            self.stats["bids_attempted"] += 1
            
            result = await autowork.place_bid(project)
            if result["success"]:
                self.stats["bids_successful"] += 1
                log_success(f"→ ✓ BID PLACED! ID: {result['bid_id']}")
            else:
                log_error(f"→ ✗ Bid failed: {result['error']}")
    
    async def run(self):
        """Run the realtime monitor"""
        async with AutoWork() as autowork:
            with Live(self.generate_status_table(), refresh_per_second=1) as live:
                while True:
                    try:
                        new_projects = await self.check_for_new_projects(autowork)
                        
                        for project in new_projects:
                            await self.process_new_project(autowork, project)
                        
                        live.update(self.generate_status_table())
                        
                        if len(self.seen_projects) % 100 == 0:
                            self.save_seen_projects()
                        
                        await asyncio.sleep(settings.check_interval_seconds)
                        
                    except Exception as e:
                        log_error(f"Monitor error: {e}")
                        await asyncio.sleep(60)

async def main():
    monitor = RealtimeMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())