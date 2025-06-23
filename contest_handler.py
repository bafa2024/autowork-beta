#!/usr/bin/env python3
"""
Contest Handler for Freelancer Contests
Monitors and participates in contests
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class ContestHandler:
    def __init__(self, token: str, user_id: str):
        self.token = token
        self.user_id = user_id
        self.api_base = "https://www.freelancer.com/api"
        self.headers = {
            "Freelancer-OAuth-V1": self.token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Contest tracking
        self.processed_contests = set()
        self.entered_contests = set()
        self.contest_entries = {}  # contest_id: entry_id
        
        # Contest statistics
        self.contest_stats = {
            'total_checked': 0,
            'total_entered': 0,
            'total_wins': 0,
            'total_prize_money': 0
        }
        
        # Load state
        self.load_contest_state()
        
        logging.info("✓ Contest handler initialized")
    
    def load_contest_state(self):
        """Load saved contest state"""
        try:
            if os.path.exists('contest_state.json'):
                with open('contest_state.json', 'r') as f:
                    state = json.load(f)
                    self.processed_contests = set(state.get('processed', []))
                    self.entered_contests = set(state.get('entered', []))
                    self.contest_entries = state.get('entries', {})
                    self.contest_stats = state.get('stats', self.contest_stats)
                logging.info(f"Loaded contest state: {len(self.entered_contests)} contests entered")
        except Exception as e:
            logging.error(f"Error loading contest state: {e}")
    
    def save_contest_state(self):
        """Save contest state"""
        try:
            state = {
                'processed': list(self.processed_contests)[-1000:],  # Keep last 1000
                'entered': list(self.entered_contests),
                'entries': self.contest_entries,
                'stats': self.contest_stats,
                'last_update': datetime.now().isoformat()
            }
            with open('contest_state.json', 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving contest state: {e}")
    
    def get_active_contests(self, limit: int = 50) -> List[Dict]:
        """Fetch active contests"""
        try:
            endpoint = f"{self.api_base}/contests/0.1/contests"
            params = {
                "limit": limit,
                "status": "active",  # Only active contests
                "full_description": "true",
                "job_details": "true",
                "upgrade_details": "true"
            }
            
            response = requests.get(
                endpoint,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                contests = data.get('result', {}).get('contests', [])
                logging.info(f"✓ Fetched {len(contests)} active contests")
                return contests
            else:
                logging.error(f"Failed to fetch contests: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Error fetching contests: {e}")
            return []
    
    def get_contest_details(self, contest_id: int) -> Optional[Dict]:
        """Get detailed information about a specific contest"""
        try:
            endpoint = f"{self.api_base}/contests/0.1/contests/{contest_id}"
            
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('result', {})
            else:
                logging.error(f"Failed to get contest details: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error getting contest details: {e}")
            return None
    
    def should_enter_contest(self, contest: Dict, config: Dict) -> Tuple[bool, str]:
        """Determine if should enter a contest"""
        contest_id = contest.get('id')
        
        # Skip if already processed
        if contest_id in self.processed_contests:
            return False, "Already processed"
        
        # Skip if already entered
        if contest_id in self.entered_contests:
            return False, "Already entered"
        
        # Check prize amount
        prize = contest.get('prize', 0)
        min_prize = config.get('contests', {}).get('min_prize', 100)
        
        if prize < min_prize:
            return False, f"Prize too low (${prize} < ${min_prize})"
        
        # Check contest type
        contest_type = contest.get('type', {}).get('name', '')
        allowed_types = config.get('contests', {}).get('allowed_types', [])
        
        if allowed_types and contest_type not in allowed_types:
            return False, f"Contest type not allowed: {contest_type}"
        
        # Check skills match
        skills = [job.get('name', '') for job in contest.get('jobs', [])]
        our_skills = config.get('contests', {}).get('skills', [])
        
        if our_skills:
            matching_skills = set(skills) & set(our_skills)
            if not matching_skills:
                return False, "No matching skills"
        
        # Check time remaining
        end_date = contest.get('end_date')
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                time_remaining = end_datetime - datetime.now(end_datetime.tzinfo)
                
                min_hours = config.get('contests', {}).get('min_hours_remaining', 24)
                if time_remaining < timedelta(hours=min_hours):
                    return False, f"Not enough time remaining ({time_remaining.total_seconds() / 3600:.1f} hours)"
            except:
                pass
        
        # Check entry count
        entry_count = contest.get('entry_count', 0)
        max_entries = config.get('contests', {}).get('max_existing_entries', 100)
        
        if entry_count > max_entries:
            return False, f"Too many entries ({entry_count} > {max_entries})"
        
        return True, "Good contest opportunity"
    
    def create_contest_entry(self, contest: Dict, config: Dict) -> Optional[Dict]:
        """Create an entry for the contest based on type"""
        contest_type = contest.get('type', {}).get('name', '').lower()
        
        # Get entry templates based on contest type
        templates = config.get('contests', {}).get('entry_templates', {})
        
        entry_data = {
            'description': self._generate_entry_description(contest, templates),
            'rating': 5  # Default rating
        }
        
        # For design contests, we'd need to upload files
        # For name contests, we submit text entries
        # For code contests, we might submit code snippets
        
        if 'design' in contest_type or 'logo' in contest_type:
            # Design contests need file uploads
            logging.info("Design contest detected - would need to upload design files")
            entry_data['files'] = []  # Would need actual file upload logic
        
        elif 'naming' in contest_type or 'slogan' in contest_type:
            # Text-based contests
            suggestions = self._generate_name_suggestions(contest)
            entry_data['suggestions'] = suggestions[:5]  # Submit up to 5 names
        
        elif 'article' in contest_type or 'writing' in contest_type:
            # Writing contests
            entry_data['content'] = templates.get('writing', {}).get('sample', '')
        
        return entry_data
    
    def _generate_entry_description(self, contest: Dict, templates: Dict) -> str:
        """Generate entry description based on contest"""
        contest_type = contest.get('type', {}).get('name', '').lower()
        title = contest.get('title', 'your contest')
        
        # Use templates if available
        if 'design' in contest_type:
            template = templates.get('design', {}).get('description', '')
        elif 'naming' in contest_type:
            template = templates.get('naming', {}).get('description', '')
        else:
            template = templates.get('default', {}).get('description', '')
        
        if not template:
            template = """Hi! I'm excited to participate in {title}.
            
