#!/usr/bin/env python3
"""
Enhanced AutoWork Bot with Smart Features for Higher Win Rate
Includes: Smart timing, competitive pricing, client analysis, and more
Fixed API error handling and token validation
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
            'not_matched': 0
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
        
        # Portfolio specializations (customize based on your skills)
        self.specializations = self.load_specializations()
        
        # Load state from Redis
        self.load_state_from_redis()
        
        logging.info("✓ Enhanced Bot initialized with smart features")
        logging.info(f"✓ Early bird window: {self.config['smart_bidding']['early_bird_minutes']} minutes")
        logging.info(f"✓ Max bids threshold: {self.config['smart_bidding']['max_existing_bids']}")
        logging.info(f"✓ Min budget: ${self.config['smart_bidding']['min_profitable_budget']}")
        
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
            
            # Test with user endpoint
            response = requests.get(
                f"{self.api_base}/users/0.1/users/{self.user_id}",
                headers=self.headers
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

    def validate_api_response(self, response, endpoint_name="API"):
        """Validate API response and handle errors gracefully"""
        
        # Check response status
        if response.status_code == 401:
            error_msg = "Authentication failed - Token expired or invalid"
            logging.error(f"{endpoint_name}: {error_msg}")
            logging.error("Please generate a new token at: https://www.freelancer.com/api/docs/")
            if self.redis_client:
                self.redis_client.set('last_error', error_msg)
                self.redis_client.set('bot_status', 'Error - Invalid Token')
            return None
        
        if response.status_code == 429:
            error_msg = "Rate limit exceeded - Too many requests"
            logging.error(f"{endpoint_name}: {error_msg}")
            if self.redis_client:
                self.redis_client.set('last_error', error_msg)
            return None
        
        if response.status_code != 200:
            error_msg = f"HTTP {response.status_code} error"
            logging.error(f"{endpoint_name}: {error_msg}")
            logging.error(f"Response: {response.text[:500]}")
            if self.redis_client:
                self.redis_client.set('last_error', error_msg)
            return None
        
        # Try to parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            logging.error(f"{endpoint_name}: Invalid JSON response - {e}")
            logging.error(f"Raw response: {response.text[:500]}")
            if self.redis_client:
                self.redis_client.set('last_error', 'Invalid JSON response')
            return None
        
        # Validate response structure
        if not isinstance(data, dict):
            logging.error(f"{endpoint_name}: Response is not a dictionary")
            logging.error(f"Type: {type(data)}, Content: {str(data)[:500]}")
            return None
        
        # Check for API errors in response
        if data.get('status') == 'error':
            error_msg = data.get('message', 'Unknown API error')
            logging.error(f"{endpoint_name}: API Error - {error_msg}")
            if self.redis_client:
                self.redis_client.set('last_error', error_msg)
            return None
        
        return data

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
        
        # Default specializations - CUSTOMIZE THESE FOR YOUR SKILLS
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
                
                # Save skip reasons
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

    def load_bid_messages(self) -> Dict[str, List[str]]:
        """Load categorized bid messages for A/B testing"""
        messages_file = "bid_messages_enhanced.json"
        
        if os.path.exists(messages_file):
            try:
                with open(messages_file, 'r') as f:
                    messages = json.load(f)
                    logging.info(f"✓ Loaded enhanced bid messages from file")
                    return messages
            except Exception as e:
                logging.error(f"Error loading bid messages: {e}")
        
        # Try standard bid messages file
        standard_file = "bid_messages.json"
        if os.path.exists(standard_file):
            try:
                with open(standard_file, 'r') as f:
                    messages = json.load(f)
                    # Convert to categorized format
                    return {
                        "professional": messages[:len(messages)//4],
                        "friendly": messages[len(messages)//4:len(messages)//2],
                        "technical": messages[len(messages)//2:3*len(messages)//4],
                        "value_focused": messages[3*len(messages)//4:]
                    }
            except:
                pass
        
        # Default categorized messages
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

    def analyze_client(self, employer_id: int) -> Dict[str, Any]:
        """Analyze client history and reputation"""
        if not self.config['client_filtering']['enabled']:
            return {'is_good_client': True}
        
        try:
            endpoint = f"{self.api_base}/users/0.1/users/{employer_id}"
            response = requests.get(endpoint, headers=self.headers)
            
            data = self.validate_api_response(response, "Client Analysis")
            if not data:
                return {'is_good_client': True}  # Default to true if can't analyze
            
            user_data = data.get('result', {})
            
            # Get client's project history
            projects_endpoint = f"{self.api_base}/projects/0.1/projects"
            projects_params = {'owners[]': employer_id, 'limit': 10}
            projects_response = requests.get(projects_endpoint, headers=self.headers, params=projects_params)
            
            project_count = 0
            completion_rate = 0
            
            projects_data = self.validate_api_response(projects_response, "Client Projects")
            if projects_data:
                projects = projects_data.get('result', {}).get('projects', [])
                project_count = len(projects)
                if projects:
                    completed = sum(1 for p in projects if p.get('status', {}).get('name') == 'complete')
                    completion_rate = completed / project_count
            
            client_analysis = {
                'rating': user_data.get('reputation', {}).get('entire_history', {}).get('overall', 0),
                'projects_posted': project_count,
                'payment_verified': user_data.get('status', {}).get('payment_verified', False),
                'completion_rate': completion_rate,
                'member_since': user_data.get('registration_date', ''),
                'is_good_client': True
            }
            
            # Determine if good client
            config = self.config['client_filtering']
            if (client_analysis['rating'] < config['min_client_rating'] or
                client_analysis['completion_rate'] < config['min_completion_rate'] or
                client_analysis['projects_posted'] < config['min_projects_posted']):
                client_analysis['is_good_client'] = False
            
            return client_analysis
                
        except Exception as e:
            logging.error(f"Error analyzing client {employer_id}: {e}")
            
        return {'is_good_client': True}

    def calculate_bid_priority(self, project: Dict) -> Tuple[int, str]:
        """Calculate priority score for a project"""
        score = 100
        reasons = []
        
        # Time since posted (highest priority for fresh projects)
        try:
            time_posted = datetime.fromisoformat(project['time_submitted'].replace('Z', '+00:00'))
            minutes_ago = (datetime.now(time_posted.tzinfo) - time_posted).total_seconds() / 60
        except:
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
        
        # Bid count (prefer projects with few bids)
        bid_count = project.get('bid_stats', {}).get('bid_count', 0)
        
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
        min_budget = float(budget.get('minimum', 0))
        
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
        if project.get('upgrades', {}).get('urgent', False):
            score += 20
            reasons.append("🚨 Urgent")
        
        # Elite project bonus
        if self.is_elite_project(project):
            score += 10
            reasons.append("🌟 Elite project")
        
        return score, ", ".join(reasons)

    def calculate_skill_match(self, project: Dict) -> float:
        """Calculate how well project matches our specializations"""
        project_title = project.get('title', '').lower()
        project_description = project.get('description', '').lower()
        full_text = project_title + ' ' + project_description
        
        best_match = 0
        
        for spec_name, spec_data in self.specializations.items():
            keywords = spec_data['keywords']
            matches = sum(1 for keyword in keywords if keyword in full_text)
            
            if matches > 0:
                match_score = (matches / len(keywords)) * spec_data['success_rate']
                best_match = max(best_match, match_score)
        
        return best_match

    def calculate_competitive_bid(self, project: Dict, is_elite: bool = False) -> float:
        """Calculate competitive bid amount using market intelligence"""
        if not self.config['smart_bidding']['competitive_pricing']:
            # Use simple calculation
            return self.calculate_bid_amount(project.get('budget', {}), is_elite)
        
        budget = project.get('budget', {})
        min_budget = float(budget.get('minimum', 0))
        max_budget = float(budget.get('maximum', min_budget * 2))
        bid_stats = project.get('bid_stats', {})
        avg_bid = float(bid_stats.get('bid_avg', 0))
        bid_count = bid_stats.get('bid_count', 0)
        
        # If no bids yet, use strategic positioning
        if bid_count == 0:
            # First bid: 30% above minimum for quality signal
            return min(min_budget * 1.3, max_budget)
        
        # If few bids, position competitively
        elif bid_count < 5 and avg_bid > 0:
            # Slightly below average to be competitive
            competitive_bid = avg_bid * self.config['smart_bidding']['undercut_percentage']
            # But not below profitable minimum
            return max(competitive_bid, min_budget * 1.1)
        
        # If many bids, need to be more aggressive
        elif bid_count > 10 and avg_bid > 0:
            # More aggressive undercut
            aggressive_bid = avg_bid * 0.85
            # But still profitable
            return max(aggressive_bid, min_budget * 1.05)
        
        # Default: standard multiplier
        else:
            multiplier = self.config['bidding']['bid_multiplier_elite'] if is_elite else self.config['bidding']['bid_multiplier_regular']
            return min_budget * multiplier

    def calculate_bid_amount(self, budget: Dict, is_elite: bool = False) -> float:
        """Simple bid calculation for fallback"""
        if budget.get("minimum"):
            min_amount = float(budget["minimum"])
            max_amount = float(budget.get("maximum", min_amount * 1.5))
            
            if is_elite:
                bid_amount = min_amount * self.config['bidding']['bid_multiplier_elite']
            else:
                bid_amount = min_amount * self.config['bidding']['bid_multiplier_regular']
            
            return min(bid_amount, max_amount)
        
        return self.config['bidding']['default_bid_elite'] if is_elite else self.config['bidding']['default_bid_regular']

    def select_bid_message(self, project: Dict, is_elite: bool = False) -> str:
        """Select and customize bid message using A/B testing"""
        if not self.config['performance']['ab_testing_enabled']:
            # Use first professional message
            messages = self.bid_messages.get('professional', ["Default message"])
            message_template = messages[0]
        else:
            # A/B testing logic
            variant_names = list(self.message_variants.keys())
            
            # Use round-robin for even distribution
            total_uses = sum(self.message_variants.values())
            variant_index = total_uses % len(variant_names)
            selected_variant = variant_names[variant_index]
            
            # Track usage
            self.message_variants[selected_variant] += 1
            
            # Get message template
            messages = self.bid_messages.get(selected_variant, self.bid_messages.get('professional', ["Default"]))
            message_template = messages[0] if messages else "Default message"
            
            # Track in Redis
            if self.redis_client:
                self.redis_client.hincrby('message_variants', selected_variant, 1)
        
        # Customize message
        project_skills = []
        for job in project.get('jobs', []):
            skill_name = self.skills_map.get(str(job['id']), job.get('name', ''))
            if skill_name:
                project_skills.append(skill_name)
        
        skills_text = ", ".join(project_skills[:2]) if project_skills else "relevant technologies"
        
        # Determine delivery days
        delivery_days = self.config['bidding']['express_delivery_days'] if project.get('upgrades', {}).get('urgent', False) else self.config['bidding']['delivery_days']
        
        message = message_template.format(
            project_title=project['title'][:50],
            skills=skills_text,
            days=delivery_days
        )
        
        # Add NDA/IP note if needed
        if is_elite and (project.get('upgrades', {}).get('NDA', False) or project.get('upgrades', {}).get('ip_contract', False)):
            message += "\n\nI understand this project requires confidentiality agreements and I'm ready to sign any necessary NDA/IP documents."
        
        return message

    def is_elite_project(self, project: Dict) -> bool:
        """Check if a project is an elite project"""
        upgrades = project.get('upgrades', {})
        
        is_elite = (
            upgrades.get('featured', False) or
            upgrades.get('sealed', False) or
            upgrades.get('NDA', False) or
            upgrades.get('ip_contract', False) or
            upgrades.get('non_compete', False) or
            upgrades.get('project_management', False) or
            upgrades.get('qualified', False)
        )
        
        project_type = project.get('type', {}).get('name', '').lower()
        if 'recruit' in project_type or 'premium' in project_type:
            is_elite = True
        
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

    def should_bid_on_project(self, project: Dict) -> Tuple[bool, str]:
        """Determine if should bid on a project with reason"""
        project_id = project['id']
        
        # Skip if already processed
        if project_id in self.processed_projects:
            return False, "Already processed"
        
        # Check bid count
        bid_count = project.get('bid_stats', {}).get('bid_count', 0)
        if bid_count > self.config['filtering']['skip_projects_with_bids_above']:
            self.skipped_projects['too_many_bids'] += 1
            return False, f"Too many bids ({bid_count})"
        
        # Check budget
        min_budget = float(project.get('budget', {}).get('minimum', 0))
        if min_budget < self.config['smart_bidding']['min_profitable_budget']:
            self.skipped_projects['low_budget'] += 1
            return False, f"Budget too low (${min_budget})"
        
        # Check client
        if self.config['client_filtering']['enabled']:
            employer_id = project.get('owner_id')
            if employer_id:
                client_analysis = self.analyze_client(employer_id)
                if not client_analysis['is_good_client']:
                    self.skipped_projects['bad_client'] += 1
                    return False, "Client doesn't meet criteria"
        
        # Check skill match
        if self.config['filtering']['portfolio_matching']:
            match_score = self.calculate_skill_match(project)
            if match_score < self.config['filtering']['min_skill_match_score']:
                self.skipped_projects['not_matched'] += 1
                return False, f"Poor skill match ({match_score:.2f})"
        
        return True, "Good opportunity"

    def check_and_sign_nda(self, project_id: int) -> bool:
        """Check if project requires NDA and sign it"""
        if not self.config['elite_projects']['auto_sign_nda']:
            return True
        
        try:
            endpoint = f"{self.api_base}/projects/0.1/projects/{project_id}/nda"
            response = requests.get(endpoint, headers=self.headers)
            
            data = self.validate_api_response(response, "NDA Check")
            if not data:
                return True  # Continue anyway
            
            nda_data = data.get('result', {})
            
            if nda_data.get('status') == 'unsigned':
                sign_endpoint = f"{self.api_base}/projects/0.1/projects/{project_id}/nda/sign"
                sign_response = requests.post(sign_endpoint, headers=self.headers, json={})
                
                if sign_response.status_code in [200, 201]:
                    self.nda_signed_projects.add(project_id)
                    logging.info("   ✅ NDA signed automatically")
                    return True
                else:
                    logging.error(f"   Failed to sign NDA: {sign_response.status_code}")
                    return False
            
            elif nda_data.get('status') == 'signed':
                self.nda_signed_projects.add(project_id)
                return True
            
            return True
            
        except Exception as e:
            logging.error(f"   Error checking/signing NDA: {e}")
            return True

    def check_and_sign_ip_agreement(self, project_id: int) -> bool:
        """Check if project requires IP agreement and sign it"""
        if not self.config['elite_projects']['auto_sign_ip_agreement']:
            return True
        
        try:
            endpoint = f"{self.api_base}/projects/0.1/projects/{project_id}/ip_contract"
            response = requests.get(endpoint, headers=self.headers)
            
            data = self.validate_api_response(response, "IP Agreement Check")
            if not data:
                return True  # Continue anyway
            
            ip_data = data.get('result', {})
            
            if ip_data.get('status') == 'unsigned':
                sign_endpoint = f"{self.api_base}/projects/0.1/projects/{project_id}/ip_contract/sign"
                sign_response = requests.post(sign_endpoint, headers=self.headers, json={})
                
                if sign_response.status_code in [200, 201]:
                    self.ip_signed_projects.add(project_id)
                    logging.info("   ✅ IP agreement signed automatically")
                    return True
                else:
                    logging.error(f"   Failed to sign IP agreement: {sign_response.status_code}")
                    return False
            
            elif ip_data.get('status') == 'signed':
                self.ip_signed_projects.add(project_id)
                return True
            
            return True
            
        except Exception as e:
            logging.error(f"   Error checking/signing IP agreement: {e}")
            return True

    def track_bid_performance(self, project: Dict, bid_amount: float, priority_score: int, variant_used: str = None):
        """Track bid performance for analytics"""
        if not self.config['performance']['track_analytics']:
            return
        
        current_hour = datetime.now().hour
        category = project.get('jobs', [{}])[0].get('name', 'Unknown') if project.get('jobs') else 'Unknown'
        
        # Track by hour
        if str(current_hour) not in self.performance_data['by_hour']:
            self.performance_data['by_hour'][str(current_hour)] = {'bids': 0, 'wins': 0}
        self.performance_data['by_hour'][str(current_hour)]['bids'] += 1
        
        # Track by category
        if category not in self.performance_data['by_category']:
            self.performance_data['by_category'][category] = {'bids': 0, 'wins': 0}
        self.performance_data['by_category'][category]['bids'] += 1
        
        # Track by budget range
        budget_range = 'low' if bid_amount < 100 else 'medium' if bid_amount < 500 else 'high'
        if budget_range not in self.performance_data['by_budget_range']:
            self.performance_data['by_budget_range'][budget_range] = {'bids': 0, 'wins': 0}
        self.performance_data['by_budget_range'][budget_range]['bids'] += 1
        
        # Track by message type
        if variant_used:
            if variant_used not in self.performance_data['by_message_type']:
                self.performance_data['by_message_type'][variant_used] = {'bids': 0, 'wins': 0}
            self.performance_data['by_message_type'][variant_used]['bids'] += 1

    def place_bid(self, project: Dict) -> bool:
        """Place a bid on a project with all enhancements"""
        try:
            project_id = project["id"]
            
            # Check if it's a new day
            if datetime.now().date() > self.today_date:
                self.reset_daily_stats()
            
            # Calculate priority
            priority_score, priority_reasons = self.calculate_bid_priority(project)
            
            # Determine if should bid
            should_bid, reason = self.should_bid_on_project(project)
            
            if not should_bid:
                logging.info(f"⏭️  Skipping: {project['title'][:40]}... - {reason}")
                return False
            
            # Get project details
            details = self.get_project_details(project)
            is_elite = details['is_elite']
            
            logging.info(f"\n{'='*60}")
            logging.info(f"🎯 BIDDING ON: {project['title'][:50]}...")
            logging.info(f"   Priority: {priority_score} - {priority_reasons}")
            
            # Check and sign agreements if needed
            if details.get('nda', False):
                self.check_and_sign_nda(project_id)
            
            if details.get('ip_contract', False):
                self.check_and_sign_ip_agreement(project_id)
            
            # Rate limiting
            current_time = time.time()
            min_delay = self.config['bidding']['min_bid_delay_seconds']
            if current_time - self.last_bid_time < min_delay:
                time.sleep(min_delay - (current_time - self.last_bid_time))
            
            # Calculate competitive bid
            bid_amount = self.calculate_competitive_bid(project, is_elite)
            
            # Determine delivery days
            if details.get('urgent', False):
                delivery_days = self.config['bidding']['express_delivery_days']
            else:
                delivery_days = self.config['bidding']['delivery_days']
            
            # Generate optimized message
            bid_message = self.select_bid_message(project, is_elite)
            
            # Get variant used for tracking
            total_uses = sum(self.message_variants.values())
            variant_index = (total_uses - 1) % len(self.message_variants)
            variant_used = list(self.message_variants.keys())[variant_index]
            
            # Prepare bid data
            bid_data = {
                "project_id": project_id,
                "bidder_id": int(self.user_id),
                "amount": bid_amount,
                "period": delivery_days,
                "milestone_percentage": 100,
                "description": bid_message
            }
            
            # Log bid details
            project_type = "🌟 ELITE" if is_elite else "Regular"
            logging.info(f"   Type: {project_type}")
            logging.info(f"   💰 Bid: ${bid_amount:.2f} (Budget: ${details['budget']['minimum']}-${details['budget']['maximum']})")
            logging.info(f"   📅 Delivery: {delivery_days} days")
            logging.info(f"   📝 Message variant: {variant_used}")
            
            if is_elite:
                flags = []
                if details['featured']: flags.append("Featured")
                if details['sealed']: flags.append("Sealed")
                if details['nda']: flags.append("NDA")
                if details['ip_contract']: flags.append("IP Contract")
                if details['urgent']: flags.append("Urgent")
                logging.info(f"   Elite flags: {', '.join(flags)}")
            
            # Submit bid
            endpoint = f"{self.api_base}/projects/0.1/bids"
            response = requests.post(endpoint, headers=self.headers, json=bid_data)
            
            if response.status_code in [200, 201]:
                self.processed_projects.add(project_id)
                self.bid_count += 1
                self.bids_today += 1
                if is_elite:
                    self.elite_bid_count += 1
                self.last_bid_time = time.time()
                
                logging.info(f"✅ Bid placed successfully! Total: {self.bid_count} (Today: {self.bids_today})")
                
                # Track performance
                self.track_bid_performance(project, bid_amount, priority_score, variant_used)
                
                # Save bid to Redis
                if self.redis_client:
                    bid_key = f"bid:{int(time.time()*1000)}"
                    bid_info = {
                        "project_id": project_id,
                        "project_title": project['title'][:100],
                        "amount": bid_amount,
                        "delivery_days": delivery_days,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "is_elite": is_elite,
                        "priority_score": priority_score,
                        "message_variant": variant_used
                    }
                    self.redis_client.set(bid_key, json.dumps(bid_info))
                    self.redis_client.expire(bid_key, 86400)
                    self.redis_client.set('last_bid_time', datetime.now().isoformat())
                
                # Save state
                self.save_state_to_redis()
                
                return True
            else:
                logging.error(f"❌ Failed to bid: {response.status_code}")
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
            
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            # Use the validation method
            data = self.validate_api_response(response, "Projects API")
            if data is None:
                return []
            
            # Safely extract projects
            result = data.get("result", {})
            if not isinstance(result, dict):
                logging.error(f"Invalid result structure: {type(result)}")
                return []
            
            projects = result.get("projects", [])
            if not isinstance(projects, list):
                logging.error(f"Projects is not a list: {type(projects)}")
                return []
            
            # Filter out any non-dict items
            valid_projects = [p for p in projects if isinstance(p, dict)]
            
            if len(valid_projects) < len(projects):
                logging.warning(f"Filtered out {len(projects) - len(valid_projects)} invalid projects")
            
            # Process with smart bidding if enabled
            if self.config.get('smart_bidding', {}).get('enabled', True):
                projects_with_priority = []
                
                for project in valid_projects:
                    try:
                        priority_score, _ = self.calculate_bid_priority(project)
                        projects_with_priority.append((priority_score, project))
                    except Exception as e:
                        logging.warning(f"Error calculating priority for project: {e}")
                        continue
                
                # Sort by priority
                projects_with_priority.sort(key=lambda x: x[0], reverse=True)
                sorted_projects = [p[1] for p in projects_with_priority]
                
                # Count elite projects safely
                elite_count = 0
                for p in sorted_projects:
                    try:
                        if self.is_elite_project(p):
                            elite_count += 1
                    except:
                        pass
                
                logging.info(f"✓ Fetched {len(sorted_projects)} valid projects ({elite_count} elite)")
                return sorted_projects
            else:
                logging.info(f"✓ Fetched {len(valid_projects)} valid projects")
                return valid_projects
                
        except requests.exceptions.Timeout:
            logging.error("Request timeout - Freelancer API may be slow")
            if self.redis_client:
                self.redis_client.set('last_error', 'API timeout')
            return []
        except requests.exceptions.ConnectionError:
            logging.error("Connection error - Check internet connection")
            if self.redis_client:
                self.redis_client.set('last_error', 'Connection error')
            return []
        except Exception as e:
            logging.error(f"Unexpected error in get_active_projects: {e}")
            logging.error(f"Error type: {type(e).__name__}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            if self.redis_client:
                self.redis_client.set('last_error', str(e))
            return []

    def analyze_performance(self):
        """Analyze and log performance metrics"""
        if not self.config['performance']['track_analytics'] or self.bid_count == 0:
            return
        
        logging.info("\n" + "="*60)
        logging.info("📊 PERFORMANCE ANALYTICS")
        logging.info("="*60)
        
        # Overall metrics
        win_rate = (self.wins_count / self.bid_count * 100) if self.bid_count > 0 else 0
        elite_percentage = (self.elite_bid_count / self.bid_count * 100) if self.bid_count > 0 else 0
        
        logging.info(f"Overall Stats:")
        logging.info(f"  Total Bids: {self.bid_count}")
        logging.info(f"  Projects Won: {self.wins_count} ({win_rate:.1f}% win rate)")
        logging.info(f"  Elite Projects: {self.elite_bid_count} ({elite_percentage:.1f}%)")
        logging.info(f"  Bids Today: {self.bids_today}")
        
        # Skip reasons
        total_skipped = sum(self.skipped_projects.values())
        if total_skipped > 0:
            logging.info(f"\nSkipped Projects: {total_skipped}")
            for reason, count in self.skipped_projects.items():
                percentage = (count / total_skipped * 100)
                logging.info(f"  {reason.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
        
        # Best performing hours
        if self.performance_data['by_hour']:
            logging.info("\n⏰ Activity by Hour:")
            sorted_hours = sorted(
                self.performance_data['by_hour'].items(),
                key=lambda x: x[1]['bids'],
                reverse=True
            )[:5]
            for hour, data in sorted_hours:
                logging.info(f"  {hour}:00 - {data['bids']} bids")
        
        # Category performance
        if self.performance_data['by_category']:
            logging.info("\n📁 Top Categories:")
            sorted_categories = sorted(
                self.performance_data['by_category'].items(),
                key=lambda x: x[1]['bids'],
                reverse=True
            )[:5]
            for category, data in sorted_categories:
                logging.info(f"  {category}: {data['bids']} bids")
        
        # Message variant performance
        if self.config['performance']['ab_testing_enabled'] and self.message_variants:
            logging.info("\n💬 Message Variant Usage:")
            for variant, count in self.message_variants.items():
                percentage = (count / sum(self.message_variants.values()) * 100) if sum(self.message_variants.values()) > 0 else 0
                logging.info(f"  {variant}: {count} ({percentage:.1f}%)")

    def realtime_monitor_with_bidding(self):
        """Enhanced monitoring loop with smart features"""
        logging.info("🚀 Starting Enhanced AutoWork Bot...")
        logging.info(f"User ID: {self.user_id}")
        logging.info(f"Smart Features: {'Enabled' if self.config['smart_bidding']['enabled'] else 'Disabled'}")
        logging.info(f"Client Filtering: {'Enabled' if self.config['client_filtering']['enabled'] else 'Disabled'}")
        logging.info(f"Portfolio Matching: {'Enabled' if self.config['filtering']['portfolio_matching'] else 'Disabled'}")
        logging.info(f"A/B Testing: {'Enabled' if self.config['performance']['ab_testing_enabled'] else 'Disabled'}")
        
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
                    # Wait until next day
                    hours_until_midnight = (24 - datetime.now().hour)
                    logging.info(f"Waiting {hours_until_midnight} hours until midnight...")
                    time.sleep(hours_until_midnight * 3600)
                    continue
                
                # Fetch and process projects
                projects = self.get_active_projects(limit=self.config['filtering']['max_projects_per_cycle'])
                
                if projects:
                    logging.info(f"\n🔄 Cycle {cycle_count}: Processing top projects from {len(projects)} fetched")
                    
                    new_bids = 0
                    projects_analyzed = 0
                    
                    for project in projects:
                        if project["id"] not in self.processed_projects:
                            projects_analyzed += 1
                            
                            # Place bid
                            success = self.place_bid(project)
                            
                            if success:
                                new_bids += 1
                                
                                # Smart delay based on priority
                                priority_score, _ = self.calculate_bid_priority(project)
                                if priority_score > 150:
                                    delay = 2  # Fast for high priority
                                elif priority_score > 100:
                                    delay = 3
                                else:
                                    delay = 5
                                
                                time.sleep(delay)
                            
                            # Stop if we've bid enough this cycle
                            if new_bids >= 10:  # Max 10 bids per cycle
                                break
                    
                    if projects_analyzed == 0:
                        logging.info("No new projects to analyze")
                    else:
                        logging.info(f"Analyzed {projects_analyzed} new projects, placed {new_bids} bids")
                    
                    error_count = 0  # Reset on success
                else:
                    error_count += 1
                    logging.warning(f"No projects fetched (error count: {error_count}/{max_errors})")
                    
                    if error_count >= max_errors:
                        logging.error(f"Max errors reached. Waiting {self.config['monitoring']['error_retry_delay_seconds']} seconds...")
                        time.sleep(self.config['monitoring']['error_retry_delay_seconds'])
                        error_count = 0
                
                # Analyze performance periodically
                if cycle_count % self.config['performance']['analyze_every_n_cycles'] == 0:
                    self.analyze_performance()
                
                # Save state
                self.save_state_to_redis()
                
                # Determine wait time based on time of day
                current_hour = datetime.now().hour
                if 2 <= current_hour <= 6:  # Late night - less activity
                    wait_time = self.config['monitoring']['off_hours_interval']
                elif 8 <= current_hour <= 22:  # Peak hours
                    wait_time = self.config['monitoring']['peak_hours_interval']
                else:
                    wait_time = self.config['monitoring']['check_interval_seconds']
                
                # Show summary
                if self.bid_count > 0:
                    win_rate = (self.wins_count / self.bid_count * 100)
                    elite_rate = (self.elite_bid_count / self.bid_count * 100)
                    skip_rate = (sum(self.skipped_projects.values()) / (self.bid_count + sum(self.skipped_projects.values())) * 100)
                    
                    logging.info(f"📈 Stats: {self.bid_count} bids | {win_rate:.1f}% win | {elite_rate:.1f}% elite | {skip_rate:.1f}% filtered")
                
                logging.info(f"💤 Waiting {wait_time} seconds until next cycle...")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                logging.info("\n⏹️  Bot stopped by user")
                self.analyze_performance()
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
    # For local testing
    bot = AutoWorkMinimal()
    bot.realtime_monitor_with_bidding()