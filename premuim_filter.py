#!/usr/bin/env python3
"""
Premium Project Filter for High-Quality Projects
Identifies and prioritizes premium projects worth bidding on
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class PremiumProjectFilter:
    def __init__(self, config: Dict):
        self.config = config
        self.quality_config = config.get('quality_filters', {})
        self.premium_categories = config.get('premium_categories', {})
        
        # Quality indicators
        self.quality_indicators = {
            'description_quality': {
                'min_words': 50,
                'has_requirements': ['requirements', 'need', 'looking for', 'must have'],
                'has_timeline': ['deadline', 'timeline', 'duration', 'timeframe'],
                'has_budget_justification': ['budget', 'pay', 'compensation', 'rate'],
                'professional_tone': ['please', 'thank you', 'experience', 'portfolio']
            },
            'project_complexity': {
                'complex_keywords': [
                    'architecture', 'scalable', 'microservices', 'distributed',
                    'real-time', 'high performance', 'optimization', 'integration',
                    'custom solution', 'from scratch', 'redesign', 'migration',
                    'api development', 'full stack', 'end to end', 'enterprise'
                ],
                'tech_stack_mentions': 2,  # Minimum tech mentions
                'feature_count': 3  # Minimum features mentioned
            },
            'employer_quality': {
                'min_rating': 4.0,
                'min_reviews': 5,
                'min_completion_rate': 0.85,
                'verified_payment': True,
                'returning_client': True
            }
        }
        
        # Premium bid message templates
        self.premium_templates = {
            'consultant': """Dear {client_name},

I've carefully reviewed your requirements for {project_title}. With my {experience_years}+ years of expertise in {primary_skill}, I can deliver a robust, scalable solution that exceeds your expectations.

My approach:
• Initial consultation to understand your complete vision
• Detailed project architecture and timeline proposal
• {approach_point_1}
• {approach_point_2}
• Ongoing support and optimization post-delivery

Recent similar project: {recent_project}

I'm available for a call to discuss your specific needs and how I can add value to your project.

Best regards,
{your_name}""",

            'technical_expert': """Hello {client_name},

Your {project_type} project aligns perfectly with my expertise. I specialize in {specialization} and have delivered {project_count}+ similar solutions.

Technical approach for your project:
• {tech_point_1}
• {tech_point_2}
• {tech_point_3}

I ensure:
✓ Clean, documented, test-driven code
✓ {delivery_time} delivery with regular updates
✓ Post-deployment support and knowledge transfer

Portfolio: {portfolio_link}
GitHub: {github_link}

Let's discuss how I can bring your vision to life.

Regards,
{your_name}""",

            'solution_architect': """Dear {client_name},

I'm excited about your {project_type} project. As a {role} with expertise in {tech_stack}, I can architect a solution that's both powerful and maintainable.

Value I bring:
• Strategic technical planning saving 30-40% development time
• {value_prop_1}
• {value_prop_2}
• Future-proof architecture supporting your growth

My process includes detailed documentation, code reviews, and knowledge transfer sessions.

Available for immediate discussion about your requirements.

