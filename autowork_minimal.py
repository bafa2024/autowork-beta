#!/usr/bin/env python3
"""
AutoWork Bot - Minimal Version for Render Deployment
This version runs without external dependencies like Discord
Updated to bid on all projects equally with auto NDA/IP signing
"""

import os
import sys
import json
import time
import logging
import requests
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AutoWorkMinimal:
    def __init__(self):
        self.token = self.load_token()
        self.user_id = os.environ.get('FREELANCER_USER_ID', '45214417')
        self.api_base = "https://www.freelancer.com/api"
        self.headers = {
            "Freelancer-OAuth-V1": self.token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Initialize Redis connection (optional)
        self.redis_client = self.init_redis()
        
        # Bid message templates
        self.bid_messages = self.load_bid_messages()
        
        # Skills mapping
        self.skills_map = self.load_skills_map()
        
        # Tracking
        self.processed_projects = set()
        self.bid_count = 0
        self.elite_bid_count = 0
        self.nda_signed_projects = set()
        self.ip_signed_projects = set()
        self.last_bid_time = 0
        self.start_time = datetime.now()
        self.bids_today = 0
        self.today_date = datetime.now().date()
        
        # Configuration
        self.config = {
            'delivery_days': 4,  # Constant 4-day delivery
            'auto_sign_nda': True,  # Auto-sign NDA
            'auto_sign_ip': True,   # Auto-sign IP agreements
            'min_bid_delay': 5,     # Seconds between bids
        }
        
        # Load state from Redis if available
        self.load_state_from_redis()
        
        logging.info(f"✓ Bot initialized for user ID: {self.user_id}")
        logging.info(f"✓ Auto-sign NDA: ON")
        logging.info(f"✓ Auto-sign IP: ON")
        logging.info(f"✓ Delivery time: {self.config['delivery_days']} days")

    def init_redis(self):
        """Initialize Redis connection if available"""
        redis_url = os.environ.get('REDIS_URL')
        if redis_url:
            try:
                client = redis.from_url(redis_url, decode_responses=True)
                client.ping()
                logging.info("✓ Connected to Redis")
                return client
            except Exception as e:
                logging.warning(f"Redis connection failed: {e}. Running without Redis.")
        return None

    def load_state_from_redis(self):
        """Load saved state from Redis"""
        if self.redis_client:
            try:
                # Load counters
                self.bid_count = int(self.redis_client.get('total_bids') or 0)
                self.elite_bid_count = int(self.redis_client.get('elite_bids') or 0)
                self.bids_today = int(self.redis_client.get('bids_today') or 0)
                
                # Load processed projects
                processed = self.redis_client.get('processed_projects')
                if processed:
                    self.processed_projects = set(json.loads(processed))
                
                # Load NDA/IP signed projects
                nda_signed = self.redis_client.get('nda_signed_projects')
                if nda_signed:
                    self.nda_signed_projects = set(json.loads(nda_signed))
                    
                ip_signed = self.redis_client.get('ip_signed_projects')
                if ip_signed:
                    self.ip_signed_projects = set(json.loads(ip_signed))
                
                # Check if we need to reset daily counter
                last_reset = self.redis_client.get('last_daily_reset')
                if last_reset:
                    last_reset_date = datetime.fromisoformat(last_reset).date()
                    if last_reset_date < self.today_date:
                        self.reset_daily_stats()
                else:
                    self.reset_daily_stats()
                
                logging.info(f"✓ Loaded state: {self.bid_count} total bids ({self.elite_bid_count} elite), {self.bids_today} today")
            except Exception as e:
                logging.error(f"Error loading state from Redis: {e}")

    def save_state_to_redis(self):
        """Save current state to Redis"""
        if self.redis_client:
            try:
                # Save counters
                self.redis_client.set('total_bids', self.bid_count)
                self.redis_client.set('elite_bids', self.elite_bid_count)
                self.redis_client.set('bids_today', self.bids_today)
                self.redis_client.set('processed_projects_count', len(self.processed_projects))
                
                # Save processed projects (limit to last 1000)
                recent_projects = list(self.processed_projects)[-1000:]
                self.redis_client.set('processed_projects', json.dumps(recent_projects))
                
                # Save NDA/IP signed projects
                self.redis_client.set('nda_signed_projects', json.dumps(list(self.nda_signed_projects)))
                self.redis_client.set('ip_signed_projects', json.dumps(list(self.ip_signed_projects)))
                
                # Save status
                self.redis_client.set('bot_status', 'Running')
                self.redis_client.set('last_update', datetime.now().isoformat())
                
                # Calculate and save uptime
                uptime = datetime.now() - self.start_time
                uptime_str = str(uptime).split('.')[0]  # Remove microseconds
                self.redis_client.set('bot_uptime', uptime_str)
                
                # Calculate success rate (simplified - assumes all bids are successful for now)
                success_rate = 100.0 if self.bid_count > 0 else 0.0
                self.redis_client.set('success_rate', success_rate)
                
                # Elite project stats
                elite_percentage = (self.elite_bid_count / self.bid_count * 100) if self.bid_count > 0 else 0
                self.redis_client.set('elite_percentage', elite_percentage)
                
            except Exception as e:
                logging.error(f"Error saving state to Redis: {e}")

    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.bids_today = 0
        self.today_date = datetime.now().date()
        if self.redis_client:
            self.redis_client.set('bids_today', 0)
            self.redis_client.set('last_daily_reset', datetime.now().isoformat())

    def load_bid_messages(self) -> List[str]:
        """Load bid messages from file or use defaults"""
        messages_file = "bid_messages.json"
        
        if os.path.exists(messages_file):
            try:
                with open(messages_file, 'r') as f:
                    messages = json.load(f)
                    logging.info(f"✓ Loaded {len(messages)} bid messages from file")
                    return messages
            except Exception as e:
                logging.error(f"Error loading bid messages: {e}")
        
        # Default messages - will use the full list from bid_messages.json
        return [
            "Hi! I've carefully reviewed your project requirements and I'm confident I can deliver excellent results. With my experience in {skills}, I can start immediately and complete your project efficiently. I'd love to discuss your specific needs in more detail. Looking forward to working with you!",
            "Hello! Your project caught my attention as it perfectly matches my expertise in {skills}. I have successfully completed similar projects and can ensure high-quality delivery within your timeline. I'm available to start right away. Let's discuss how I can help bring your vision to life!"
        ]

    def load_skills_map(self) -> Dict[int, str]:
        """Load skills mapping"""
        skills_file = "skills_map.json"
        
        if os.path.exists(skills_file):
            try:
                with open(skills_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading skills map: {e}")
        
        # Default skills map (common skill IDs)
        return {
            "3": "PHP",
            "9": "Data Entry",
            "13": "Python",
            "17": "Web Scraping",
            "22": "Excel"
        }

    def load_token(self) -> str:
        """Load token from environment variable or .env file"""
        # First, try to get from environment variable
        token = os.environ.get('FREELANCER_OAUTH_TOKEN')
        
        if token:
            logging.info("✓ Token loaded from environment variable")
            return token.strip()
        
        # Try to load from .env file
        if os.path.exists('.env'):
            try:
                # Try using python-dotenv if available
                from dotenv import load_dotenv
                load_dotenv()
                token = os.environ.get('FREELANCER_OAUTH_TOKEN')
                if token:
                    logging.info("✓ Token loaded from .env file via dotenv")
                    return token.strip()
            except ImportError:
                # Fallback to manual parsing if python-dotenv not available
                with open('.env', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('FREELANCER_OAUTH_TOKEN='):
                            token = line.split('=', 1)[1].strip()
                            if token:
                                logging.info("✓ Token loaded from .env file")
                                return token
        
        # In non-interactive environments (like Render), we can't ask for input
        if os.environ.get('RENDER') or not sys.stdin.isatty():
            raise ValueError(
                "FREELANCER_OAUTH_TOKEN not found! "
                "Please set it as an environment variable in Render dashboard."
            )
        
        # Only ask for input in interactive environments
        logging.warning("Token not found in environment or .env file.")
        token = input("Enter your Freelancer OAuth token: ").strip()
        
        # Save to .env file for future use
        try:
            with open('.env', 'w') as f:
                f.write(f"FREELANCER_OAUTH_TOKEN={token}\n")
            logging.info("✓ Token saved to .env file")
        except Exception as e:
            logging.error(f"Error saving token to .env: {e}")
        
        return token

    def is_elite_project(self, project: Dict) -> bool:
        """Check if a project is an elite project (has special flags)"""
        # Check for upgrade flags
        upgrades = project.get('upgrades', {})
        
        # Elite projects typically have these flags
        is_elite = (
            upgrades.get('featured', False) or
            upgrades.get('sealed', False) or
            upgrades.get('NDA', False) or
            upgrades.get('ip_contract', False) or
            upgrades.get('non_compete', False) or
            upgrades.get('project_management', False) or
            upgrades.get('qualified', False)
        )
        
        # Also check project type
        project_type = project.get('type', {}).get('name', '').lower()
        if 'recruit' in project_type or 'premium' in project_type:
            is_elite = True
        
        # Check if it's explicitly marked as requiring NDA
        if project.get('nda_details', {}).get('required', False):
            is_elite = True
        
        return is_elite

    def get_project_details(self, project: Dict) -> Dict:
        """Extract detailed information about a project"""
        upgrades = project.get('upgrades', {})
        
        details = {
            'id': project['id'],
            'title': project['title'],
            'is_elite': self.is_elite_project(project),
            'featured': upgrades.get('featured', False),
            'sealed': upgrades.get('sealed', False),
            'nda': upgrades.get('NDA', False),
            'ip_contract': upgrades.get('ip_contract', False),
            'non_compete': upgrades.get('non_compete', False),
            'urgent': upgrades.get('urgent', False),
            'qualified': upgrades.get('qualified', False),
            'budget': project.get('budget', {}),
            'bid_count': project.get('bid_stats', {}).get('bid_count', 0),
            'avg_bid': project.get('bid_stats', {}).get('bid_avg', 0)
        }
        
        return details

    def check_and_sign_nda(self, project_id: int) -> bool:
        """Check if project requires NDA and sign it"""
        try:
            # Check NDA status
            endpoint = f"{self.api_base}/projects/0.1/projects/{project_id}/nda"
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                nda_data = response.json().get('result', {})
                
                if nda_data.get('status') == 'unsigned':
                    # Sign the NDA
                    sign_endpoint = f"{self.api_base}/projects/0.1/projects/{project_id}/nda/sign"
                    sign_response = requests.post(sign_endpoint, headers=self.headers, json={})
                    
                    if sign_response.status_code in [200, 201]:
                        self.nda_signed_projects.add(project_id)
                        logging.info(f"✅ Successfully signed NDA for project {project_id}")
                        return True
                    else:
                        logging.error(f"Failed to sign NDA for project {project_id}: {sign_response.status_code}")
                        return False
                
                elif nda_data.get('status') == 'signed':
                    self.nda_signed_projects.add(project_id)
                    logging.info(f"ℹ️ NDA already signed for project {project_id}")
                    return True
            
            return True  # No NDA required or already handled
            
        except Exception as e:
            logging.error(f"Error checking/signing NDA for project {project_id}: {e}")
            return True  # Don't skip the project due to error

    def check_and_sign_ip_agreement(self, project_id: int) -> bool:
        """Check if project requires IP agreement and sign it"""
        try:
            # Check IP agreement status
            endpoint = f"{self.api_base}/projects/0.1/projects/{project_id}/ip_contract"
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                ip_data = response.json().get('result', {})
                
                if ip_data.get('status') == 'unsigned':
                    # Sign the IP agreement
                    sign_endpoint = f"{self.api_base}/projects/0.1/projects/{project_id}/ip_contract/sign"
                    sign_response = requests.post(sign_endpoint, headers=self.headers, json={})
                    
                    if sign_response.status_code in [200, 201]:
                        self.ip_signed_projects.add(project_id)
                        logging.info(f"✅ Successfully signed IP agreement for project {project_id}")
                        return True
                    else:
                        logging.error(f"Failed to sign IP agreement for project {project_id}: {sign_response.status_code}")
                        return False
                
                elif ip_data.get('status') == 'signed':
                    self.ip_signed_projects.add(project_id)
                    logging.info(f"ℹ️ IP agreement already signed for project {project_id}")
                    return True
            
            return True  # No IP agreement required or already handled
            
        except Exception as e:
            logging.error(f"Error checking/signing IP agreement for project {project_id}: {e}")
            return True  # Don't skip the project due to error

    def get_active_projects(self, limit: int = 30) -> List[Dict]:
        """Fetch active projects"""
        try:
            endpoint = f"{self.api_base}/projects/0.1/projects/active"
            params = {
                "limit": limit,
                "job_details": "true",
                "full_description": "true",
                "upgrade_details": "true",  # Important for elite detection
                "compact": "false"
            }
            
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                projects = data.get("result", {}).get("projects", [])
                
                # Count elite projects for logging
                elite_count = sum(1 for p in projects if self.is_elite_project(p))
                logging.info(f"✓ Fetched {len(projects)} projects ({elite_count} elite, {len(projects) - elite_count} regular)")
                
                return projects
            else:
                logging.error(f"Error fetching projects: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Exception fetching projects: {e}")
            if self.redis_client:
                self.redis_client.set('last_error', str(e))
            return []

    def calculate_bid_amount(self, budget: Dict, is_elite: bool = False) -> float:
        """Calculate bid amount based on budget"""
        if budget.get("minimum"):
            min_amount = float(budget["minimum"])
            max_amount = float(budget.get("maximum", min_amount * 1.5))
            
            # Bid 10-20% above minimum for all projects
            if is_elite:
                bid_amount = min_amount * 1.2  # 20% above minimum for elite
            else:
                bid_amount = min_amount * 1.15  # 15% above minimum for regular
            
            # Ensure within range
            return min(bid_amount, max_amount)
        
        return 150.0 if is_elite else 100.0  # Default bid

    def format_bid_description(self, project: Dict, is_elite: bool = False) -> str:
        """Format bid description with project skills"""
        import random
        
        # Get project skills
        project_skills = []
        for job in project.get("jobs", []):
            skill_name = self.skills_map.get(str(job["id"]), job.get("name", ""))
            if skill_name:
                project_skills.append(skill_name)
        
        skills_text = ", ".join(project_skills[:3]) if project_skills else "relevant skills"
        
        # Select random message
        message = random.choice(self.bid_messages)
        
        # Add note about NDA/IP if it's an elite project
        if is_elite:
            elite_suffix = "\n\nI understand this project may require signing NDA/IP agreements, and I'm ready to proceed with any necessary documentation."
            message = message.format(skills=skills_text) + elite_suffix
        else:
            message = message.format(skills=skills_text)
        
        return message

    def place_bid(self, project: Dict) -> bool:
        """Place a bid on a project with 4-day delivery"""
        try:
            project_id = project["id"]
            
            # Skip if already processed
            if project_id in self.processed_projects:
                return False
            
            # Check if it's a new day
            if datetime.now().date() > self.today_date:
                self.reset_daily_stats()
            
            # Get project details
            details = self.get_project_details(project)
            is_elite = details['is_elite']
            
            # Check and sign NDA if required
            if details.get('nda', False):
                self.check_and_sign_nda(project_id)
            
            # Check and sign IP agreement if required
            if details.get('ip_contract', False):
                self.check_and_sign_ip_agreement(project_id)
            
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_bid_time < self.config['min_bid_delay']:
                time.sleep(self.config['min_bid_delay'] - (current_time - self.last_bid_time))
            
            # Prepare bid data with constant 4-day delivery
            bid_data = {
                "project_id": project_id,
                "bidder_id": int(self.user_id),
                "amount": self.calculate_bid_amount(project.get("budget", {}), is_elite),
                "period": self.config['delivery_days'],  # Constant 4 days
                "milestone_percentage": 100,
                "description": self.format_bid_description(project, is_elite)
            }
            
            endpoint = f"{self.api_base}/projects/0.1/bids"
            
            response = requests.post(endpoint, headers=self.headers, json=bid_data)
            
            if response.status_code in [200, 201]:
                self.processed_projects.add(project_id)
                self.bid_count += 1
                self.bids_today += 1
                if is_elite:
                    self.elite_bid_count += 1
                self.last_bid_time = time.time()
                
                project_type = "🌟 ELITE" if is_elite else "Regular"
                logging.info(f"✅ {project_type} bid placed on: {project['title'][:50]}...")
                logging.info(f"   Amount: ${bid_data['amount']}, Delivery: {bid_data['period']} days")
                logging.info(f"   Total bids: {self.bid_count} (Elite: {self.elite_bid_count}), Today: {self.bids_today}")
                
                # Log elite project details
                if is_elite:
                    flags = []
                    if details['featured']: flags.append("Featured")
                    if details['sealed']: flags.append("Sealed")
                    if details['nda']: flags.append("NDA")
                    if details['ip_contract']: flags.append("IP Contract")
                    if details['urgent']: flags.append("Urgent")
                    logging.info(f"   Elite flags: {', '.join(flags)}")
                
                # Save bid to Redis
                if self.redis_client:
                    bid_key = f"bid:{int(time.time()*1000)}"
                    bid_info = {
                        "project_id": project_id,
                        "project_title": project['title'][:100],
                        "amount": bid_data['amount'],
                        "delivery_days": bid_data['period'],
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "is_elite": is_elite,
                        "elite_flags": flags if is_elite else []
                    }
                    self.redis_client.set(bid_key, json.dumps(bid_info))
                    self.redis_client.expire(bid_key, 86400)  # Expire after 24 hours
                    self.redis_client.set('last_bid_time', datetime.now().isoformat())
                
                # Save state
                self.save_state_to_redis()
                
                return True
            else:
                logging.error(f"❌ Failed to bid on {project_id}: {response.status_code}")
                if response.text:
                    logging.error(f"   Response: {response.text[:200]}")
                
                if self.redis_client:
                    self.redis_client.set('last_error', f"Bid failed: {response.status_code}")
                
                return False
                
        except Exception as e:
            logging.error(f"Exception placing bid: {e}")
            if self.redis_client:
                self.redis_client.set('last_error', str(e))
            return False

    def realtime_monitor_with_bidding(self):
        """Monitor and bid continuously on all projects"""
        logging.info("🚀 Starting real-time monitoring with auto-bidding...")
        logging.info(f"User ID: {self.user_id}")
        logging.info(f"Mode: Bidding on ALL projects (elite and regular)")
        logging.info(f"Delivery time: {self.config['delivery_days']} days for all projects")
        logging.info(f"Auto-sign NDA: ON | Auto-sign IP: ON")
        
        error_count = 0
        max_errors = 5
        
        # Update Redis status
        if self.redis_client:
            self.redis_client.set('bot_status', 'Running')
            self.redis_client.set('bot_start_time', self.start_time.isoformat())
            self.redis_client.set('bot_mode', 'All projects')
        
        while True:
            try:
                # Fetch active projects
                projects = self.get_active_projects(limit=50)
                
                if projects:
                    new_projects = 0
                    elite_bids = 0
                    
                    # Process all projects in the order they were fetched
                    for project in projects:
                        if project["id"] not in self.processed_projects:
                            new_projects += 1
                            
                            # Auto bid on the project
                            success = self.place_bid(project)
                            
                            if success:
                                if self.is_elite_project(project):
                                    elite_bids += 1
                                # Small delay between bids
                                time.sleep(2)
                    
                    if new_projects == 0:
                        logging.info("No new projects found in this cycle")
                    elif elite_bids > 0:
                        logging.info(f"📊 Placed {elite_bids} elite bids this cycle")
                    
                    error_count = 0  # Reset error count on success
                else:
                    error_count += 1
                    logging.warning(f"No projects fetched (error count: {error_count}/{max_errors})")
                    
                    if error_count >= max_errors:
                        logging.error("Max errors reached. Waiting 5 minutes before retry...")
                        time.sleep(300)  # 5 minutes
                        error_count = 0
                
                # Save state periodically
                self.save_state_to_redis()
                
                # Wait before next cycle
                elite_percentage = (self.elite_bid_count / self.bid_count * 100) if self.bid_count > 0 else 0
                logging.info(f"💤 Waiting 30 seconds... (Total: {self.bid_count}, Elite: {self.elite_bid_count} [{elite_percentage:.1f}%], Today: {self.bids_today})")
                time.sleep(30)
                
            except KeyboardInterrupt:
                logging.info("Monitoring stopped by user")
                if self.redis_client:
                    self.redis_client.set('bot_status', 'Stopped')
                break
            except Exception as e:
                error_count += 1
                logging.error(f"Error in monitoring loop: {e}")
                
                if self.redis_client:
                    self.redis_client.set('last_error', str(e))
                
                if error_count >= max_errors:
                    logging.error("Too many errors. Waiting 5 minutes...")
                    time.sleep(300)
                    error_count = 0
                else:
                    time.sleep(30)

if __name__ == "__main__":
    # For testing locally
    bot = AutoWorkMinimal()
    bot.realtime_monitor_with_bidding()