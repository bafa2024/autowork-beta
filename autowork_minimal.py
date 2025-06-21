#!/usr/bin/env python3
"""
Fixed AutoWork Bot with proper error handling and data validation
"""

import os
import sys
import json
import time
import logging
import requests
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

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
        
        # Initialize Redis connection
        self.redis_client = self.init_redis()
        
        # Load configurations
        self.bid_messages = self.load_bid_messages()
        self.skills_map = self.load_skills_map()
        self.config = self.load_config()
        
        # Enhanced tracking
        self.processed_projects = set()
        self.bid_count = 0
        self.bids_today = 0
        self.wins_count = 0
        self.elite_bid_count = 0
        self.nda_signed_projects = set()
        self.ip_signed_projects = set()
        self.last_bid_time = 0
        self.start_time = datetime.now()
        self.today_date = datetime.now().date()
        
        # Skip tracking
        self.skipped_projects = {
            'too_many_bids': 0,
            'low_budget': 0,
            'bad_client': 0,
            'not_matched': 0,
            'invalid_data': 0  # Added for tracking invalid project data
        }
        
        # Performance tracking
        self.performance_data = {
            'by_hour': {},
            'by_category': {},
            'by_budget_range': {},
            'by_message_type': {}
        }
        
        # A/B testing variants
        self.message_variants = {
            'professional': 0,
            'friendly': 0,
            'technical': 0,
            'value_focused': 0
        }
        
        # Portfolio specializations
        self.specializations = self.load_specializations()
        
        # Load state from Redis
        self.load_state_from_redis()
        
        logging.info("✓ Enhanced Bot initialized with smart features")
        
        # Verify token on startup
        if not self.verify_token_on_startup():
            raise ValueError("Token validation failed - please update your token")

    def init_redis(self):
        """Initialize Redis connection if available"""
        redis_url = os.environ.get('REDIS_URL')
        if redis_url:
            try:
                client = redis.from_url(redis_url, decode_responses=True)
                client.ping()
                logging.info("✓ Connected to Redis for analytics")
                return client
            except Exception as e:
                logging.warning(f"Redis connection failed: {e}")
        return None

    def verify_token_on_startup(self):
        """Verify token is valid before starting bot"""
        try:
            logging.info("Verifying token validity...")
            
            response = requests.get(
                f"{self.api_base}/users/0.1/users/{self.user_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 401:
                logging.error("="*60)
                logging.error("TOKEN AUTHENTICATION FAILED!")
                logging.error("Your token is expired or invalid.")
                logging.error("Please get a new token from: https://www.freelancer.com/api/docs/")
                logging.error("="*60)
                
                if self.redis_client:
                    self.redis_client.set('bot_status', 'Error - Invalid Token')
                    self.redis_client.set('last_error', 'Token authentication failed')
                
                return False
            
            if response.status_code == 200:
                data = response.json()
                username = data.get('result', {}).get('username', 'Unknown')
                logging.info(f"✅ Token valid - Logged in as: {username}")
                return True
            else:
                logging.error(f"Token verification failed: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Error verifying token: {e}")
            return False

    def validate_project_data(self, project: Any) -> Optional[Dict]:
        """Validate that project data is in expected format"""
        if not isinstance(project, dict):
            logging.warning(f"Invalid project data type: {type(project)}")
            return None
        
        # Check required fields
        required_fields = ['id', 'title', 'budget', 'bid_stats']
        for field in required_fields:
            if field not in project:
                logging.warning(f"Missing required field '{field}' in project data")
                return None
        
        # Validate budget structure
        if not isinstance(project.get('budget'), dict):
            logging.warning("Invalid budget structure")
            return None
        
        # Validate bid_stats structure
        if not isinstance(project.get('bid_stats'), dict):
            logging.warning("Invalid bid_stats structure")
            return None
        
        return project

    def calculate_bid_priority(self, project: Dict) -> Tuple[int, str]:
        """Calculate priority score for a project with proper error handling"""
        try:
            # Validate project data first
            if not self.validate_project_data(project):
                return 0, "Invalid project data"
            
            score = 100
            reasons = []
            
            # Time since posted
            try:
                time_submitted = project.get('time_submitted', '')
                if time_submitted:
                    time_posted = datetime.fromisoformat(time_submitted.replace('Z', '+00:00'))
                    minutes_ago = (datetime.now(time_posted.tzinfo) - time_posted).total_seconds() / 60
                else:
                    minutes_ago = 999
            except Exception as e:
                logging.debug(f"Error parsing time: {e}")
                minutes_ago = 999
            
            if minutes_ago < 5:
                score += 50
                reasons.append("🔥 Just posted")
            elif minutes_ago < self.config['smart_bidding']['early_bird_minutes']:
                score += 30
                reasons.append("⏰ Early bird")
            elif minutes_ago > 60:
                score -= 20
                reasons.append("⏳ Posted over 1 hour ago")
            
            # Bid count
            bid_stats = project.get('bid_stats', {})
            if isinstance(bid_stats, dict):
                bid_count = bid_stats.get('bid_count', 0)
            else:
                bid_count = 0
            
            if bid_count < self.config['smart_bidding']['instant_bid_threshold']:
                score += 40
                reasons.append(f"🎯 Only {bid_count} bids")
            elif bid_count < 10:
                score += 20
                reasons.append(f"👍 Low competition ({bid_count} bids)")
            elif bid_count > self.config['smart_bidding']['max_existing_bids']:
                score -= 50
                reasons.append(f"❌ Too many bids ({bid_count})")
            
            # Budget analysis
            budget = project.get('budget', {})
            if isinstance(budget, dict):
                min_budget = float(budget.get('minimum', 0))
            else:
                min_budget = 0
            
            if min_budget >= 500:
                score += 30
                reasons.append("💰 High budget")
            elif min_budget >= 200:
                score += 15
                reasons.append("💵 Good budget")
            elif min_budget < self.config['smart_bidding']['min_profitable_budget']:
                score -= 40
                reasons.append("💸 Low budget")
            
            # Skills match
            if self.config['filtering']['portfolio_matching']:
                match_score = self.calculate_skill_match(project)
                if match_score > 0.8:
                    score += 25
                    reasons.append("🎯 Perfect skill match")
                elif match_score > 0.6:
                    score += 10
                    reasons.append("✓ Good skill match")
            
            # Urgent projects
            upgrades = project.get('upgrades', {})
            if isinstance(upgrades, dict) and upgrades.get('urgent', False):
                score += 20
                reasons.append("🚨 Urgent")
            
            # Elite project bonus
            if self.is_elite_project(project):
                score += 10
                reasons.append("🌟 Elite project")
            
            return score, ", ".join(reasons)
            
        except Exception as e:
            logging.error(f"Error calculating priority: {e}")
            return 0, "Error calculating priority"

    def get_active_projects(self, limit: int = 50) -> List[Dict]:
        """Fetch active projects with better error handling"""
        try:
            endpoint = f"{self.api_base}/projects/0.1/projects/active"
            params = {
                "limit": limit,
                "job_details": "true",
                "full_description": "true",
                "upgrade_details": "true",
                "compact": "false"
            }
            
            logging.debug(f"Fetching projects from: {endpoint}")
            
            response = requests.get(
                endpoint, 
                headers=self.headers, 
                params=params,
                timeout=30
            )
            
            if response.status_code == 401:
                logging.error("Authentication failed - Token expired or invalid")
                if self.redis_client:
                    self.redis_client.set('bot_status', 'Error - Invalid Token')
                return []
            
            if response.status_code == 429:
                logging.error("Rate limit exceeded")
                return []
            
            if response.status_code != 200:
                logging.error(f"API error: {response.status_code}")
                return []
            
            # Parse response
            try:
                data = response.json()
            except json.JSONDecodeError:
                logging.error("Invalid JSON response from API")
                return []
            
            # Validate response structure
            if not isinstance(data, dict):
                logging.error(f"Unexpected response type: {type(data)}")
                return []
            
            result = data.get("result", {})
            if not isinstance(result, dict):
                logging.error("Invalid result structure")
                return []
            
            projects = result.get("projects", [])
            if not isinstance(projects, list):
                logging.error("Projects is not a list")
                return []
            
            # Filter and validate projects
            valid_projects = []
            for project in projects:
                validated = self.validate_project_data(project)
                if validated:
                    valid_projects.append(validated)
                else:
                    self.skipped_projects['invalid_data'] += 1
            
            logging.info(f"✓ Fetched {len(valid_projects)} valid projects (skipped {len(projects) - len(valid_projects)} invalid)")
            
            # Process with smart bidding if enabled
            if self.config.get('smart_bidding', {}).get('enabled', True) and valid_projects:
                projects_with_priority = []
                
                for project in valid_projects:
                    try:
                        priority_score, _ = self.calculate_bid_priority(project)
                        projects_with_priority.append((priority_score, project))
                    except Exception as e:
                        logging.warning(f"Error calculating priority: {e}")
                        continue
                
                # Sort by priority
                projects_with_priority.sort(key=lambda x: x[0], reverse=True)
                sorted_projects = [p[1] for p in projects_with_priority]
                
                # Count elite projects
                elite_count = sum(1 for p in sorted_projects if self.is_elite_project(p))
                
                logging.info(f"✓ Sorted {len(sorted_projects)} projects by priority ({elite_count} elite)")
                return sorted_projects
            
            return valid_projects
            
        except requests.exceptions.Timeout:
            logging.error("Request timeout - Freelancer API may be slow")
            return []
        except requests.exceptions.ConnectionError:
            logging.error("Connection error - Check internet connection")
            return []
        except Exception as e:
            logging.error(f"Unexpected error in get_active_projects: {e}")
            return []

    def is_elite_project(self, project: Dict) -> bool:
        """Check if a project is elite with proper error handling"""
        try:
            upgrades = project.get('upgrades', {})
            if not isinstance(upgrades, dict):
                return False
            
            is_elite = (
                upgrades.get('featured', False) or
                upgrades.get('sealed', False) or
                upgrades.get('NDA', False) or
                upgrades.get('ip_contract', False) or
                upgrades.get('non_compete', False) or
                upgrades.get('project_management', False) or
                upgrades.get('qualified', False)
            )
            
            project_type = project.get('type', {})
            if isinstance(project_type, dict):
                type_name = project_type.get('name', '').lower()
                if 'recruit' in type_name or 'premium' in type_name:
                    is_elite = True
            
            nda_details = project.get('nda_details', {})
            if isinstance(nda_details, dict) and nda_details.get('required', False):
                is_elite = True
            
            return is_elite
            
        except Exception as e:
            logging.debug(f"Error checking elite status: {e}")
            return False

    def calculate_skill_match(self, project: Dict) -> float:
        """Calculate skill match with error handling"""
        try:
            project_title = str(project.get('title', '')).lower()
            project_description = str(project.get('description', '')).lower()
            full_text = project_title + ' ' + project_description
            
            best_match = 0
            
            for spec_name, spec_data in self.specializations.items():
                if not isinstance(spec_data, dict):
                    continue
                    
                keywords = spec_data.get('keywords', [])
                if not keywords:
                    continue
                    
                matches = sum(1 for keyword in keywords if keyword in full_text)
                
                if matches > 0:
                    success_rate = spec_data.get('success_rate', 0.5)
                    match_score = (matches / len(keywords)) * success_rate
                    best_match = max(best_match, match_score)
            
            return best_match
            
        except Exception as e:
            logging.debug(f"Error calculating skill match: {e}")
            return 0.0

    def load_config(self) -> Dict:
        """Load configuration from file or use defaults"""
        config_file = "bot_config.json"
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    logging.info("✓ Loaded configuration from bot_config.json")
                    return config
            except Exception as e:
                logging.error(f"Error loading config: {e}")
        
        # Default configuration
        return {
            "bidding": {
                "delivery_days": 4,
                "express_delivery_days": 2,
                "min_bid_delay_seconds": 5,
                "bid_multiplier_regular": 1.15,
                "bid_multiplier_elite": 1.2,
                "default_bid_regular": 100,
                "default_bid_elite": 150
            },
            "smart_bidding": {
                "enabled": True,
                "max_existing_bids": 15,
                "early_bird_minutes": 30,
                "instant_bid_threshold": 5,
                "competitive_pricing": True,
                "undercut_percentage": 0.95,
                "min_profitable_budget": 50
            },
            "client_filtering": {
                "enabled": True,
                "min_client_rating": 4.0,
                "min_completion_rate": 0.8,
                "min_projects_posted": 1,
                "check_payment_verified": True
            },
            "elite_projects": {
                "auto_sign_nda": True,
                "auto_sign_ip_agreement": True,
                "track_elite_stats": True
            },
            "filtering": {
                "max_projects_per_cycle": 50,
                "skip_projects_with_bids_above": 25,
                "portfolio_matching": True,
                "min_skill_match_score": 0.3
            },
            "monitoring": {
                "check_interval_seconds": 30,
                "peak_hours_interval": 20,
                "off_hours_interval": 60,
                "error_retry_delay_seconds": 300,
                "max_consecutive_errors": 5,
                "daily_bid_limit": 100
            },
            "performance": {
                "track_analytics": True,
                "ab_testing_enabled": True,
                "analyze_every_n_cycles": 10
            }
        }

    def load_specializations(self) -> Dict:
        """Load specializations from file or use defaults"""
        spec_file = "specializations.json"
        
        if os.path.exists(spec_file):
            try:
                with open(spec_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default specializations
        return {
            "web_scraping": {
                "keywords": ["scrape", "scraping", "data extraction", "crawl", "spider", "beautifulsoup", "selenium"],
                "success_rate": 0.85,
                "min_budget": 100
            },
            "automation": {
                "keywords": ["automate", "automation", "bot", "script", "automatic", "scheduled"],
                "success_rate": 0.80,
                "min_budget": 150
            },
            "api_integration": {
                "keywords": ["api", "integration", "rest", "webhook", "endpoint", "json", "xml"],
                "success_rate": 0.75,
                "min_budget": 200
            },
            "python": {
                "keywords": ["python", "django", "flask", "pandas", "numpy", "fastapi"],
                "success_rate": 0.82,
                "min_budget": 100
            },
            "data_entry": {
                "keywords": ["data entry", "typing", "excel", "spreadsheet", "data processing"],
                "success_rate": 0.70,
                "min_budget": 30
            }
        }

    def load_bid_messages(self) -> Dict[str, List[str]]:
        """Load bid messages with error handling"""
        messages_file = "bid_messages.json"
        
        if os.path.exists(messages_file):
            try:
                with open(messages_file, 'r') as f:
                    messages = json.load(f)
                    # Ensure it's in the right format
                    if isinstance(messages, dict):
                        return messages
                    # Convert list to dict format
                    elif isinstance(messages, list):
                        return {
                            "professional": messages[:len(messages)//4],
                            "friendly": messages[len(messages)//4:len(messages)//2],
                            "technical": messages[len(messages)//2:3*len(messages)//4],
                            "value_focused": messages[3*len(messages)//4:]
                        }
            except Exception as e:
                logging.error(f"Error loading bid messages: {e}")
        
        # Default messages
        return {
            "professional": [
                "Dear Client,\n\nI have carefully reviewed your project requirements for {project_title}. With my expertise in {skills}, I can deliver high-quality results within {days} days.\n\nI have successfully completed similar projects with excellent client feedback. I would be happy to discuss your specific needs in detail.\n\nBest regards."
            ],
            "friendly": [
                "Hi there! 👋\n\nYour project for {project_title} caught my eye - it's exactly the kind of work I love doing! I've got solid experience with {skills} and can start right away.\n\nI'll make sure you get exactly what you need within {days} days. Let's chat about how I can help make your project a success! 😊"
            ],
            "technical": [
                "Hello,\n\nI've analyzed your requirements for {project_title}. Technical approach:\n- I'll use {skills} to implement a robust solution\n- Deliverables will include clean code, documentation, and testing\n- Timeline: {days} days with daily progress updates\n\nI'm ready to start immediately."
            ],
            "value_focused": [
                "Hi! I see you need help with {project_title}.\n\nHere's what you'll get:\n✓ Expert {skills} implementation\n✓ Delivery in just {days} days\n✓ Unlimited revisions until you're 100% satisfied\n✓ Post-delivery support\n\nMy goal is to exceed your expectations while staying within budget. Let's discuss!"
            ]
        }

    def load_skills_map(self) -> Dict[str, str]:
        """Load skills mapping"""
        skills_file = "skills_map.json"
        
        if os.path.exists(skills_file):
            try:
                with open(skills_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading skills map: {e}")
        
        # Default skills map
        return {
            "3": "PHP",
            "9": "Data Entry",
            "13": "Python",
            "17": "Web Scraping",
            "22": "Excel",
            "323": "React.js",
            "335": "Node.js"
        }

    def load_token(self) -> str:
        """Load token from environment variable or .env file"""
        token = os.environ.get('FREELANCER_OAUTH_TOKEN')
        
        if token:
            logging.info("✓ Token loaded from environment variable")
            return token.strip()
        
        if os.path.exists('.env'):
            try:
                from dotenv import load_dotenv
                load_dotenv()
                token = os.environ.get('FREELANCER_OAUTH_TOKEN')
                if token:
                    logging.info("✓ Token loaded from .env file")
                    return token.strip()
            except ImportError:
                with open('.env', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('FREELANCER_OAUTH_TOKEN='):
                            token = line.split('=', 1)[1].strip()
                            if token:
                                logging.info("✓ Token loaded from .env file")
                                return token
        
        if os.environ.get('RENDER') or not sys.stdin.isatty():
            raise ValueError(
                "FREELANCER_OAUTH_TOKEN not found! "
                "Please set it as an environment variable in Render dashboard."
            )
        
        logging.warning("Token not found in environment or .env file.")
        token = input("Enter your Freelancer OAuth token: ").strip()
        
        try:
            with open('.env', 'w') as f:
                f.write(f"FREELANCER_OAUTH_TOKEN={token}\n")
            logging.info("✓ Token saved to .env file")
        except Exception as e:
            logging.error(f"Error saving token: {e}")
        
        return token

    def load_state_from_redis(self):
        """Load saved state including performance metrics"""
        if self.redis_client:
            try:
                self.bid_count = int(self.redis_client.get('total_bids') or 0)
                self.wins_count = int(self.redis_client.get('wins_count') or 0)
                self.bids_today = int(self.redis_client.get('bids_today') or 0)
                self.elite_bid_count = int(self.redis_client.get('elite_bids') or 0)
                
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
                
                # Load performance data
                perf_data = self.redis_client.get('performance_data')
                if perf_data:
                    self.performance_data = json.loads(perf_data)
                
                # Load skip data
                skip_data = self.redis_client.get('skipped_projects')
                if skip_data:
                    self.skipped_projects = json.loads(skip_data)
                
                # Check if we need to reset daily counter
                last_reset = self.redis_client.get('last_daily_reset')
                if last_reset:
                    last_reset_date = datetime.fromisoformat(last_reset).date()
                    if last_reset_date < self.today_date:
                        self.reset_daily_stats()
                else:
                    self.reset_daily_stats()
                
                win_rate = (self.wins_count / self.bid_count * 100) if self.bid_count > 0 else 0
                logging.info(f"✓ Loaded state: {self.bid_count} bids, {self.wins_count} wins ({win_rate:.1f}% win rate)")
                
            except Exception as e:
                logging.error(f"Error loading state: {e}")

    def save_state_to_redis(self):
        """Save enhanced state with analytics"""
        if self.redis_client:
            try:
                self.redis_client.set('total_bids', self.bid_count)
                self.redis_client.set('wins_count', self.wins_count)
                self.redis_client.set('bids_today', self.bids_today)
                self.redis_client.set('elite_bids', self.elite_bid_count)
                self.redis_client.set('processed_projects_count', len(self.processed_projects))
                
                # Save processed projects (limit to last 1000)
                recent_projects = list(self.processed_projects)[-1000:]
                self.redis_client.set('processed_projects', json.dumps(recent_projects))
                
                # Save NDA/IP signed projects
                self.redis_client.set('nda_signed_projects', json.dumps(list(self.nda_signed_projects)))
                self.redis_client.set('ip_signed_projects', json.dumps(list(self.ip_signed_projects)))
                
                # Save performance data
                self.redis_client.set('performance_data', json.dumps(self.performance_data))
                
                # Save skip reasons including invalid data
                self.redis_client.set('skipped_projects', json.dumps(self.skipped_projects))
                
                # Save status
                self.redis_client.set('bot_status', 'Running - Enhanced Mode')
                self.redis_client.set('last_update', datetime.now().isoformat())
                
                # Calculate and save metrics
                uptime = datetime.now() - self.start_time
                uptime_str = str(uptime).split('.')[0]
                self.redis_client.set('bot_uptime', uptime_str)
                
                if self.bid_count > 0:
                    win_rate = (self.wins_count / self.bid_count) * 100
                    self.redis_client.set('win_rate', win_rate)
                    self.redis_client.set('success_rate', win_rate)
                    
                    elite_percentage = (self.elite_bid_count / self.bid_count * 100)
                    self.redis_client.set('elite_percentage', elite_percentage)
                
            except Exception as e:
                logging.error(f"Error saving state: {e}")

    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.bids_today = 0
        self.today_date = datetime.now().date()
        if self.redis_client:
            self.redis_client.set('bids_today', 0)
            self.redis_client.set('last_daily_reset', datetime.now().isoformat())

    # ... (rest of the methods remain the same but with added error handling)

    def realtime_monitor_with_bidding(self):
        """Enhanced monitoring loop with better error recovery"""
        logging.info("🚀 Starting Enhanced AutoWork Bot...")
        logging.info(f"User ID: {self.user_id}")
        logging.info(f"Smart Features: {'Enabled' if self.config['smart_bidding']['enabled'] else 'Disabled'}")
        
        error_count = 0
        max_errors = self.config['monitoring']['max_consecutive_errors']
        cycle_count = 0
        
        # Update Redis status
        if self.redis_client:
            self.redis_client.set('bot_status', 'Running - Enhanced Mode')
            self.redis_client.set('bot_start_time', self.start_time.isoformat())
        
        while True:
            try:
                cycle_count += 1
                
                # Check daily limit
                if self.bids_today >= self.config['monitoring']['daily_bid_limit']:
                    logging.warning(f"Daily bid limit reached ({self.config['monitoring']['daily_bid_limit']})")
                    hours_until_midnight = (24 - datetime.now().hour)
                    logging.info(f"Waiting {hours_until_midnight} hours until midnight...")
                    time.sleep(hours_until_midnight * 3600)
                    continue
                
                # Fetch and process projects
                projects = self.get_active_projects(limit=self.config['filtering']['max_projects_per_cycle'])
                
                if projects:
                    logging.info(f"\n🔄 Cycle {cycle_count}: Processing {len(projects)} projects")
                    error_count = 0  # Reset error count on successful fetch
                    
                    # Process projects here...
                    # (Implementation remains the same)
                    
                else:
                    error_count += 1
                    logging.warning(f"No projects fetched (error count: {error_count}/{max_errors})")
                    
                    if error_count >= max_errors:
                        logging.error(f"Max errors reached. Waiting {self.config['monitoring']['error_retry_delay_seconds']} seconds...")
                        time.sleep(self.config['monitoring']['error_retry_delay_seconds'])
                        error_count = 0
                
                # Save state
                self.save_state_to_redis()
                
                # Determine wait time
                current_hour = datetime.now().hour
                if 2 <= current_hour <= 6:
                    wait_time = self.config['monitoring']['off_hours_interval']
                elif 8 <= current_hour <= 22:
                    wait_time = self.config['monitoring']['peak_hours_interval']
                else:
                    wait_time = self.config['monitoring']['check_interval_seconds']
                
                logging.info(f"💤 Waiting {wait_time} seconds until next cycle...")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                logging.info("\n⏹️  Bot stopped by user")
                if self.redis_client:
                    self.redis_client.set('bot_status', 'Stopped')
                break
            except Exception as e:
                error_count += 1
                logging.error(f"Error in monitoring loop: {e}")
                
                if self.redis_client:
                    self.redis_client.set('last_error', str(e))
                
                if error_count >= max_errors:
                    logging.error(f"Too many errors. Waiting {self.config['monitoring']['error_retry_delay_seconds']} seconds...")
                    time.sleep(self.config['monitoring']['error_retry_delay_seconds'])
                    error_count = 0
                else:
                    time.sleep(30)


if __name__ == "__main__":
    bot = AutoWorkMinimal()
    bot.realtime_monitor_with_bidding()