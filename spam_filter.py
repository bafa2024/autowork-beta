#!/usr/bin/env python3
"""
Spam Filter Module for AutoWork Bot
Detects and filters out spammy/scam projects on Freelancer
"""

import re
import logging
from typing import Dict, List, Tuple, Optional

class SpamFilter:
    def __init__(self):
        # Spam keywords and patterns
        self.spam_keywords = [
            # Get-rich-quick schemes
            "make money fast", "earn.*per day", "passive income guaranteed",
            "financial freedom", "be your own boss today", "millionaire secrets",
            "guaranteed profit", "risk free investment", "double your money",
            
            # Adult/Dating/Escort
            "adult", "escort", "dating site", "cam girl", "cam model", "only fans",
            "onlyfans", "adult content", "xxx", "porn", "sex chat", "hot girls",
            
            # Cryptocurrency scams
            "crypto trading bot", "bitcoin investment", "forex signals",
            "pump and dump", "guaranteed returns", "crypto expert",
            
            # MLM/Pyramid schemes
            "mlm", "network marketing", "pyramid", "referral program",
            "recruit others", "downline", "multi level",
            
            # Academic fraud
            "write my essay", "do my homework", "take my exam", "ghost writer",
            "academic writing", "assignment help", "dissertation for me",
            
            # Gambling/Casino
            "casino", "gambling", "betting site", "poker bot", "slot machine",
            "sports betting", "odds prediction",
            
            # Illegal activities
            "hack", "crack", "bypass security", "ddos", "phishing",
            "fake documents", "fake id", "counterfeit", "illegal",
            
            # Review manipulation
            "fake review", "buy reviews", "5 star reviews", "app store reviews",
            "google reviews", "yelp reviews", "amazon reviews",
            
            # Click fraud
            "click my ads", "watch ads", "click bot", "traffic bot",
            "fake traffic", "bot traffic", "click farm",
            
            # Social media manipulation
            "buy followers", "instagram followers", "fake followers",
            "youtube views", "tiktok likes", "social media bot",
            
            # Survey/Data collection scams
            "survey", "data entry captcha", "form filling", "copy paste job",
            "simple typing", "earn by typing", "home based typing"
        ]
        
        # Suspicious patterns
        self.suspicious_patterns = [
            r'\$\d+\s*(?:per|/)\s*(?:day|hour|week)',  # $X per day/hour/week
            r'earn\s*\$?\d+\+?\s*(?:daily|hourly|weekly)',  # earn $X daily
            r'(?:WhatsApp|Telegram|Skype|Discord)\s*(?:me|contact|chat)',  # External contact
            r'contact\s*me\s*(?:at|on)\s*[^\s]+@[^\s]+',  # Email in description
            r'(?:www\.|https?://)[^\s]+',  # URLs in description
            r'\b(?:urgent|asap|immediately)\b.*\b(?:money|payment|cash)\b',  # Urgent money
            r'(?:no\s*experience|anyone\s*can\s*do|easy\s*money)',  # Too good to be true
            r'(?:work\s*from\s*home|remote\s*job).*(?:guaranteed|assured)',  # WFH scams
        ]
        
        # Compile regex patterns
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]
        
        # Budget red flags
        self.budget_red_flags = {
            'too_high_hourly': 100,  # $100+/hour for simple tasks
            'suspiciously_round': [1000, 5000, 10000],  # Round numbers
            'data_entry_max': 50,  # Max reasonable for data entry
        }
        
        # Title red flags
        self.title_red_flags = [
            "easy job", "simple task", "quick money", "urgent hiring",
            "data entry", "copy paste", "form filling", "ad clicking",
            "5 minutes work", "no experience", "hiring now"
        ]
        
        # Description length thresholds
        self.description_thresholds = {
            'too_short': 50,  # Less than 50 chars is suspicious
            'too_vague': 100,  # Less than 100 chars might be vague
        }
        
        # Initialize spam statistics
        self.stats = {
            'total_checked': 0,
            'spam_detected': 0,
            'reasons': {}
        }

    def is_spam(self, project: Dict) -> Tuple[bool, List[str]]:
        """
        Check if a project is spam
        Returns: (is_spam: bool, reasons: List[str])
        """
        self.stats['total_checked'] += 1
        reasons = []
        spam_score = 0
        
        title = project.get('title', '').lower()
        description = project.get('description', '').lower()
        budget = project.get('budget', {})
        
        # 1. Check title for spam keywords
        title_check = self._check_title(title)
        if title_check[0]:
            spam_score += title_check[1]
            reasons.extend(title_check[2])
        
        # 2. Check description for spam content
        desc_check = self._check_description(description)
        if desc_check[0]:
            spam_score += desc_check[1]
            reasons.extend(desc_check[2])
        
        # 3. Check budget anomalies
        budget_check = self._check_budget(budget, title, description)
        if budget_check[0]:
            spam_score += budget_check[1]
            reasons.extend(budget_check[2])
        
        # 4. Check project metadata
        meta_check = self._check_metadata(project)
        if meta_check[0]:
            spam_score += meta_check[1]
            reasons.extend(meta_check[2])
        
        # 5. Check for external contact requests
        contact_check = self._check_external_contact(title + ' ' + description)
        if contact_check[0]:
            spam_score += contact_check[1]
            reasons.extend(contact_check[2])
        
        # Determine if spam based on score
        is_spam = spam_score >= 50  # Threshold of 50 points
        
        if is_spam:
            self.stats['spam_detected'] += 1
            for reason in reasons:
                if reason not in self.stats['reasons']:
                    self.stats['reasons'][reason] = 0
                self.stats['reasons'][reason] += 1
        
        return is_spam, reasons

    def _check_title(self, title: str) -> Tuple[bool, int, List[str]]:
        """Check title for spam indicators"""
        score = 0
        reasons = []
        
        # Check for spam keywords in title
        for keyword in self.title_red_flags:
            if keyword in title:
                score += 20
                reasons.append(f"Suspicious title: '{keyword}'")
        
        # Check for ALL CAPS
        if title.isupper() and len(title) > 10:
            score += 15
            reasons.append("Title in ALL CAPS")
        
        # Check for excessive punctuation
        if title.count('!') > 2 or title.count('$') > 2:
            score += 10
            reasons.append("Excessive punctuation in title")
        
        return score > 0, score, reasons

    def _check_description(self, description: str) -> Tuple[bool, int, List[str]]:
        """Check description for spam content"""
        score = 0
        reasons = []
        
        # Check length
        desc_length = len(description)
        if desc_length < self.description_thresholds['too_short']:
            score += 30
            reasons.append(f"Description too short ({desc_length} chars)")
        elif desc_length < self.description_thresholds['too_vague']:
            score += 15
            reasons.append(f"Description too vague ({desc_length} chars)")
        
        # Check for spam keywords
        for keyword in self.spam_keywords:
            if keyword in description:
                score += 25
                reasons.append(f"Spam keyword: '{keyword}'")
                break  # One is enough
        
        # Check suspicious patterns
        for pattern in self.compiled_patterns:
            if pattern.search(description):
                score += 20
                reasons.append(f"Suspicious pattern detected")
                break
        
        # Check for repeated characters/words
        if self._has_excessive_repetition(description):
            score += 15
            reasons.append("Excessive repetition in description")
        
        return score > 0, score, reasons

    def _check_budget(self, budget: Dict, title: str, description: str) -> Tuple[bool, int, List[str]]:
        """Check budget for anomalies"""
        score = 0
        reasons = []
        
        min_budget = budget.get('minimum', 0)
        max_budget = budget.get('maximum', 0)
        
        # Check for data entry/simple task with high budget
        is_simple_task = any(keyword in title + description for keyword in 
                           ['data entry', 'copy paste', 'typing', 'form filling', 'simple task'])
        
        if is_simple_task and min_budget > self.budget_red_flags['data_entry_max']:
            score += 30
            reasons.append(f"Suspiciously high budget for simple task (${min_budget})")
        
        # Check for suspiciously round numbers
        if min_budget in self.budget_red_flags['suspiciously_round']:
            score += 10
            reasons.append(f"Suspiciously round budget (${min_budget})")
        
        # Check for hourly rate anomalies
        if budget.get('type') == 'hourly':
            hourly_rate = min_budget
            if hourly_rate > self.budget_red_flags['too_high_hourly'] and is_simple_task:
                score += 25
                reasons.append(f"Unrealistic hourly rate (${hourly_rate}/hr)")
        
        return score > 0, score, reasons

    def _check_metadata(self, project: Dict) -> Tuple[bool, int, List[str]]:
        """Check project metadata for red flags"""
        score = 0
        reasons = []
        
        # Check if employer is new with urgent project
        owner = project.get('owner', {})
        if isinstance(owner, dict):
            employer_reputation = owner.get('reputation', {})
            if isinstance(employer_reputation, dict):
                entire_history = employer_reputation.get('entire_history', {})
                if isinstance(entire_history, dict):
                    overall = entire_history.get('overall', 0)
                    reviews = entire_history.get('reviews', 0)
                    
                    if reviews == 0 and 'urgent' in project.get('title', '').lower():
                        score += 20
                        reasons.append("New employer with 'urgent' project")
        
        # Check for NDA on simple tasks
        upgrades = project.get('upgrades', {})
        if isinstance(upgrades, dict):
            has_nda = upgrades.get('NDA', False)
            is_simple = any(word in project.get('title', '').lower() 
                          for word in ['data entry', 'typing', 'copy paste'])
            
            if has_nda and is_simple:
                score += 15
                reasons.append("NDA required for simple task")
        
        # Check job category mismatches
        jobs = project.get('jobs', [])
        if isinstance(jobs, list) and jobs:
            categories = [job.get('name', '').lower() for job in jobs if isinstance(job, dict)]
            title_lower = project.get('title', '').lower()
            
            # If title mentions data entry but category is programming
            if 'data entry' in title_lower and any('programming' in cat or 'software' in cat for cat in categories):
                score += 20
                reasons.append("Category mismatch with title")
        
        return score > 0, score, reasons

    def _check_external_contact(self, text: str) -> Tuple[bool, int, List[str]]:
        """Check for attempts to move communication off-platform"""
        score = 0
        reasons = []
        
        # Check for messaging apps
        messaging_apps = ['whatsapp', 'telegram', 'skype', 'discord', 'signal', 'viber']
        for app in messaging_apps:
            if app in text.lower():
                score += 30
                reasons.append(f"Requests contact via {app.title()}")
                break
        
        # Check for email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, text):
            score += 25
            reasons.append("Contains email address")
        
        # Check for phone numbers
        phone_pattern = r'(?:\+\d{1,3}\s?)?(?:\d{10,15}|\(\d{3}\)\s?\d{3}-?\d{4})'
        if re.search(phone_pattern, text):
            score += 25
            reasons.append("Contains phone number")
        
        return score > 0, score, reasons

    def _has_excessive_repetition(self, text: str) -> bool:
        """Check for excessive character or word repetition"""
        # Check for repeated characters (e.g., "!!!!!" or "$$$$")
        if re.search(r'(.)\1{4,}', text):
            return True
        
        # Check for repeated words
        words = text.split()
        if len(words) > 10:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            # If any word appears more than 20% of the time
            max_count = max(word_counts.values())
            if max_count / len(words) > 0.2:
                return True
        
        return False

    def get_stats(self) -> Dict:
        """Get spam detection statistics"""
        return {
            'total_checked': self.stats['total_checked'],
            'spam_detected': self.stats['spam_detected'],
            'spam_rate': (self.stats['spam_detected'] / self.stats['total_checked'] * 100) 
                        if self.stats['total_checked'] > 0 else 0,
            'top_reasons': sorted(self.stats['reasons'].items(), key=lambda x: x[1], reverse=True)[:5]
        }

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_checked': 0,
            'spam_detected': 0,
            'reasons': {}
        }