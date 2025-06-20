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
        """Hi! I just reviewed your project and I'm ready to start immediately. 
        With my expertise in {skills}, I can deliver exactly what you need. 
        I've successfully completed similar projects and maintain 100% client satisfaction. 
        Let's discuss your requirements right away!""",
        
        """Hello! Your project caught my attention and I'm very interested. 
        I specialize in {skills} and can begin working on this today. 
        I'll ensure high-quality delivery within your timeline and budget. 
        Available to chat now!""",
        
        """Hi there! I'm experienced in {skills} and perfectly suited for your project. 
        I can start immediately and provide regular updates. 
        Let's connect to discuss how I can help you achieve your goals!"""
    ]

settings = Settings()