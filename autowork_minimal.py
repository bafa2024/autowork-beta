#!/usr/bin/env python3
"""
AutoWork Minimal - No Filters Version
Bids on ALL projects that match your skills
No budget limits, no country restrictions, no bid count limits
"""

import json
import time
import urllib.request
import urllib.parse
import sqlite3
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class AutoWorkMinimal:
    def __init__(self):
        self.token = self.load_token()
        self.base_url = "https://www.freelancer.com/api"
        self.db = self.init_database()
        self.rate_limit_tracker = {"requests": [], "max_per_hour": 600}
        
        # Modified configuration - NO FILTERS!
        self.auto_bid_enabled = True
        self.max_bid_count = 999999  # Effectively no limit
        self.min_budget = 0  # Accept any budget
        self.max_project_age_hours = 24  # Bid on projects up to 24 hours old
        
        # Skill categories - organized by type
        self.skill_categories = {
            "backend_languages": [
                "PHP", "Python", "Java", "Javascript", "Nodejs", "GoLang", 
                "Ruby on Rails", "Perl", "Rust", "Scala", "Kotlin", "Swift", 
                "C#", "C++", "Elixir", "Haskell", "Clojure", "Erlang", 
                "F#", "Objective-C", "Dart"
            ],
            
            "backend_frameworks": [
                "Laravel", "Symfony", "CodeIgniter", "Django", "Flask",
                "Expressjs", "Spring", "Springboot", "Springmvc", "ASP.NET",
                "Moodle"
            ],
            
            "frontend_frameworks": [
                "Reactjs", "Vuejs", "Angular", "Nextjs", "Nuxtjs", "Svelte"
            ],
            
            "api_technologies": [
                "Graphql", "Restfulapi", "Restapi", "Websocket", "gRPC"
            ],
            
            "mobile_development": [
                "Android", "iOS", "Flutter", "React Native", "SwiftUI", 
                "Xamarin", "Ionic", "Cordova"
            ],
            
            "databases": [
                "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQLite",
                "Oracle", "SQL Server", "Cassandra", "DynamoDB"
            ],
            
            "cloud_services": [
                "AWS", "Azure", "Google Cloud", "Firebase", "Heroku",
                "DigitalOcean", "Cloudflare"
            ],
            
            "cms_ecommerce": [
                "WordPress", "Shopify", "WooCommerce", "Magento", "Drupal",
                "Joomla", "PrestaShop", "OpenCart"
            ],
            
            "frontend_basics": [
                "HTML5", "CSS3", "SASS", "LESS", "PostCSS", "JavaScript"
            ],
            
            "css_frameworks": [
                "Bootstrap", "TailwindCSS", "MaterializeCSS", "Foundation", 
                "Bulma", "UIKit", "Semantic UI"
            ],
            
            "ai_ml": [
                "ChatGPT", "OpenAI", "Machine Learning", "Deep Learning", 
                "TensorFlow", "PyTorch", "NLP", "Computer Vision"
            ],
            
            "blockchain": [
                "Blockchain", "Ethereum", "Smart Contracts", "Solidity", 
                "Web3", "NFT", "DeFi", "Cryptocurrency"
            ],
            
            "other_skills": [
                "SEO", "Digital Marketing", "Content Writing", "Graphic Design",
                "Video Editing", "Data Entry", "Translation", "Virtual Assistant"
            ]
        }
        
        # Create flat list of all skills
        self.all_skills = []
        seen = set()
        for skills in self.skill_categories.values():
            for skill in skills:
                if skill.lower() not in seen:
                    self.all_skills.append(skill)
                    seen.add(skill.lower())
        
        # All skills are priority skills now
        self.priority_search_skills = self.all_skills[:30]  # Top 30 for searching
        
        # User configuration
        self.user_id = 45214417  # Your Freelancer user ID
    
    def load_token(self) -> str:
        """Load token from .env file or ask user"""
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('FREELANCER_OAUTH_TOKEN='):
                        return line.split('=', 1)[1].strip()
        
        token = input("Enter your Freelancer OAuth token: ").strip()
        
        with open('.env', 'w') as f:
            f.write(f"FREELANCER_OAUTH_TOKEN={token}\n")
        
        return token
    
    def init_database(self) -> sqlite3.Connection:
        """Initialize SQLite database with all required tables"""
        conn = sqlite3.connect('autowork.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if projects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Update existing table
            cursor.execute("PRAGMA table_info(projects)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            # Add missing columns
            if 'matched_skills' not in existing_columns:
                cursor.execute("ALTER TABLE projects ADD COLUMN matched_skills TEXT")
            
            if 'skill_match_score' not in existing_columns:
                cursor.execute("ALTER TABLE projects ADD COLUMN skill_match_score INTEGER DEFAULT 0")
            
            # Check bids table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bids'")
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(bids)")
                bid_columns = [col[1] for col in cursor.fetchall()]
                
                if 'matched_skills' not in bid_columns:
                    cursor.execute("ALTER TABLE bids ADD COLUMN matched_skills TEXT")
        else:
            # Create new tables
            cursor.execute('''
                CREATE TABLE projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    budget_min REAL,
                    budget_max REAL,
                    currency TEXT,
                    bid_count INTEGER DEFAULT 0,
                    skills TEXT,
                    matched_skills TEXT,
                    skill_match_score INTEGER DEFAULT 0,
                    search_keyword TEXT,
                    is_elite BOOLEAN DEFAULT 0,
                    time_submitted TIMESTAMP,
                    raw_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Create other tables if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                bid_id INTEGER,
                amount REAL,
                period INTEGER,
                description TEXT,
                matched_skills TEXT,
                status TEXT DEFAULT 'pending',
                response_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                project_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("✓ Database initialized successfully")
        return conn
    
    def log_event(self, event_type: str, project_id: Optional[int] = None, details: str = ""):
        """Log monitoring events to database"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO monitoring_log (event_type, project_id, details)
            VALUES (?, ?, ?)
        ''', (event_type, project_id, details))
        self.db.commit()
    
    def check_rate_limit(self) -> bool:
        """Check if we can make an API request"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old requests
        self.rate_limit_tracker["requests"] = [
            req for req in self.rate_limit_tracker["requests"]
            if req > hour_ago
        ]
        
        # Check if we're at limit
        current_requests = len(self.rate_limit_tracker["requests"])
        if current_requests >= self.rate_limit_tracker["max_per_hour"]:
            print(f"⚠️  Rate limit reached: {current_requests}/600 requests in last hour")
            return False
        
        return True
    
    def record_request(self):
        """Record an API request"""
        self.rate_limit_tracker["requests"].append(datetime.now())
        
        # Also log to database
        cursor = self.db.cursor()
        cursor.execute("INSERT INTO rate_limits (endpoint) VALUES (?)", ("api_call",))
        self.db.commit()
    
    def api_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request with rate limiting and error handling"""
        if not self.check_rate_limit():
            return None
        
        url = f"{self.base_url}{endpoint}"
        
        request = urllib.request.Request(url)
        request.add_header('Freelancer-OAuth-V1', self.token)
        
        if method == "POST" and data:
            request.data = json.dumps(data).encode('utf-8')
            request.add_header('Content-Type', 'application/json')
            request.method = method
        
        try:
            self.record_request()
            with urllib.request.urlopen(request) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                self.log_event("rate_limited", details=f"HTTP 429 on {endpoint}")
            elif e.code != 404:  # Don't log 404s
                print(f"❌ API Error {e.code}: {e.reason}")
            return None
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None
    
    def get_matching_skills(self, project: Dict) -> List[str]:
        """Get skills from project that match our skill set - MORE AGGRESSIVE"""
        project_skills = [job['name'].lower() for job in project.get('jobs', [])]
        title = project.get('title', '').lower()
        description = project.get('description', '').lower()[:500]  # First 500 chars
        
        matching = []
        
        # Check project skills
        for skill in self.all_skills:
            skill_lower = skill.lower()
            # Check in skills
            if any(skill_lower in ps or ps in skill_lower for ps in project_skills):
                matching.append(skill)
            # Also check in title and description
            elif skill_lower in title or skill_lower in description:
                matching.append(skill)
        
        return list(set(matching))  # Remove duplicates
    
    def calculate_skill_match_score(self, project: Dict) -> int:
        """Calculate how well a project matches our skills (0-100)"""
        matching_skills = self.get_matching_skills(project)
        
        # Any match is good enough
        if matching_skills:
            return max(10, len(matching_skills) * 15)  # At least 10 points per match
        
        return 0
    
    def calculate_optimal_period(self, project: Dict) -> int:
        """Calculate optimal delivery period based on project details"""
        budget_min = project.get('budget', {}).get('minimum', 0)
        budget_max = project.get('budget', {}).get('maximum', 0)
        avg_budget = (budget_min + budget_max) / 2 if budget_max > 0 else budget_min
        
        description = project.get('description', '').lower()
        title = project.get('title', '').lower()
        
        # Base period on budget
        if avg_budget == 0:
            base_period = 7  # Default 1 week for undefined budget
        elif avg_budget < 100:
            base_period = 3
        elif avg_budget < 500:
            base_period = 7
        elif avg_budget < 1500:
            base_period = 14
        else:
            base_period = 21
        
        # Adjust for urgency
        urgent_keywords = ['urgent', 'asap', 'immediately', 'today', 'tomorrow', 'quickly', 'fast', 'hurry']
        if any(keyword in title + description for keyword in urgent_keywords):
            base_period = max(1, int(base_period * 0.5))
        
        # Quick fixes are always fast
        if any(word in title for word in ['fix', 'bug', 'error', 'issue', 'problem']):
            base_period = min(base_period, 2)
        
        # Never promise less than 1 day or more than 30 days
        return max(1, min(30, base_period))
    
    def calculate_competitive_bid_amount(self, project: Dict) -> float:
        """Calculate bid amount for ANY budget - AGGRESSIVE PRICING"""
        budget_min = project.get('budget', {}).get('minimum', 0)
        budget_max = project.get('budget', {}).get('maximum', 0)
        
        # Handle $0 budget projects
        if budget_min == 0 and budget_max == 0:
            # For undefined budget, propose reasonable amount based on description
            description = project.get('description', '').lower()
            if any(word in description for word in ['simple', 'quick', 'small', 'easy']):
                return 30
            elif any(word in description for word in ['complex', 'large', 'advanced']):
                return 250
            else:
                return 100  # Default for undefined
        
        # For hourly projects
        if project.get('type') == 'hourly':
            # Always bid at minimum or $10/hour minimum
            return max(budget_min, 10) if budget_min > 0 else 15
        
        # For fixed projects - ALWAYS bid at minimum to win
        if budget_min > 0:
            return budget_min
        elif budget_max > 0:
            # If only max is set, bid at 20% of max (aggressive)
            return budget_max * 0.2
        else:
            # Fallback
            return 50
    
    def generate_smart_bid_description(self, project: Dict, matched_skills: List[str]) -> str:
        """Generate personalized bid description - MORE AGGRESSIVE"""
        skills_text = ', '.join(matched_skills[:3]) if matched_skills else 'the required technologies'
        title = project.get('title', '').lower()
        description = project.get('description', '').lower()
        budget_min = project.get('budget', {}).get('minimum', 0)
        period = self.calculate_optimal_period(project)
        
        # Detect project type
        is_urgent = any(word in title + description for word in ['urgent', 'asap', 'immediately'])
        is_wordpress = 'wordpress' in ' '.join([s.lower() for s in matched_skills])
        is_bug_fix = any(word in title for word in ['fix', 'bug', 'error', 'issue'])
        is_simple = any(word in title + description for word in ['simple', 'easy', 'quick', 'small'])
        
        # Select appropriate template
        if is_urgent:
            template = f"""Hi! I'm available to start IMMEDIATELY!

I have the exact skills you need: {skills_text}

I'll complete this within {period} {'day' if period == 1 else 'days'} and I'm online now ready to begin.

Let's get started right away!"""

        elif is_bug_fix:
            template = f"""Hi! I can fix this issue quickly.

Expert in {skills_text}, I've fixed similar problems many times.

I'll have this resolved within {period} {'day' if period == 1 else 'days'}.

Let's fix this now!"""

        elif is_simple or budget_min < 100:
            template = f"""Hi! Perfect match for your project.

I'm skilled in {skills_text} and can deliver quality work within {period} {'day' if period == 1 else 'days'}.

Ready to start immediately!"""

        else:
            # Default template - short and to the point
            template = f"""Hi! I'm the perfect fit for your project.

Expert in {skills_text} with proven track record.
Delivery in {period} {'day' if period == 1 else 'days'}.
Available to start now.

Let's discuss!"""

        return template
    
    def fetch_latest_projects(self, limit: int = 100) -> List[Dict]:
        """Fetch ALL available projects - NO FILTERS"""
        all_projects = []
        seen_ids = set()
        
        # Method 1: Search with various terms
        search_terms = random.sample(self.all_skills, min(15, len(self.all_skills)))
        
        for term in search_terms:
            params = {
                'query': term,
                'limit': 50,
                'offset': 0,
                'job_details': 'true',
                'compact': 'true',
                # NO country filter
                # NO minimum budget filter
                'sort_field': 'time_submitted',
                'order': 'desc'
            }
            
            query_string = urllib.parse.urlencode(params, doseq=True)
            endpoint = f"/projects/0.1/projects/active/?{query_string}"
            
            response = self.api_request(endpoint)
            
            if response and 'result' in response:
                projects = response['result'].get('projects', [])
                for project in projects:
                    if project['id'] not in seen_ids:
                        # Enrich project with our analysis
                        project['matched_skills'] = self.get_matching_skills(project)
                        project['skill_match_score'] = self.calculate_skill_match_score(project)
                        all_projects.append(project)
                        seen_ids.add(project['id'])
            
            time.sleep(0.5)  # Small delay between searches
        
        # Method 2: Also get ALL recent projects without search filter
        params = {
            'limit': 100,
            'offset': 0,
            'job_details': 'true',
            'compact': 'true',
            'sort_field': 'time_submitted',
            'order': 'desc'
        }
        
        query_string = urllib.parse.urlencode(params, doseq=True)
        endpoint = f"/projects/0.1/projects/active/?{query_string}"
        
        response = self.api_request(endpoint)
        
        if response and 'result' in response:
            projects = response['result'].get('projects', [])
            for project in projects:
                if project['id'] not in seen_ids:
                    project['matched_skills'] = self.get_matching_skills(project)
                    project['skill_match_score'] = self.calculate_skill_match_score(project)
                    if project['skill_match_score'] > 0:  # Only add if we have matching skills
                        all_projects.append(project)
                        seen_ids.add(project['id'])
        
        # Sort by newest first
        all_projects.sort(key=lambda p: -p.get('time_submitted', 0))
        
        return all_projects
    
    def should_bid_immediately(self, project: Dict) -> Tuple[bool, str]:
        """Minimal checks - bid on almost everything"""
        # Check if already bid
        cursor = self.db.cursor()
        cursor.execute("SELECT id FROM bids WHERE project_id = ?", (project['id'],))
        if cursor.fetchone():
            return False, "Already bid on this project"
        
        # Get matched skills
        matched_skills = project.get('matched_skills', [])
        
        # If no direct skill match, check if we can do it anyway
        if not matched_skills:
            # Check if title or description contains any technology keywords
            title = project.get('title', '').lower()
            description = project.get('description', '').lower()[:200]
            
            # Generic tech keywords
            tech_keywords = ['website', 'app', 'software', 'develop', 'design', 'build', 'create', 
                           'code', 'program', 'fix', 'update', 'modify', 'integrate', 'api', 
                           'database', 'frontend', 'backend', 'mobile', 'web']
            
            if any(keyword in title + description for keyword in tech_keywords):
                matched_skills = ['General Development']
            else:
                return False, "No relevant keywords found"
        
        # Get project info for display
        budget_min = project.get('budget', {}).get('minimum', 0)
        budget_max = project.get('budget', {}).get('maximum', 0)
        bid_count = project.get('bid_stats', {}).get('bid_count', 0)
        
        # Build reason string
        if budget_min == 0 and budget_max == 0:
            budget_str = "Open budget"
        elif budget_min == 0:
            budget_str = f"Up to ${budget_max}"
        else:
            budget_str = f"${budget_min}-${budget_max}"
        
        reason = f"BIDDING: {', '.join(matched_skills[:2])}, {budget_str}, {bid_count} bids"
        
        return True, reason
    
    def place_bid_immediately(self, project: Dict) -> bool:
        """Place a bid immediately on a project"""
        project_id = project['id']
        project_title = project.get('title', 'Unknown')[:60]
        matched_skills = project.get('matched_skills', ['General'])
        
        print(f"\n🎯 Bidding on: {project_title}...")
        
        # Calculate bid details
        bid_amount = self.calculate_competitive_bid_amount(project)
        period = self.calculate_optimal_period(project)
        description = self.generate_smart_bid_description(project, matched_skills)
        
        # Log bid details
        budget_min = project.get('budget', {}).get('minimum', 0)
        budget_max = project.get('budget', {}).get('maximum', 0)
        
        if budget_min == 0 and budget_max == 0:
            budget_str = "Undefined budget"
        else:
            budget_str = f"${budget_min}-${budget_max}"
        
        print(f"💰 Bid: ${bid_amount} (Project: {budget_str})")
        print(f"📅 Delivery: {period} days")
        print(f"🎯 Skills: {', '.join(matched_skills[:3])}")
        
        # Prepare bid data
        bid_data = {
            'project_id': project_id,
            'bidder_id': self.user_id,
            'amount': bid_amount,
            'period': period,
            'milestone_percentage': 100,
            'description': description
        }
        
        # Place the bid
        response = self.api_request("/projects/0.1/bids/", "POST", bid_data)
        
        # Save bid record
        cursor = self.db.cursor()
        status = 'success' if response else 'failed'
        
        cursor.execute('''
            INSERT INTO bids (project_id, amount, period, description, matched_skills, status, response_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            project_id,
            bid_amount,
            period,
            description,
            ', '.join(matched_skills),
            status,
            json.dumps(response) if response else None
        ))
        self.db.commit()
        
        if response:
            bid_id = response.get('result', {}).get('id', 'Unknown')
            print(f"✅ BID SUCCESSFUL! Bid ID: {bid_id}")
            self.log_event("bid_success", project_id, f"Amount: ${bid_amount}, Period: {period} days")
            return True
        else:
            print(f"❌ Bid failed")
            self.log_event("bid_failed", project_id, "API request failed")
            return False
    
    def save_project(self, project: Dict, search_keyword: str = "monitor"):
        """Save project to database with all metadata"""
        cursor = self.db.cursor()
        
        # Check if project already exists
        cursor.execute("SELECT id FROM projects WHERE project_id = ?", (project['id'],))
        if cursor.fetchone():
            return
        
        # Extract all relevant data
        matched_skills = project.get('matched_skills', [])
        skill_match_score = project.get('skill_match_score', 0)
        skills = ', '.join([job['name'] for job in project.get('jobs', [])])
        
        # Determine if elite
        is_elite = (
            project.get('budget', {}).get('minimum', 0) >= 500 or
            project.get('upgrades', {}).get('featured', False) or
            project.get('upgrades', {}).get('urgent', False) or
            project.get('upgrades', {}).get('nonpublic', False)
        )
        
        cursor.execute('''
            INSERT INTO projects (
                project_id, title, description, budget_min, budget_max,
                currency, bid_count, skills, matched_skills, skill_match_score,
                search_keyword, is_elite, time_submitted, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            project['id'],
            project.get('title', ''),
            project.get('description', '')[:1000],  # Limit description length
            project.get('budget', {}).get('minimum', 0),
            project.get('budget', {}).get('maximum', 0),
            project.get('currency', {}).get('code', 'USD'),
            project.get('bid_stats', {}).get('bid_count', 0),
            skills,
            ', '.join(matched_skills),
            skill_match_score,
            search_keyword,
            is_elite,
            datetime.fromtimestamp(project.get('time_submitted', 0)),
            json.dumps(project)
        ))
        
        self.db.commit()
    
    def realtime_monitor_with_bidding(self):
        """Enhanced real-time monitor that bids on ALL matching projects"""
        print("\n🚀 Starting Real-Time Monitor - NO FILTERS MODE")
        print("=" * 60)
        print(f"✓ Tracking {len(self.all_skills)} skills")
        print(f"✓ Accepting ALL budgets (including $0)")
        print(f"✓ Accepting projects from ALL countries")
        print(f"✓ Bidding regardless of existing bid count")
        print(f"✓ Check interval: 15 seconds")
        print("=" * 60)
        print("\nSearching for ALL projects... Press Ctrl+C to stop\n")
        
        seen_projects = set()
        stats = {
            'checks': 0,
            'new_projects': 0,
            'bids_attempted': 0,
            'bids_successful': 0,
            'start_time': datetime.now()
        }
        
        # Load recently seen projects from database
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT project_id FROM projects 
            WHERE created_at > datetime('now', '-1 days')
        """)
        for row in cursor.fetchall():
            seen_projects.add(row['project_id'])
        
        print(f"Loaded {len(seen_projects)} recent projects from database\n")
        
        try:
            while True:
                stats['checks'] += 1
                
                # Status line
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Checks: {stats['checks']} | "
                      f"New: {stats['new_projects']} | "
                      f"Bids: {stats['bids_successful']}/{stats['bids_attempted']} | "
                      f"API: {len(self.rate_limit_tracker['requests'])}/600", 
                      end='', flush=True)
                
                # Fetch latest projects - NO FILTERS
                projects = self.fetch_latest_projects(limit=100)
                
                # Process each project
                new_in_batch = 0
                for project in projects:
                    if project['id'] not in seen_projects:
                        seen_projects.add(project['id'])
                        stats['new_projects'] += 1
                        new_in_batch += 1
                        
                        # Save project to database
                        self.save_project(project, "monitor")
                        
                        # Get project details
                        time_submitted = datetime.fromtimestamp(project.get('time_submitted', 0))
                        project_age = datetime.now() - time_submitted
                        
                        # Display new project
                        print(f"\n\n🆕 NEW PROJECT FOUND!")
                        print(f"📋 Title: {project.get('title', '')[:70]}...")
                        
                        budget_min = project.get('budget', {}).get('minimum', 0)
                        budget_max = project.get('budget', {}).get('maximum', 0)
                        if budget_min == 0 and budget_max == 0:
                            budget_str = "Open Budget"
                        else:
                            budget_str = f"${budget_min} - ${budget_max}"
                        
                        print(f"💵 Budget: {budget_str} {project.get('currency', {}).get('code', 'USD')}")
                        print(f"⏰ Posted: {project_age.total_seconds()/60:.1f} minutes ago")
                        print(f"👥 Current Bids: {project.get('bid_stats', {}).get('bid_count', 0)}")
                        print(f"🎯 Skill Match: {project.get('skill_match_score', 0)}/100")
                        
                        if project.get('matched_skills'):
                            print(f"✅ Matched Skills: {', '.join(project['matched_skills'][:5])}")
                        
                        # Check if we should bid
                        should_bid, reason = self.should_bid_immediately(project)
                        
                        if should_bid:
                            print(f"🟢 {reason}")
                            stats['bids_attempted'] += 1
                            
                            # Place bid immediately!
                            if self.place_bid_immediately(project):
                                stats['bids_successful'] += 1
                            
                            # Small delay after bidding
                            time.sleep(1)
                        else:
                            print(f"🔴 Skipping: {reason}")
                        
                        print()  # Empty line for readability
                
                if new_in_batch > 0:
                    print(f"\n📊 Found {new_in_batch} new projects in this batch")
                
                # Manage memory - keep only recent project IDs
                if len(seen_projects) > 20000:
                    # Keep only the most recent 10000
                    seen_projects = set(list(seen_projects)[-10000:])
                
                # Wait before next check - shorter interval for more aggressive bidding
                time.sleep(15)
                
        except KeyboardInterrupt:
            # Show final statistics
            runtime = datetime.now() - stats['start_time']
            
            print(f"\n\n{'='*50}")
            print("📊 Monitoring Session Summary")
            print(f"{'='*50}")
            print(f"Total runtime: {runtime}")
            print(f"Total checks: {stats['checks']}")
            print(f"New projects found: {stats['new_projects']}")
            print(f"Bids attempted: {stats['bids_attempted']}")
            print(f"Bids successful: {stats['bids_successful']}")
            
            if stats['bids_attempted'] > 0:
                success_rate = (stats['bids_successful'] / stats['bids_attempted']) * 100
                print(f"Bid success rate: {success_rate:.1f}%")
            
            if stats['checks'] > 0:
                projects_per_check = stats['new_projects'] / stats['checks']
                print(f"Avg new projects per check: {projects_per_check:.2f}")
            
            print(f"\n✅ Monitor stopped successfully")
    
    def show_statistics(self):
        """Show comprehensive statistics"""
        cursor = self.db.cursor()
        
        print("\n" + "="*60)
        print("📊 AutoWork Statistics Dashboard - NO FILTERS MODE")
        print("="*60)
        
        # Overall stats
        cursor.execute("SELECT COUNT(*) as count FROM projects")
        total_projects = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM bids")
        total_bids = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM bids WHERE status = 'success'")
        successful_bids = cursor.fetchone()['count']
        
        print(f"\n📈 Overall Performance:")
        print(f"   Total projects tracked: {total_projects}")
        print(f"   Total bids placed: {total_bids}")
        print(f"   Successful bids: {successful_bids}")
        
        if total_bids > 0:
            success_rate = (successful_bids / total_bids) * 100
            print(f"   Success rate: {success_rate:.1f}%")
        
        # Last 24 hours
        print(f"\n⏰ Last 24 Hours:")
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM projects 
            WHERE created_at > datetime('now', '-1 day')
        """)
        recent_projects = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM bids 
            WHERE created_at > datetime('now', '-1 day')
        """)
        recent_bids = cursor.fetchone()['count']
        
        print(f"   Projects found: {recent_projects}")
        print(f"   Bids placed: {recent_bids}")
        
        # Budget range statistics
        print(f"\n💰 Budget Distribution of Bids:")
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN amount = 0 THEN '$0'
                    WHEN amount < 50 THEN '<$50'
                    WHEN amount < 100 THEN '$50-100'
                    WHEN amount < 500 THEN '$100-500'
                    WHEN amount < 1000 THEN '$500-1000'
                    ELSE '>$1000'
                END as range,
                COUNT(*) as count
            FROM bids
            GROUP BY range
            ORDER BY count DESC
        """)
        
        for row in cursor.fetchall():
            print(f"   {row['range']}: {row['count']} bids")
        
        # Top matched skills
        print(f"\n🎯 Top Matched Skills:")
        cursor.execute("""
            SELECT matched_skills, COUNT(*) as count 
            FROM projects 
            WHERE matched_skills != '' AND matched_skills IS NOT NULL
            GROUP BY matched_skills 
            ORDER BY count DESC 
            LIMIT 5
        """)
        
        for i, row in enumerate(cursor.fetchall(), 1):
            skills = row['matched_skills'][:50] + "..." if len(row['matched_skills']) > 50 else row['matched_skills']
            print(f"   {i}. {skills} ({row['count']} projects)")
        
        # Recent successful bids
        print(f"\n✅ Recent Successful Bids:")
        cursor.execute("""
            SELECT b.created_at, b.amount, p.title
            FROM bids b
            JOIN projects p ON b.project_id = p.project_id
            WHERE b.status = 'success'
            ORDER BY b.created_at DESC
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        if results:
            for row in results:
                date = datetime.fromisoformat(row['created_at']).strftime('%Y-%m-%d %H:%M')
                title = row['title'][:40] + "..." if len(row['title']) > 40 else row['title']
                print(f"   {date} - ${row['amount']:.0f} - {title}")
        else:
            print("   No successful bids yet")
        
        # API usage
        requests_last_hour = len(self.rate_limit_tracker["requests"])
        print(f"\n🔌 API Usage:")
        print(f"   Requests in last hour: {requests_last_hour}/600")
        print(f"   Remaining: {600 - requests_last_hour}")
    
    def configure_settings(self):
        """Simplified configuration for no-filters mode"""
        print("\n⚙️  AutoWork Configuration - NO FILTERS MODE")
        print("="*40)
        
        print(f"\nCurrent Settings:")
        print(f"✓ Accepting ALL budgets (including $0)")
        print(f"✓ Accepting ALL countries")
        print(f"✓ Bidding on ALL projects regardless of bid count")
        print(f"✓ Auto-bid enabled: {'Yes' if self.auto_bid_enabled else 'No'}")
        
        choice = input("\nToggle auto-bid on/off? (y/n): ").strip().lower()
        
        if choice == 'y':
            self.auto_bid_enabled = not self.auto_bid_enabled
            print(f"\n✓ Auto-bid {'enabled' if self.auto_bid_enabled else 'disabled'}")
            
            if not self.auto_bid_enabled:
                print("⚠️  Warning: Auto-bid is disabled. The monitor will only track projects without bidding.")
    
    def manual_project_search(self):
        """Manual search for specific skills or keywords"""
        print("\n🔍 Manual Project Search - NO FILTERS")
        print("Enter a skill/keyword to search (or 'list' to see all skills):")
        
        query = input("> ").strip()
        
        if query.lower() == 'list':
            print("\n📚 All Tracked Skills:")
            for category, skills in self.skill_categories.items():
                print(f"\n{category.replace('_', ' ').title()}:")
                print(f"  {', '.join(skills)}")
            return
        
        if not query:
            return
        
        print(f"\nSearching for ALL '{query}' projects (no filters)...")
        
        params = {
            'query': query,
            'limit': 20,
            'offset': 0,
            'job_details': 'true',
            'compact': 'true',
            'sort_field': 'time_submitted'
        }
        
        query_string = urllib.parse.urlencode(params, doseq=True)
        endpoint = f"/projects/0.1/projects/active/?{query_string}"
        
        response = self.api_request(endpoint)
        
        if response and 'result' in response:
            projects = response['result'].get('projects', [])
            
            if projects:
                print(f"\nFound {len(projects)} projects:\n")
                
                for i, project in enumerate(projects[:20], 1):
                    matched_skills = self.get_matching_skills(project)
                    budget_min = project['budget']['minimum']
                    budget_max = project['budget']['maximum']
                    
                    print(f"{i}. {project['title'][:60]}...")
                    
                    if budget_min == 0 and budget_max == 0:
                        print(f"   Budget: Open/Undefined")
                    else:
                        print(f"   Budget: ${budget_min}-${budget_max}")
                    
                    print(f"   Bids: {project['bid_stats']['bid_count']}")
                    print(f"   Posted: {datetime.fromtimestamp(project['time_submitted']).strftime('%Y-%m-%d %H:%M')}")
                    print(f"   Country: {project.get('location', {}).get('country', {}).get('name', 'Not specified')}")
                    
                    if matched_skills:
                        print(f"   Matched skills: {', '.join(matched_skills[:5])}")
                    
                    # Ask if user wants to bid
                    if self.auto_bid_enabled:
                        bid_now = input(f"   Bid on this project? (y/n): ").strip().lower()
                        if bid_now == 'y':
                            project['matched_skills'] = matched_skills
                            project['skill_match_score'] = self.calculate_skill_match_score(project)
                            self.save_project(project, "manual_search")
                            self.place_bid_immediately(project)
                    
                    print()
            else:
                print("No projects found for this search.")
        else:
            print("Search failed. Please try again.")
    
    def menu(self):
        """Main menu system"""
        while True:
            print("\n" + "="*50)
            print("🤖 AutoWork - NO FILTERS Bidding Bot")
            print("="*50)
            print("1. 🚀 Start Real-Time Monitor (Bid on ALL)")
            print("2. 📊 Show Statistics")
            print("3. ⚙️  Configure Settings")
            print("4. 🔍 Manual Project Search")
            print("5. 📚 List All Skills")
            print("6. 🚪 Exit")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == '1':
                if self.auto_bid_enabled:
                    self.realtime_monitor_with_bidding()
                else:
                    print("\n⚠️  Auto-bid is disabled. Enable it in settings first.")
            
            elif choice == '2':
                self.show_statistics()
            
            elif choice == '3':
                self.configure_settings()
            
            elif choice == '4':
                self.manual_project_search()
            
            elif choice == '5':
                print(f"\n📚 Tracking {len(self.all_skills)} skills across {len(self.skill_categories)} categories")
                print("\nCategories:")
                for i, (category, skills) in enumerate(self.skill_categories.items(), 1):
                    print(f"{i}. {category.replace('_', ' ').title()} ({len(skills)} skills)")
                
                show_all = input("\nShow all skills in detail? (y/n): ").lower() == 'y'
                
                if show_all:
                    for category, skills in self.skill_categories.items():
                        print(f"\n{category.replace('_', ' ').title()}:")
                        for skill in skills:
                            print(f"  • {skill}")
            
            elif choice == '6':
                print("\n👋 Thank you for using AutoWork!")
                print("Happy freelancing! 🎯")
                break
            
            else:
                print("\n❌ Invalid option. Please try again.")

# Main execution
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 AutoWork - NO FILTERS VERSION")
    print("="*60)
    print("This version bids on ALL projects that match your skills!")
    print("No budget limits, no country restrictions, no bid count limits")
    print("="*60)
    
    try:
        # Create and run the application
        app = AutoWorkMinimal()
        app.menu()
    except KeyboardInterrupt:
        print("\n\n⚠️  Program interrupted by user")
    except Exception as e:
        print(f"\n❌ Critical Error: {e}")
        print("\nPlease check:")
        print("1. Your OAuth token is valid")
        print("2. You have internet connection")
        print("3. Freelancer API is accessible")
        
        # Log the error
        import traceback
        with open('error_log.txt', 'a') as f:
            f.write(f"\n{datetime.now()}: {str(e)}\n")
            f.write(traceback.format_exc())
        
        print("\nError details saved to error_log.txt")