#!/usr/bin/env python3
"""
AutoWork Bot - Minimal Version for Render Deployment
This version runs without external dependencies like Discord
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime
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
        
        # Bid message templates
        self.bid_messages = self.load_bid_messages()
        
        # Skills mapping
        self.skills_map = self.load_skills_map()
        
        # Tracking
        self.processed_projects = set()
        self.bid_count = 0
        self.last_bid_time = 0
        
        logging.info(f"✓ Bot initialized for user ID: {self.user_id}")

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
        
        # Default messages
        default_messages = [
            "Hi! I've carefully reviewed your project requirements and I'm confident I can deliver excellent results. With my experience in {skills}, I can start immediately and complete your project efficiently. I'd love to discuss your specific needs in more detail. Looking forward to working with you!",
            
            "Hello! Your project caught my attention as it perfectly matches my expertise in {skills}. I have successfully completed similar projects and can ensure high-quality delivery within your timeline. I'm available to start right away. Let's discuss how I can help bring your vision to life!",
            
            "Greetings! I'm very interested in your project and have the exact skills you need in {skills}. I pride myself on clear communication, timely delivery, and exceeding client expectations. I'm ready to begin immediately and would appreciate the opportunity to discuss your project further.",
            
            "Hi there! I've read through your project details and I'm excited about the opportunity to work with you. My strong background in {skills} makes me an ideal candidate for this job. I'm committed to delivering quality work on time and within budget. Let's connect to discuss your requirements!",
            
            "Hello! Your project aligns perfectly with my skill set in {skills}. I have a proven track record of delivering similar projects successfully. I'm detail-oriented, responsive, and dedicated to client satisfaction. I'm available to start immediately and look forward to contributing to your project's success!"
        ]
        
        # Save default messages for future use
        try:
            with open(messages_file, 'w') as f:
                json.dump(default_messages, f, indent=2)
            logging.info("✓ Created default bid messages file")
        except Exception as e:
            logging.error(f"Error saving bid messages: {e}")
        
        return default_messages

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
            "22": "Excel",
            "39": "Graphic Design",
            "44": "Article Writing",
            "73": "JavaScript",
            "94": "WordPress",
            "114": "HTML",
            "119": "SEO",
            "323": "React.js",
            "335": "Node.js",
            "1205": "Content Writing"
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

    def get_active_projects(self, limit: int = 20) -> List[Dict]:
        """Fetch active projects"""
        try:
            endpoint = f"{self.api_base}/projects/0.1/projects/active"
            params = {
                "limit": limit,
                "job_details": "true",
                "full_description": "true",
                "compact": "false"
            }
            
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                projects = data.get("result", {}).get("projects", [])
                logging.info(f"✓ Fetched {len(projects)} active projects")
                return projects
            else:
                logging.error(f"Error fetching projects: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Exception fetching projects: {e}")
            return []

    def calculate_bid_amount(self, budget: Dict) -> float:
        """Calculate bid amount based on budget"""
        if budget.get("minimum"):
            min_amount = float(budget["minimum"])
            max_amount = float(budget.get("maximum", min_amount * 1.5))
            
            # Bid 10-20% above minimum for better visibility
            bid_amount = min_amount * 1.15
            
            # Ensure within range
            return min(bid_amount, max_amount)
        
        return 100.0  # Default bid

    def format_bid_description(self, project: Dict) -> str:
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
        
        # Replace placeholders
        return message.format(skills=skills_text)

    def place_bid(self, project: Dict) -> bool:
        """Place a bid on a project"""
        try:
            project_id = project["id"]
            
            # Skip if already processed
            if project_id in self.processed_projects:
                return False
            
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_bid_time < 5:  # 5 seconds between bids
                time.sleep(5 - (current_time - self.last_bid_time))
            
            # Prepare bid data
            bid_data = {
                "project_id": project_id,
                "bidder_id": int(self.user_id),
                "amount": self.calculate_bid_amount(project.get("budget", {})),
                "period": 7,  # 7 days delivery
                "milestone_percentage": 100,
                "description": self.format_bid_description(project)
            }
            
            endpoint = f"{self.api_base}/projects/0.1/bids"
            
            response = requests.post(endpoint, headers=self.headers, json=bid_data)
            
            if response.status_code in [200, 201]:
                self.processed_projects.add(project_id)
                self.bid_count += 1
                self.last_bid_time = time.time()
                
                logging.info(f"✅ Bid placed on project: {project['title'][:50]}...")
                logging.info(f"   Amount: ${bid_data['amount']}, Total bids: {self.bid_count}")
                return True
            else:
                logging.error(f"❌ Failed to bid on {project_id}: {response.status_code}")
                if response.text:
                    logging.error(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            logging.error(f"Exception placing bid: {e}")
            return False

    def realtime_monitor_with_bidding(self):
        """Monitor and bid continuously"""
        logging.info("🚀 Starting real-time monitoring with auto-bidding...")
        logging.info(f"User ID: {self.user_id}")
        
        error_count = 0
        max_errors = 5
        
        while True:
            try:
                # Fetch active projects
                projects = self.get_active_projects(limit=30)
                
                if projects:
                    new_projects = 0
                    for project in projects:
                        if project["id"] not in self.processed_projects:
                            new_projects += 1
                            
                            # Auto bid on the project
                            success = self.place_bid(project)
                            
                            if success:
                                # Small delay between bids
                                time.sleep(2)
                    
                    if new_projects == 0:
                        logging.info("No new projects found in this cycle")
                    
                    error_count = 0  # Reset error count on success
                else:
                    error_count += 1
                    logging.warning(f"No projects fetched (error count: {error_count}/{max_errors})")
                    
                    if error_count >= max_errors:
                        logging.error("Max errors reached. Waiting 5 minutes before retry...")
                        time.sleep(300)  # 5 minutes
                        error_count = 0
                
                # Wait before next cycle
                logging.info(f"💤 Waiting 30 seconds before next check... (Total bids: {self.bid_count})")
                time.sleep(30)
                
            except KeyboardInterrupt:
                logging.info("Monitoring stopped by user")
                break
            except Exception as e:
                error_count += 1
                logging.error(f"Error in monitoring loop: {e}")
                
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