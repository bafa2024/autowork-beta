#!/usr/bin/env python3
"""
Premium Project Filter for AutoWork Bot
Filters projects based on premium criteria
"""

import logging
from typing import Dict, Tuple, List

class PremiumProjectFilter:
    def __init__(self, config: Dict):
        self.config = config
        self.premium_keywords = [
            'enterprise', 'corporate', 'business', 'professional',
            'high-quality', 'expert', 'senior', 'advanced',
            'complex', 'sophisticated', 'comprehensive'
        ]
        
        self.premium_skills = [
            'Architecture', 'System Design', 'Enterprise', 'DevOps',
            'Cloud Computing', 'Microservices', 'API Design', 'Security'
        ]
        
        logging.info("✓ Premium filter initialized")

    def is_premium_project(self, project: Dict) -> Tuple[bool, float, List[str]]:
        """Determine if a project is premium quality"""
        score = 0
        factors = []
        
        # Budget factor (30 points)
        budget = project.get('budget', {})
        if isinstance(budget, dict):
            min_budget = budget.get('minimum', 0)
            currency_code = project.get('currency', {}).get('code', 'USD')
            
            # Convert to USD equivalent for scoring
            if currency_code == 'USD':
                usd_budget = min_budget
            elif currency_code == 'EUR':
                usd_budget = min_budget * 1.1
            elif currency_code == 'GBP':
                usd_budget = min_budget * 1.3
            else:
                usd_budget = min_budget
            
            if usd_budget >= 1000:
                score += 30
                factors.append("High budget")
            elif usd_budget >= 500:
                score += 20
                factors.append("Good budget")
            elif usd_budget >= 250:
                score += 10
                factors.append("Decent budget")
        
        # Description quality (25 points)
        description = project.get('description', '')
        word_count = len(description.split())
        
        if word_count >= 300:
            score += 25
            factors.append("Detailed description")
        elif word_count >= 200:
            score += 15
            factors.append("Good description")
        elif word_count >= 100:
            score += 10
            factors.append("Adequate description")
        
        # Premium keywords (20 points)
        description_lower = description.lower()
        premium_keyword_count = sum(1 for keyword in self.premium_keywords if keyword in description_lower)
        
        if premium_keyword_count >= 3:
            score += 20
            factors.append("Premium keywords")
        elif premium_keyword_count >= 1:
            score += 10
            factors.append("Some premium keywords")
        
        # Skills match (15 points)
        project_skills = [job.get('name', '') for job in project.get('jobs', [])]
        premium_skill_matches = sum(1 for skill in project_skills if skill in self.premium_skills)
        
        if premium_skill_matches >= 2:
            score += 15
            factors.append("Premium skills")
        elif premium_skill_matches >= 1:
            score += 8
            factors.append("Some premium skills")
        
        # Client quality (10 points)
        owner = project.get('owner', {})
        if isinstance(owner, dict):
            if owner.get('status', {}).get('payment_verified', False):
                score += 10
                factors.append("Payment verified")
        
        # Determine if premium
        min_premium_score = self.config.get('premium_mode', {}).get('min_premium_score', 70)
        is_premium = score >= min_premium_score
        
        return is_premium, score, factors

    def get_premium_score_breakdown(self, project: Dict) -> Dict:
        """Get detailed breakdown of premium scoring"""
        is_premium, score, factors = self.is_premium_project(project)
        
        return {
            'is_premium': is_premium,
            'score': score,
            'factors': factors,
            'threshold': self.config.get('premium_mode', {}).get('min_premium_score', 70)
        } 