Best regards,
{your_name}"""
        }

    def calculate_project_quality_score(self, project: Dict) -> Tuple[int, Dict]:
        """Calculate quality score for a project (0-100)"""
        score = 0
        factors = {
            'description_quality': 0,
            'budget_quality': 0,
            'employer_quality': 0,
            'project_complexity': 0,
            'category_match': 0,
            'elite_status': 0
        }
        
        # 1. Description Quality (25 points)
        desc_score = self._evaluate_description(project)
        factors['description_quality'] = desc_score
        score += desc_score
        
        # 2. Budget Quality (25 points)
        budget_score = self._evaluate_budget(project)
        factors['budget_quality'] = budget_score
        score += budget_score
        
        # 3. Employer Quality (20 points)
        employer_score = self._evaluate_employer(project)
        factors['employer_quality'] = employer_score
        score += employer_score
        
        # 4. Project Complexity (15 points)
        complexity_score = self._evaluate_complexity(project)
        factors['project_complexity'] = complexity_score
        score += complexity_score
        
        # 5. Category Match (10 points)
        category_score = self._evaluate_category_match(project)
        factors['category_match'] = category_score
        score += category_score
        
        # 6. Elite Status (5 points)
        if self._is_elite_project(project):
            factors['elite_status'] = 5
            score += 5
        
        return score, factors

    def _evaluate_description(self, project: Dict) -> int:
        """Evaluate description quality (0-25 points)"""
        score = 0
        description = project.get('description', '')
        
        # Length check (5 points)
        word_count = len(description.split())
        if word_count >= 200:
            score += 5
        elif word_count >= 100:
            score += 3
        elif word_count >= 50:
            score += 1
        
        # Has requirements section (5 points)
        if any(req in description.lower() for req in self.quality_indicators['description_quality']['has_requirements']):
            score += 5
        
        # Has timeline info (5 points)
        if any(timeline in description.lower() for timeline in self.quality_indicators['description_quality']['has_timeline']):
            score += 5
        
        # Professional tone (5 points)
        professional_count = sum(1 for word in self.quality_indicators['description_quality']['professional_tone'] 
                               if word in description.lower())
        if professional_count >= 3:
            score += 5
        elif professional_count >= 2:
            score += 3
        
        # No spam keywords (5 points)
        avoid_keywords = self.quality_config.get('avoid_keywords', [])
        if not any(keyword in description.lower() for keyword in avoid_keywords):
            score += 5
        
        return min(score, 25)

    def _evaluate_budget(self, project: Dict) -> int:
        """Evaluate budget quality (0-25 points)"""
        score = 0
        budget = project.get('budget', {})
        
        if not isinstance(budget, dict):
            return 0
        
        min_budget = budget.get('minimum', 0)
        max_budget = budget.get('maximum', 0)
        budget_type = budget.get('type', 'fixed')
        
        # Budget range (15 points)
        preferred_min = self.quality_config.get('preferred_budget_range', {}).get('min', 500)
        preferred_max = self.quality_config.get('preferred_budget_range', {}).get('max', 5000)
        
        if preferred_min <= min_budget <= preferred_max:
            score += 15
        elif min_budget >= self.quality_config.get('min_project_budget', 250):
            score += 8
        elif min_budget >= 100:
            score += 3
        
        # Hourly rate premium (5 points)
        if budget_type == 'hourly' and min_budget >= 50:
            score += 5
        
        # Reasonable budget range (5 points)
        if max_budget > 0 and (max_budget / min_budget) <= 3:
            score += 5
        
        return min(score, 25)

    def _evaluate_employer(self, project: Dict) -> int:
        """Evaluate employer quality (0-20 points)"""
        score = 0
        owner = project.get('owner', {})
        
        if not isinstance(owner, dict):
            return 0
        
        # Rating (8 points)
        reputation = owner.get('reputation', {})
        if isinstance(reputation, dict):
            rating = reputation.get('entire_history', {}).get('overall', 0)
            if rating >= 4.8:
                score += 8
            elif rating >= 4.5:
                score += 6
            elif rating >= 4.0:
                score += 4
        
        # Payment verified (6 points)
        if owner.get('status', {}).get('payment_verified', False):
            score += 6
        
        # Previous projects (6 points)
        if isinstance(reputation, dict):
            project_count = reputation.get('entire_history', {}).get('projects', 0)
            if project_count >= 20:
                score += 6
            elif project_count >= 10:
                score += 4
            elif project_count >= 5:
                score += 2
        
        return min(score, 20)

    def _evaluate_complexity(self, project: Dict) -> int:
        """Evaluate project complexity (0-15 points)"""
        score = 0
        title = project.get('title', '').lower()
        description = project.get('description', '').lower()
        full_text = title + ' ' + description
        
        # Complex keywords (8 points)
        complex_count = sum(1 for keyword in self.quality_indicators['project_complexity']['complex_keywords'] 
                          if keyword in full_text)
        if complex_count >= 3:
            score += 8
        elif complex_count >= 2:
            score += 5
        elif complex_count >= 1:
            score += 3
        
        # Multiple technologies mentioned (7 points)
        tech_mentions = self._count_tech_mentions(project)
        if tech_mentions >= 4:
            score += 7
        elif tech_mentions >= 3:
            score += 5
        elif tech_mentions >= 2:
            score += 3
        
        return min(score, 15)

    def _evaluate_category_match(self, project: Dict) -> int:
        """Evaluate category match (0-10 points)"""
        score = 0
        title = project.get('title', '').lower()
        description = project.get('description', '').lower()
        full_text = title + ' ' + description
        
        best_match_score = 0
        for category, config in self.premium_categories.items():
            keywords = config.get('keywords', [])
            matches = sum(1 for keyword in keywords if keyword.lower() in full_text)
            
            if matches > 0:
                category_score = min(matches * 2, 10)
                best_match_score = max(best_match_score, category_score)
        
        return best_match_score

    def _count_tech_mentions(self, project: Dict) -> int:
        """Count technology mentions in project"""
        tech_keywords = [
            'react', 'vue', 'angular', 'node', 'python', 'django', 'flask',
            'laravel', 'php', 'java', 'spring', 'kotlin', 'swift', 'flutter',
            'aws', 'azure', 'docker', 'kubernetes', 'mongodb', 'postgresql',
            'redis', 'elasticsearch', 'graphql', 'rest api', 'microservices'
        ]
        
        text = f"{project.get('title', '')} {project.get('description', '')}".lower()
        return sum(1 for tech in tech_keywords if tech in text)

    def _is_elite_project(self, project: Dict) -> bool:
        """Check if project has elite status"""
        upgrades = project.get('upgrades', {})
        if not isinstance(upgrades, dict):
            return False
        
        return any([
            upgrades.get('featured', False),
            upgrades.get('sealed', False),
            upgrades.get('NDA', False),
            upgrades.get('ip_contract', False),
            upgrades.get('qualified', False)
        ])

    def is_premium_project(self, project: Dict, min_score: int = 60) -> Tuple[bool, int, Dict]:
        """
        Determine if project qualifies as premium
        Returns: (is_premium, score, factors)
        """
        score, factors = self.calculate_project_quality_score(project)
        is_premium = score >= min_score
        
        return is_premium, score, factors

    def get_premium_bid_template(self, project: Dict, user_info: Dict) -> str:
        """Get appropriate premium bid template for project"""
        # Determine project type
        title = project.get('title', '').lower()
        description = project.get('description', '').lower()
        
        # Choose template based on project
        if any(word in title + description for word in ['architect', 'design', 'scalable', 'enterprise']):
            template_key = 'solution_architect'
        elif any(word in title + description for word in ['expert', 'senior', 'complex', 'advanced']):
            template_key = 'technical_expert'
        else:
            template_key = 'consultant'
        
        template = self.premium_templates[template_key]
        
        # Customize template with project info
        # This is a simplified version - you'd want to make this more sophisticated
        return template.format(
            client_name="Client",
            project_title=project.get('title', 'your project')[:50],
            experience_years="5",
            primary_skill=self._get_primary_skill(project),
            approach_point_1="Comprehensive requirement analysis",
            approach_point_2="Iterative development with regular demos",
            recent_project="[Similar project example]",
            your_name="[Your name]",
            project_type=self._get_project_type(project),
            specialization=self._get_primary_skill(project),
            project_count="50",
            tech_point_1="Modern architecture patterns",
            tech_point_2="Comprehensive testing strategy",
            tech_point_3="Performance optimization",
            delivery_time="Timely",
            portfolio_link="[Portfolio URL]",
            github_link="[GitHub URL]",
            role="Senior Developer",
            tech_stack=self._get_primary_skill(project),
            value_prop_1="Best practices implementation",
            value_prop_2="Scalable solution design"
        )

    def _get_primary_skill(self, project: Dict) -> str:
        """Extract primary skill from project"""
        jobs = project.get('jobs', [])
        if jobs and isinstance(jobs[0], dict):
            return jobs[0].get('name', 'development')
        return 'development'

    def _get_project_type(self, project: Dict) -> str:
        """Determine project type"""
        title = project.get('title', '').lower()
        if 'web' in title:
            return 'web development'
        elif 'mobile' in title or 'app' in title:
            return 'mobile app'
        elif 'api' in title:
            return 'API development'
        else:
            return 'development'