I have carefully reviewed your requirements and created this entry based on your brief.
I'm available for any revisions or modifications you might need.

Looking forward to your feedback!"""
        
        return template.format(title=title[:50])
    
    def _generate_name_suggestions(self, contest: Dict) -> List[str]:
        """Generate name suggestions for naming contests"""
        # This is a simple example - you'd want more sophisticated generation
        description = contest.get('description', '').lower()
        
        suggestions = []
        
        # Extract keywords from description
        keywords = []
        for word in ['tech', 'smart', 'pro', 'max', 'plus', 'hub', 'zone', 'lab']:
            if word in description:
                keywords.append(word.capitalize())
        
        # Generate some combinations
        base_words = ['Nova', 'Apex', 'Prime', 'Elite', 'Fusion']
        
        for base in base_words[:3]:
            if keywords:
                suggestions.append(f"{base}{keywords[0]}")
            else:
                suggestions.append(base)
        
        return suggestions[:5]
    
    def submit_contest_entry(self, contest_id: int, entry_data: Dict) -> bool:
        """Submit an entry to a contest"""
        try:
            endpoint = f"{self.api_base}/contests/0.1/contests/{contest_id}/entries"
            
            # Prepare the entry submission
            submission_data = {
                'contest_id': contest_id,
                'freelancer_id': int(self.user_id),
                'description': entry_data.get('description', ''),
                'rating': entry_data.get('rating', 5)
            }
            
            # Add type-specific data
            if 'suggestions' in entry_data:
                # For naming contests
                submission_data['entries'] = [
                    {'name': name} for name in entry_data['suggestions']
                ]
            elif 'content' in entry_data:
                # For writing contests
                submission_data['content'] = entry_data['content']
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=submission_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                entry_id = result.get('result', {}).get('id')
                
                # Track the entry
                self.entered_contests.add(contest_id)
                if entry_id:
                    self.contest_entries[str(contest_id)] = entry_id
                
                # Update stats
                self.contest_stats['total_entered'] += 1
                
                logging.info(f"✅ Successfully entered contest {contest_id}")
                return True
            else:
                logging.error(f"Failed to enter contest: {response.status_code}")
                if response.text:
                    logging.error(f"Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            logging.error(f"Error submitting contest entry: {e}")
            return False
    
    def check_contest_results(self):
        """Check results of entered contests"""
        try:
            for contest_id, entry_id in self.contest_entries.items():
                contest = self.get_contest_details(int(contest_id))
                
                if contest:
                    status = contest.get('status', '')
                    
                    if status == 'closed' or status == 'complete':
                        # Check if we won
                        winner_id = contest.get('winner_id')
                        if winner_id == int(self.user_id):
                            prize = contest.get('prize', 0)
                            self.contest_stats['total_wins'] += 1
                            self.contest_stats['total_prize_money'] += prize
                            logging.info(f"🏆 WON CONTEST {contest_id}! Prize: ${prize}")
                
        except Exception as e:
            logging.error(f"Error checking contest results: {e}")
    
    def get_contest_summary(self) -> Dict:
        """Get contest participation summary"""
        return {
            'total_checked': self.contest_stats['total_checked'],
            'total_entered': self.contest_stats['total_entered'],
            'total_wins': self.contest_stats['total_wins'],
            'total_prize_money': self.contest_stats['total_prize_money'],
            'win_rate': (self.contest_stats['total_wins'] / self.contest_stats['total_entered'] * 100) 
                       if self.contest_stats['total_entered'] > 0 else 0
        }