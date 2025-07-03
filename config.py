import os
from typing import List
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Freelancer API
    freelancer_oauth_token: str = os.getenv("FREELANCER_OAUTH_TOKEN", "")
    freelancer_user_id: int = int(os.getenv("FREELANCER_USER_ID", "0"))
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./autowork.db")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # API Limits
    api_rate_limit_per_second: int = 3
    api_rate_limit_per_hour: int = 600
    api_rate_limit_per_day: int = 3600
    
    # Monitoring
    check_interval_seconds: int = 30
    max_concurrent_bids: int = 5
    
    # Bidding Strategy
    min_project_budget: int = 50
    max_existing_bids: int = 20
    bid_immediately_threshold_minutes: int = 10
    
    # Target countries (Canada, India, Pakistan)
    target_countries: List[int] = [40, 113, 151]
    
    # Priority skills
    priority_skills: List[str] = [
        "PHP", "Laravel", "WordPress", "CodeIgniter",
        "JavaScript", "React", "Node.js", "Vue.js",
        "Python", "Django", "Flask",
        "MySQL", "PostgreSQL", "MongoDB"
    ]
    
    # Bid templates
    bid_templates: List[str] = [
        """Hello, I liked your project for the {project_title}, which aligns perfectly with my professional expertise. I bring extensive experience in {skills}, I can ensure timely delivery within {days} days. I'm committed to exceeding your expectations and would welcome the opportunity to discuss your requirements in detail.""",
        
        """Hello, I liked your project for the {project_title}, which aligns perfectly with my professional expertise. I bring extensive experience in {skills}, I can ensure timely delivery within {days} days. I'm committed to exceeding your expectations and would welcome the opportunity to discuss your requirements in detail.""",
        
        """Hello, I liked your project for the {project_title}, which aligns perfectly with my professional expertise. I bring extensive experience in {skills}, I can ensure timely delivery within {days} days. I'm committed to exceeding your expectations and would welcome the opportunity to discuss your requirements in detail."""
    ]

settings = Settings()