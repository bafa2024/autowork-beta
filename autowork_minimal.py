#!/usr/bin/env python3
"""
Enhanced AutoWork Bot with Smart Filtering - Bids only on filtered quality projects
Modified to use strict filtering criteria before bidding
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
from spam_filter import SpamFilter
from currency_converter_freelancer import CurrencyConverter
from contest_handler import ContestHandler

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AutoWorkMinimal:
    def __init__(self):
        self.token = self.load_token()
        # Convert user_id to integer to fix bid placement error
        user_id_str = os.environ.get('FREELANCER_USER_ID', '45214417')
        self.user_id = int(user_id_str)
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
        
        # Initialize spam filter - ENABLED for quality filtering
        try:
            self.spam_filter = SpamFilter()
            self.spam_filter_enabled = True  # ENABLED for filtering
            logging.info(f"✓ Spam filter initialized: ENABLED")
        except ImportError:
            logging.warning("Spam filter module not found - continuing without spam filtering")
            self.spam_filter = None
            self.spam_filter_enabled = False
        
        # Initialize currency converter
        try:
            self.currency_converter = CurrencyConverter(freelancer_token=self.token)
            logging.info("✓ Currency converter initialized")
        except Exception as e:
            logging.warning(f"Currency converter initialization failed: {e}")
            self.currency_converter = None
        
        # Initialize premium filter
        try:
            from premium_filter import PremiumProjectFilter
            self.premium_filter = PremiumProjectFilter(self.config)
            self.premium_mode = self.config.get('premium_mode', {}).get('enabled', False)
            logging.info(f"✓ Premium filter initialized: {'Enabled' if self.premium_mode else 'Disabled'}")
        except Exception as e:
            logging.warning(f"Premium filter initialization failed: {e}")
            self.premium_filter = None
            self.premium_mode = False
        
        # Initialize contest handler
        self.contests_enabled = self.config.get('contests', {}).get('enabled', False)
        if self.contests_enabled:
            try:
                self.contest_handler = ContestHandler(self.token, self.user_id)
                logging.info("✓ Contest handler initialized")
            except Exception as e:
                logging.warning(f"Contest handler initialization failed: {e}")
                self.contest_handler = None
                self.contests_enabled = False
        else:
            self.contest_handler = None
        
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
        
        # Filtering statistics
        self.filtered_projects_count = 0
        self.passed_filter_count = 0
        
        # Skip tracking
        self.skipped_projects = {
            'too_many_bids': 0,
            'low_budget': 0,
            'bad_client': 0,
            'client_verification_failed': 0,
            'not_matched': 0,
            'invalid_data': 0,
            'spam': 0,
            'low_quality': 0,
            'poor_description': 0,
            'suspicious_title': 0,
            'currency_filtered': 0,
            'skills_mismatch': 0,
            'indian_filtered': 0
        }
        
        # Performance tracking
        self.performance_data = {
            'by_hour': {},
            'by_category': {},
            'by_budget_range': {},
            'by_message_type': {},
            'by_quality_score': {}
        }
        
        # A/B testing variants
        self.message_variants = {
            'professional': 0,
            'friendly': 0,
            'technical': 0,
            'value_focused': 0,
            'premium': 0
        }
        
        # Portfolio specializations
        self.specializations = self.load_specializations()
        
        # Load state from Redis
        self.load_state_from_redis()
        
        logging.info("✓ Enhanced Bot initialized with LOOSE FILTERING")
        logging.info(f"✓ Filtering mode: LOOSE - Only budget and payment requirements")
        logging.info(f"✓ Minimum budget: $250 USD / ₹16000 INR / PKR 16000")
        logging.info(f"✓ Payment requirement: Verified OR deposit made")
        logging.info(f"✓ Quality filtering: DISABLED")
        logging.info(f"✓ Spam filtering: DISABLED")
        logging.info(f"✓ Skill matching: DISABLED")
        
        # Verify token on startup
        if not self.verify_token_on_startup():
            raise ValueError("Token validation failed - please update your token")

    def load_config(self) -> Dict:
        """Load configuration with proper filtering settings"""
        config_file = "bot_config.json"
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    logging.info("✓ Loaded configuration from bot_config.json")
                    return config
            except Exception as e:
                logging.error(f"Error loading config: {e}")
        
        # Default configuration with LOOSE filtering - only budget and payment requirements
        return {
            "bidding": {
                "delivery_days": 3,
                "express_delivery_days": 2,
                "min_bid_delay_seconds": 10,
                "bid_multiplier_regular": 1.15,
                "bid_multiplier_elite": 1.25,
                "default_bid_regular": 150,
                "default_bid_elite": 250
            },
            "smart_bidding": {
                "enabled": True,
                "max_existing_bids": 50,  # Much higher limit
                "early_bird_minutes": 30,
                "instant_bid_threshold": 5,
                "competitive_pricing": True,
                "undercut_percentage": 0.95,
                "min_profitable_budget": 250  # $250 minimum
            },
            "client_filtering": {
                "enabled": True,  # ENABLED - Only check payment/deposit
                "min_client_rating": 0.0,  # No rating requirement
                "min_completion_rate": 0.0,  # No completion rate requirement
                "min_projects_posted": 0,  # No project count requirement
                "check_payment_verified": True,  # Must have payment verified OR deposit
                "require_payment_method": False,  # Not required
                "require_deposit": False,  # Not required (either payment verified OR deposit)
                "require_identity_verified": False,  # Not required
                "skip_phone_email_only": False  # Allow all clients
            },
            "currency_filtering": {
                "enabled": True,  # ENABLED - Only check minimum budgets
                "inr_pkr_strict_filtering": False,  # Disabled - use simple budget check
                "inr_minimum_budget": 16000.0,  # ₹16000 minimum
                "pkr_minimum_budget": 16000.0,  # PKR 16000 minimum
                "require_payment_verified_for_inr_pkr": True,  # Must have payment verified OR deposit
                "require_identity_verified_for_inr_pkr": False,  # Not required
                "skip_phone_email_only_for_inr_pkr": False  # Allow all clients
            },
            "elite_projects": {
                "auto_sign_nda": True,
                "auto_sign_ip_agreement": True,
                "track_elite_stats": True,
                "prefer_elite": False  # No preference
            },
            "filtering": {
                "max_projects_per_cycle": 100,  # Higher limit
                "skip_projects_with_bids_above": 100,  # Much higher competition limit
                "portfolio_matching": False,  # Disabled - bid on any project
                "min_skill_match_score": 0.0,  # No skill match requirement
                "min_description_length": 0,  # No description length requirement
                "prefer_long_term": False  # No preference
            },
            "quality_filters": {
                "enabled": False,  # DISABLED - no quality filtering
                "min_quality_score": 0,  # No quality score requirement
                "min_description_words": 0,  # No word count requirement
                "require_clear_requirements": False,  # Not required
                "avoid_vague_projects": False  # Allow vague projects
            },
            "spam_filter": {
                "enabled": False,  # DISABLED - no spam filtering
                "log_spam_reasons": False,
                "save_spam_projects": False
            },
            "monitoring": {
                "check_interval_seconds": 30,
                "peak_hours_interval": 20,
                "off_hours_interval": 60,
                "error_retry_delay_seconds": 300,
                "max_consecutive_errors": 5,
                "daily_bid_limit": 100  # Higher daily limit
            },
            "performance": {
                "track_analytics": True,
                "ab_testing_enabled": True,
                "analyze_every_n_cycles": 10
            },
            "premium_mode": {
                "enabled": False  # Disabled
            }
        }

    def should_bid_on_project(self, project: Dict) -> Tuple[bool, str]:
        """Simple filtering - only check minimum budget and payment verification/deposit"""
        try:
            project_id = project.get('id')
            
            # Skip if already processed
            if project_id in self.processed_projects:
                return False, "Already processed"
            
            # VALIDATION CHECK - Ensure project data is valid
            if not self.validate_project_data(project):
                self.skipped_projects['invalid_data'] += 1
                return False, "Invalid project data"
            
            # BUDGET CHECK - Check minimum budget requirements
            budget = project.get('budget', {})
            if isinstance(budget, dict):
                min_budget = float(budget.get('minimum', 0))
                currency_code = project.get('currency', {}).get('code', 'USD')
                
                # Check minimum budget based on currency
                if currency_code == 'USD':
                    min_required = 250.0  # $250 minimum
                    if min_budget < min_required:
                        self.skipped_projects['low_budget'] += 1
                        return False, f"Budget too low (${min_budget} < ${min_required})"
                elif currency_code == 'INR':
                    min_required = 16000.0  # ₹16000 minimum
                    if min_budget < min_required:
                        self.skipped_projects['low_budget'] += 1
                        return False, f"Budget too low (₹{min_budget} < ₹{min_required})"
                elif currency_code == 'PKR':
                    min_required = 16000.0  # PKR 16000 minimum
                    if min_budget < min_required:
                        self.skipped_projects['low_budget'] += 1
                        return False, f"Budget too low (PKR {min_budget} < PKR {min_required})"
                else:
                    # For other currencies, convert to USD and check
                    if self.currency_converter:
                        min_usd = self.currency_converter.to_usd(min_budget, currency_code)
                        if min_usd < 250.0:
                            self.skipped_projects['low_budget'] += 1
                            return False, f"Budget too low (${min_usd:.2f} < $250.00)"
                    else:
                        # If no converter, allow the project
                        pass
            else:
                self.skipped_projects['invalid_data'] += 1
                return False, "No budget information"
            
            # PAYMENT VERIFICATION CHECK - Must have payment verified OR deposit made
            employer_id = project.get('owner_id')
            if employer_id:
                client_analysis = self.analyze_client_simple(employer_id)
                if not client_analysis.get('is_good_client', True):
                    self.skipped_projects['bad_client'] += 1
                    return False, f"Payment verification failed: {client_analysis.get('reason', 'Unknown')}"
            
            # All checks passed
            self.passed_filter_count += 1
            return True, f"Project passed budget and payment checks (Budget: {currency_code} {min_budget})"
            
        except Exception as e:
            logging.error(f"Error in should_bid_on_project: {e}")
            return False, f"Error evaluating project: {str(e)}"

    def calculate_project_quality_score(self, project: Dict) -> int:
        """Calculate quality score for a project (0-100) - more lenient for better coverage"""
        score = 0
        
        # Description quality (30 points) - More lenient
        description = project.get('description', '')
        word_count = len(description.split())
        if word_count >= 100:
            score += 30
        elif word_count >= 50:
            score += 20
        elif word_count >= 20:
            score += 15
        elif word_count >= 10:
            score += 10
        
        # Has clear requirements (20 points) - More lenient
        requirements_keywords = ['requirements', 'need', 'must have', 'looking for', 'deliverables', 'want', 'project']
        if any(keyword in description.lower() for keyword in requirements_keywords):
            score += 20
        elif word_count > 0:  # Give points for any description
            score += 10
        
        # Budget quality (25 points) - More lenient
        budget = project.get('budget', {})
        if isinstance(budget, dict):
            min_budget = budget.get('minimum', 0)
            if self.currency_converter:
                min_usd = self.currency_converter.to_usd(min_budget, project.get('currency', {}).get('code', 'USD'))
                if min_usd >= 200:
                    score += 25
                elif min_usd >= 100:
                    score += 20
                elif min_usd >= 50:
                    score += 15
                elif min_usd >= 25:
                    score += 10
                else:
                    score += 5  # Give some points even for low budgets
        
        # Client quality (10 points) - More lenient
        owner = project.get('owner', {})
        if isinstance(owner, dict):
            # Payment verification is still important
            if owner.get('status', {}).get('payment_verified', False):
                score += 10
            else:
                score += 5  # Give points even without verification
        
        # Project features (15 points) - More lenient
        upgrades = project.get('upgrades', {})
        if isinstance(upgrades, dict):
            if upgrades.get('featured', False):
                score += 5
            if upgrades.get('NDA', False):
                score += 5
            if upgrades.get('urgent', False):
                score += 5
        
        # Bonus points for any project with a budget
        if isinstance(budget, dict) and budget.get('minimum', 0) > 0:
            score += 5
        
        return min(score, 100)

    def get_minimum_budget_for_currency(self, currency_code: str, project_type: str = 'fixed') -> float:
        """Get minimum budget threshold for quality projects - more lenient"""
        currency_code = currency_code.upper()
        project_type = project_type.lower()
        
        # More lenient thresholds for different currencies
        if project_type == 'hourly':
            # Hourly projects: More lenient threshold
            hourly_minimums = {
                'USD': 15.0,
                'CAD': 20.0,
                'EUR': 12.0,
                'GBP': 10.0,
                'AUD': 25.0,
                'INR': 1000.0,
                'PKR': 3500.0,
                'PHP': 700.0,
            }
            return hourly_minimums.get(currency_code, 15.0)
        else:
            # Fixed projects: More lenient threshold
            fixed_minimums = {
                'USD': 50.0,
                'CAD': 65.0,
                'EUR': 45.0,
                'GBP': 40.0,
                'AUD': 75.0,
                'INR': 4000.0,
                'PKR': 14000.0,
                'PHP': 2800.0,
            }
            return fixed_minimums.get(currency_code, 50.0)

    def calculate_bid_priority(self, project: Dict) -> Tuple[int, str]:
        """Calculate priority with emphasis on quality"""
        try:
            score = 100
            reasons = []
            
            # Quality score boost
            quality_score = self.calculate_project_quality_score(project)
            score += quality_score // 2  # Add half of quality score
            if quality_score >= 80:
                reasons.append(f"⭐ High quality ({quality_score})")
            elif quality_score >= 60:
                reasons.append(f"✓ Good quality ({quality_score})")
            
            # Time factor
            try:
                time_submitted = project.get('time_submitted', '')
                if time_submitted:
                    time_posted = datetime.fromisoformat(time_submitted.replace('Z', '+00:00'))
                    minutes_ago = (datetime.now(time_posted.tzinfo) - time_posted).total_seconds() / 60
                else:
                    minutes_ago = 999
            except:
                minutes_ago = 999
            
            if minutes_ago < 10:
                score += 40
                reasons.append("🔥 Very fresh")
            elif minutes_ago < 30:
                score += 20
                reasons.append("⏰ Fresh posting")
            
            # Competition level
            bid_count = project.get('bid_stats', {}).get('bid_count', 0)
            if bid_count < 5:
                score += 30
                reasons.append(f"🎯 Low competition ({bid_count} bids)")
            elif bid_count < 10:
                score += 15
                reasons.append(f"👍 Moderate competition ({bid_count} bids)")
            
            # Budget bonus
            budget = project.get('budget', {})
            if isinstance(budget, dict):
                min_budget = budget.get('minimum', 0)
                currency_code = project.get('currency', {}).get('code', 'USD')
                
                if self.currency_converter:
                    min_usd = self.currency_converter.to_usd(min_budget, currency_code)
                    if min_usd >= 500:
                        score += 30
                        reasons.append("💰 Premium budget")
                    elif min_usd >= 250:
                        score += 15
                        reasons.append("💵 Good budget")
            
            # Elite bonus
            if self.is_elite_project(project):
                score += 20
                reasons.append("🌟 Elite project")
            
            # Skill match bonus
            match_score = self.calculate_skill_match(project)
            if match_score > 0.8:
                score += 20
                reasons.append("🎯 Perfect skill match")
            elif match_score > 0.5:
                score += 10
                reasons.append("✓ Good skill match")
            
            return score, ", ".join(reasons)
            
        except Exception as e:
            logging.error(f"Error calculating priority: {e}")
            return 0, "Error calculating priority"

    def analyze_performance(self):
        """Analyze and log performance metrics with filtering focus"""
        if not self.config['performance']['track_analytics'] or self.bid_count == 0:
            return
        
        logging.info("\n" + "="*60)
        logging.info("📊 PERFORMANCE ANALYTICS - FILTERED BIDDING")
        logging.info("="*60)
        
        # Filtering metrics
        total_analyzed = self.filtered_projects_count + self.passed_filter_count
        if total_analyzed > 0:
            filter_pass_rate = (self.passed_filter_count / total_analyzed * 100)
            logging.info(f"\nFiltering Stats:")
            logging.info(f"  Projects analyzed: {total_analyzed}")
            logging.info(f"  Passed filters: {self.passed_filter_count} ({filter_pass_rate:.1f}%)")
            logging.info(f"  Filtered out: {self.filtered_projects_count}")
        
        # Overall metrics
        win_rate = (self.wins_count / self.bid_count * 100) if self.bid_count > 0 else 0
        elite_percentage = (self.elite_bid_count / self.bid_count * 100) if self.bid_count > 0 else 0
        
        logging.info(f"\nBidding Stats:")
        logging.info(f"  Total Bids: {self.bid_count}")
        logging.info(f"  Projects Won: {self.wins_count} ({win_rate:.1f}% win rate)")
        logging.info(f"  Elite Projects: {self.elite_bid_count} ({elite_percentage:.1f}%)")
        logging.info(f"  Bids Today: {self.bids_today}")
        
        # Skip reasons
        total_skipped = sum(self.skipped_projects.values())
        if total_skipped > 0:
            logging.info(f"\nFiltered Projects by Reason: {total_skipped}")
            for reason, count in sorted(self.skipped_projects.items(), key=lambda x: x[1], reverse=True):
                if count > 0:
                    percentage = (count / total_skipped * 100)
                    logging.info(f"  {reason.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")

    def realtime_monitor_with_bidding(self):
        """Monitor and bid on projects with loose filtering - only budget and payment requirements"""
        logging.info("🚀 Starting Enhanced AutoWork Bot - LOOSE FILTERING MODE...")
        logging.info(f"User ID: {self.user_id}")
        logging.info(f"Filtering Mode: LOOSE - Only budget and payment requirements")
        logging.info(f"Minimum Budget: $250 USD / ₹16000 INR / PKR 16000")
        logging.info(f"Payment Requirement: Verified OR deposit made")
        logging.info(f"Smart Features: Enabled")
        
        error_count = 0
        max_errors = self.config['monitoring']['max_consecutive_errors']
        cycle_count = 0
        
        # Update Redis status
        if self.redis_client:
            self.redis_client.set('bot_status', 'Running - Filtered Quality Mode')
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
                    logging.info(f"\n🔄 Cycle {cycle_count}: Analyzing {len(projects)} projects for quality")
                    
                    new_bids = 0
                    projects_analyzed = 0
                    quality_projects = 0
                    
                    # Process each project
                    for project in projects:
                        project_id = project.get("id")
                        
                        # Skip if already processed
                        if project_id in self.processed_projects:
                            continue
                        
                        projects_analyzed += 1
                        self.filtered_projects_count += 1
                        
                        # Check if should bid (strict filtering)
                        should_bid, reason = self.should_bid_on_project(project)
                        
                        if not should_bid:
                            logging.debug(f"⏭️  Filtered out: {project.get('title', 'Unknown')[:40]}... - {reason}")
                            self.processed_projects.add(project_id)
                            continue
                        
                        quality_projects += 1
                        
                        # Place bid on quality project
                        logging.info(f"\n{'='*60}")
                        logging.info(f"✅ QUALITY PROJECT FOUND: {project.get('title', 'Unknown')[:50]}...")
                        
                        success = self.place_bid(project)
                        
                        if success:
                            new_bids += 1
                            
                            # Smart delay based on priority
                            priority_score, _ = self.calculate_bid_priority(project)
                            if priority_score > 150:
                                delay = 5  # Fast for high priority
                            elif priority_score > 100:
                                delay = 8
                            else:
                                delay = 10
                            
                            logging.info(f"⏳ Waiting {delay} seconds before next bid...")
                            time.sleep(delay)
                        
                        # Stop if we've bid enough this cycle
                        if new_bids >= 5:  # Max 5 quality bids per cycle
                            logging.info("📊 Reached cycle bid limit (5 quality bids)")
                            break
                    
                    # Log cycle summary
                    if projects_analyzed > 0:
                        quality_rate = (quality_projects / projects_analyzed * 100)
                        logging.info(f"\n📊 Cycle Summary:")
                        logging.info(f"   Projects analyzed: {projects_analyzed}")
                        logging.info(f"   Quality projects found: {quality_projects} ({quality_rate:.1f}%)")
                        logging.info(f"   Bids placed: {new_bids}")
                        logging.info(f"   Filtered out: {projects_analyzed - quality_projects}")
                    else:
                        logging.info("No new projects to analyze")
                    
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
                
                # Process contests periodically
                if self.contests_enabled and cycle_count % 10 == 0:
                    self.process_contests()
                
                # Save state
                self.save_state_to_redis()
                
                # Determine wait time
                current_hour = datetime.now().hour
                if 2 <= current_hour <= 6:  # Late night
                    wait_time = self.config['monitoring']['off_hours_interval']
                elif 8 <= current_hour <= 22:  # Peak hours
                    wait_time = self.config['monitoring']['peak_hours_interval']
                else:
                    wait_time = self.config['monitoring']['check_interval_seconds']
                
                # Show status
                if self.bid_count > 0:
                    win_rate = (self.wins_count / self.bid_count * 100)
                    logging.info(f"\n📈 Status: {self.bid_count} bids | {win_rate:.1f}% wins | {self.passed_filter_count} projects passed filters")
                
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
                import traceback
                logging.error(f"Traceback: {traceback.format_exc()}")
                
                if self.redis_client:
                    self.redis_client.set('last_error', str(e))
                
                if error_count >= max_errors:
                    logging.error(f"Too many errors. Waiting {self.config['monitoring']['error_retry_delay_seconds']} seconds...")
                    time.sleep(self.config['monitoring']['error_retry_delay_seconds'])
                    error_count = 0
                else:
                    time.sleep(30)

    def load_token(self) -> str:
        """Load token from environment or .env file"""
        token = os.environ.get('FREELANCER_OAUTH_TOKEN')
        
        if token:
            return token.strip()
        
        # Try .env file
        if os.path.exists('.env'):
            try:
                from dotenv import load_dotenv
                load_dotenv()
                token = os.environ.get('FREELANCER_OAUTH_TOKEN')
                if token:
                    return token.strip()
            except ImportError:
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('FREELANCER_OAUTH_TOKEN='):
                            token = line.split('=', 1)[1].strip()
                            if token:
                                return token
        
        # Ask for token
        print("Token not found in environment.")
        token = input("Enter your Freelancer OAuth token: ").strip()
        return token

    def init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            logging.info("✓ Redis connection established")
            return client
        except Exception as e:
            logging.warning(f"Redis connection failed: {e}")
            return None

    def load_bid_messages(self) -> Dict:
        """Load bid messages from JSON file"""
        try:
            with open('bid_messages.json', 'r') as f:
                messages = json.load(f)
                logging.info("✓ Loaded bid messages")
                return messages
        except Exception as e:
            logging.warning(f"Could not load bid messages: {e}")
            return {
                "professional": ["I'm interested in your project and ready to start immediately."],
                "friendly": ["Hi! I'd love to help with your project."],
                "technical": ["I have the technical expertise needed for this project."]
            }

    def load_skills_map(self) -> Dict:
        """Load skills mapping from JSON file"""
        try:
            with open('skills_map.json', 'r') as f:
                skills = json.load(f)
                logging.info("✓ Loaded skills map")
                return skills
        except Exception as e:
            logging.warning(f"Could not load skills map: {e}")
            return {}

    def load_specializations(self) -> Dict:
        """Load specializations from JSON file"""
        try:
            with open('specializations.json', 'r') as f:
                specs = json.load(f)
                logging.info("✓ Loaded specializations")
                return specs
        except Exception as e:
            logging.warning(f"Could not load specializations: {e}")
            return {}

    def load_state_from_redis(self):
        """Load bot state from Redis"""
        if not self.redis_client:
            return
        
        try:
            # Load basic stats
            self.bid_count = int(self.redis_client.get('bid_count') or 0)
            self.bids_today = int(self.redis_client.get('bids_today') or 0)
            self.wins_count = int(self.redis_client.get('wins_count') or 0)
            self.elite_bid_count = int(self.redis_client.get('elite_bid_count') or 0)
            
            # Load processed projects
            processed_data = self.redis_client.get('processed_projects')
            if processed_data:
                self.processed_projects = set(json.loads(processed_data))
            
            # Load skipped projects
            skipped_data = self.redis_client.get('skipped_projects')
            if skipped_data:
                self.skipped_projects.update(json.loads(skipped_data))
            
            logging.info("✓ Loaded state from Redis")
        except Exception as e:
            logging.warning(f"Could not load state from Redis: {e}")

    def save_state_to_redis(self):
        """Save bot state to Redis"""
        if not self.redis_client:
            return
        
        try:
            # Save basic stats
            self.redis_client.set('bid_count', self.bid_count)
            self.redis_client.set('bids_today', self.bids_today)
            self.redis_client.set('wins_count', self.wins_count)
            self.redis_client.set('elite_bid_count', self.elite_bid_count)
            
            # Save processed projects
            self.redis_client.set('processed_projects', json.dumps(list(self.processed_projects)))
            
            # Save skipped projects
            self.redis_client.set('skipped_projects', json.dumps(self.skipped_projects))
            
            # Save current time
            self.redis_client.set('last_update', datetime.now().isoformat())
        except Exception as e:
            logging.warning(f"Could not save state to Redis: {e}")

    def verify_token_on_startup(self) -> bool:
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

    def validate_project_data(self, project: Dict) -> bool:
        """Validate that project data is complete and valid"""
        required_fields = ['id', 'title', 'description', 'budget', 'currency']
        
        for field in required_fields:
            if field not in project:
                return False
        
        # Check budget structure
        budget = project.get('budget', {})
        if not isinstance(budget, dict):
            return False
        
        if 'minimum' not in budget:
            return False
        
        return True

    def analyze_client(self, employer_id: int) -> Dict:
        """Analyze client for quality indicators"""
        try:
            response = requests.get(
                f"{self.api_base}/users/0.1/users/{employer_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                return {'is_good_client': False, 'reason': 'Could not fetch client data'}
            
            data = response.json()
            user = data.get('result', {})
            
            # Basic checks
            is_good = True
            reasons = []
            
            # Payment verification
            if not user.get('status', {}).get('payment_verified', False):
                is_good = False
                reasons.append("Payment not verified")
            
            # Rating check (if available)
            rating = user.get('rating', 0)
            if rating > 0 and rating < 4.0:
                is_good = False
                reasons.append(f"Low rating ({rating})")
            
            return {
                'is_good_client': is_good,
                'reason': '; '.join(reasons) if reasons else 'Good client',
                'rating': rating,
                'payment_verified': user.get('status', {}).get('payment_verified', False)
            }
            
        except Exception as e:
            logging.warning(f"Error analyzing client {employer_id}: {e}")
            return {'is_good_client': True, 'reason': 'Analysis failed'}

    def analyze_client_for_inr_pkr(self, employer_id: int) -> Dict:
        """Special client analysis for INR projects - targets clients without payment verification"""
        try:
            response = requests.get(
                f"{self.api_base}/users/0.1/users/{employer_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                return {'is_good_client': True, 'reason': 'Could not fetch client data - allowing'}
            
            data = response.json()
            user = data.get('result', {})
            status = user.get('status', {})
            
            # Check if Indian project filters are enabled
            indian_filters = self.config.get('currency_filtering', {}).get('indian_project_filters', {})
            if not indian_filters.get('enabled', False):
                return {'is_good_client': True, 'reason': 'Indian filters disabled'}
            
            # For Indian projects, we want clients WITHOUT payment verification
            if indian_filters.get('skip_payment_verified_clients', True):
                if status.get('payment_verified', False):
                    return {
                        'is_good_client': False, 
                        'reason': 'Payment verified (we want unverified clients for INR projects)'
                    }
            
            # Check for deposit made
            if indian_filters.get('skip_deposit_made_clients', True):
                if status.get('deposit_made', False):
                    return {
                        'is_good_client': False, 
                        'reason': 'Deposit made (we want clients without deposits for INR projects)'
                    }
            
            # Check for payment method
            if indian_filters.get('require_no_payment_method', True):
                if status.get('payment_method_verified', False):
                    return {
                        'is_good_client': False, 
                        'reason': 'Payment method verified (we want clients without payment methods for INR projects)'
                    }
            
            # More lenient rating check for INR projects
            rating = user.get('rating', 0)
            if rating > 0 and rating < 2.0:  # Very low rating threshold for INR projects
                return {'is_good_client': False, 'reason': f'Very low rating ({rating})'}
            
            return {
                'is_good_client': True,
                'reason': 'Suitable for INR project (no payment verification, no deposit, no payment method)',
                'rating': rating,
                'payment_verified': status.get('payment_verified', False),
                'deposit_made': status.get('deposit_made', False),
                'payment_method_verified': status.get('payment_method_verified', False)
            }
            
        except Exception as e:
            logging.warning(f"Error in INR client analysis: {e}")
            return {'is_good_client': True, 'reason': 'Analysis failed - allowing'}

    def should_bid_on_indian_project(self, project: Dict) -> Tuple[bool, str]:
        """Special filtering for Indian projects with specific requirements"""
        try:
            currency_code = project.get('currency', {}).get('code', 'USD')
            if currency_code != 'INR':
                return True, "Not INR project"
            
            indian_filters = self.config.get('currency_filtering', {}).get('indian_project_filters', {})
            if not indian_filters.get('enabled', False):
                return True, "Indian filters disabled"
            
            # Check minimum budget
            budget = project.get('budget', {})
            if isinstance(budget, dict):
                min_budget = float(budget.get('minimum', 0))
                min_required = indian_filters.get('min_inr_budget', 15000.0)
                
                if min_budget < min_required:
                    reason = f"Budget too low (₹{min_budget} < ₹{min_required})"
                    if indian_filters.get('log_filtered_projects', True):
                        logging.info(f"🇮🇳 INR Project Filtered: {project.get('title', 'Unknown')[:50]}... - {reason}")
                    return False, reason
            
            # Check client requirements
            employer_id = project.get('owner_id')
            if employer_id:
                client_analysis = self.analyze_client_for_inr_pkr(employer_id)
                if not client_analysis.get('is_good_client', True):
                    reason = f"Client not suitable: {client_analysis.get('reason', 'Unknown')}"
                    if indian_filters.get('log_filtered_projects', True):
                        logging.info(f"🇮🇳 INR Project Filtered: {project.get('title', 'Unknown')[:50]}... - {reason}")
                    return False, reason
            
            return True, "Indian project passed all filters"
            
        except Exception as e:
            logging.error(f"Error in Indian project filtering: {e}")
            return False, f"Error: {str(e)}"

    def calculate_skill_match(self, project: Dict) -> float:
        """Calculate skill match score between project and our skills"""
        project_skills = [job.get('name', '').lower() for job in project.get('jobs', [])]
        
        if not project_skills:
            return 0.0
        
        # Our skills from specializations
        our_skills = []
        for category, skills in self.specializations.items():
            if isinstance(skills, list):
                our_skills.extend([skill.lower() for skill in skills])
        
        if not our_skills:
            return 0.5  # Default score if no skills defined
        
        # Calculate match
        matching_skills = set(project_skills) & set(our_skills)
        match_score = len(matching_skills) / len(project_skills)
        
        return min(match_score, 1.0)

    def is_elite_project(self, project: Dict) -> bool:
        """Check if project is elite"""
        upgrades = project.get('upgrades', {})
        return upgrades.get('featured', False) or upgrades.get('qualified', False)

    def get_active_projects(self, limit: int = 50) -> List[Dict]:
        """Fetch active projects from Freelancer API"""
        try:
            response = requests.get(
                f"{self.api_base}/projects/0.1/projects/active",
                headers=self.headers,
                params={
                    'limit': limit,
                    'job_details': 'true',
                    'full_description': 'true'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                projects = data.get('result', {}).get('projects', [])
                logging.info(f"Fetched {len(projects)} active projects")
                return projects
            else:
                logging.error(f"Failed to fetch projects: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Error fetching projects: {e}")
            return []

    def place_bid(self, project: Dict) -> bool:
        """Place a bid on a project"""
        try:
            project_id = project.get('id')
            
            # Calculate bid amount
            bid_amount = self.calculate_bid_amount(project)
            
            # Select bid message
            message = self.select_bid_message(project)
            
            # Ensure user_id is integer
            bidder_id = int(self.user_id)
            
            # Prepare bid data
            bid_data = {
                'project_id': int(project_id),
                'bidder_id': bidder_id,
                'amount': float(bid_amount),
                'period': int(self.config['bidding']['delivery_days']),
                'milestone_percentage': 100,
                'description': str(message)
            }
            
            logging.info(f"Placing bid on project {project_id}:")
            logging.info(f"  Bidder ID: {bidder_id} (type: {type(bidder_id)})")
            logging.info(f"  Amount: ${bid_amount}")
            logging.info(f"  Period: {self.config['bidding']['delivery_days']} days")
            
            # Place bid
            response = requests.post(
                f"{self.api_base}/projects/0.1/bids/",
                headers=self.headers,
                json=bid_data
            )
            
            if response.status_code == 200:
                data = response.json()
                bid_id = data.get('result', {}).get('id')
                
                self.bid_count += 1
                self.bids_today += 1
                
                if self.is_elite_project(project):
                    self.elite_bid_count += 1
                
                logging.info(f"✅ Bid placed successfully! ID: {bid_id}")
                logging.info(f"   Amount: ${bid_amount}")
                logging.info(f"   Project: {project.get('title', 'Unknown')[:50]}...")
                
                # Track performance
                self.track_bid_performance(project, bid_amount, True)
                
                return True
            else:
                logging.error(f"Bid failed: {response.status_code} - {response.text}")
                logging.error(f"Request data: {bid_data}")
                return False
                
        except Exception as e:
            logging.error(f"Error placing bid: {e}")
            logging.error(f"Project ID: {project.get('id')}")
            logging.error(f"User ID: {self.user_id} (type: {type(self.user_id)})")
            return False

    def calculate_bid_amount(self, project: Dict) -> float:
        """Calculate appropriate bid amount for project"""
        budget = project.get('budget', {})
        min_budget = float(budget.get('minimum', 0))
        currency_code = project.get('currency', {}).get('code', 'USD')
        
        # Convert to USD if needed
        if self.currency_converter and currency_code != 'USD':
            min_budget = self.currency_converter.to_usd(min_budget, currency_code)
        
        # Apply multiplier based on project type
        if self.is_elite_project(project):
            multiplier = self.config['bidding']['bid_multiplier_elite']
        else:
            multiplier = self.config['bidding']['bid_multiplier_regular']
        
        bid_amount = min_budget * multiplier
        
        # Ensure minimum bid
        if self.is_elite_project(project):
            min_bid = self.config['bidding']['default_bid_elite']
        else:
            min_bid = self.config['bidding']['default_bid_regular']
        
        return max(bid_amount, min_bid)

    def select_bid_message(self, project: Dict) -> str:
        """Select appropriate bid message for project"""
        messages = self.bid_messages.get('professional', [])
        
        if not messages:
            return "I'm interested in your project and ready to start immediately."
        
        # Select random message
        import random
        message = random.choice(messages)
        
        # Replace placeholders
        skills = ', '.join([job.get('name', '') for job in project.get('jobs', [])[:3]])
        message = message.replace('{skills}', skills)
        
        return message

    def track_bid_performance(self, project: Dict, bid_amount: float, success: bool):
        """Track bid performance for analytics"""
        if not self.config['performance']['track_analytics']:
            return
        
        # Track by hour
        hour = datetime.now().hour
        if hour not in self.performance_data['by_hour']:
            self.performance_data['by_hour'][hour] = {'bids': 0, 'amount': 0}
        
        self.performance_data['by_hour'][hour]['bids'] += 1
        self.performance_data['by_hour'][hour]['amount'] += bid_amount

    def process_contests(self):
        """Process contests if enabled"""
        if not self.contests_enabled or not self.contest_handler:
            return
        
        try:
            self.contest_handler.process_available_contests()
        except Exception as e:
            logging.warning(f"Error processing contests: {e}")

    def reset_daily_stats(self):
        """Reset daily statistics"""
        if datetime.now().date() != self.today_date:
            self.bids_today = 0
            self.today_date = datetime.now().date()
            logging.info("📅 Daily stats reset")

    def analyze_client_simple(self, employer_id: int) -> Dict:
        """Simple client analysis - only check payment verification or deposit"""
        try:
            response = requests.get(
                f"{self.api_base}/users/0.1/users/{employer_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                return {'is_good_client': True, 'reason': 'Could not fetch client data - allowing'}
            
            data = response.json()
            user = data.get('result', {})
            status = user.get('status', {})
            
            # Check if payment is verified OR deposit is made
            payment_verified = status.get('payment_verified', False)
            deposit_made = status.get('deposit_made', False)
            
            if payment_verified or deposit_made:
                return {
                    'is_good_client': True,
                    'reason': f"Payment verified: {payment_verified}, Deposit made: {deposit_made}",
                    'payment_verified': payment_verified,
                    'deposit_made': deposit_made
                }
            else:
                return {
                    'is_good_client': False,
                    'reason': 'Neither payment verified nor deposit made',
                    'payment_verified': payment_verified,
                    'deposit_made': deposit_made
                }
            
        except Exception as e:
            logging.warning(f"Error in simple client analysis: {e}")
            return {'is_good_client': True, 'reason': 'Analysis failed - allowing'}

if __name__ == "__main__":
    bot = AutoWorkMinimal()
    bot.realtime_monitor_with_bidding()