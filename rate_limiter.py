import asyncio
from datetime import datetime, timedelta
from typing import Dict, Tuple
import json
import aiofiles
import os

class RateLimiter:
    def __init__(self, per_second=3, per_hour=600, per_day=3600):
        self.per_second = per_second
        self.per_hour = per_hour
        self.per_day = per_day
        self.requests = []
        self.lock = asyncio.Lock()
        self.tracking_file = "rate_limit_tracking.json"
        
    async def can_make_request(self) -> Tuple[bool, str]:
        """Check if we can make a request"""
        async with self.lock:
            now = datetime.now()
            
            # Clean old requests
            self.requests = [
                req for req in self.requests 
                if now - req < timedelta(days=1)
            ]
            
            # Count requests in different windows
            last_second = [
                req for req in self.requests 
                if now - req < timedelta(seconds=1)
            ]
            last_hour = [
                req for req in self.requests 
                if now - req < timedelta(hours=1)
            ]
            
            # Check limits
            if len(last_second) >= self.per_second:
                return False, f"Rate limit: {self.per_second} per second"
            
            if len(last_hour) >= self.per_hour:
                wait_time = 60 - (now - last_hour[0]).seconds
                return False, f"Rate limit: {self.per_hour} per hour. Wait {wait_time}s"
            
            if len(self.requests) >= self.per_day:
                wait_time = 86400 - (now - self.requests[0]).seconds
                return False, f"Rate limit: {self.per_day} per day. Wait {wait_time}s"
            
            return True, "OK"
    
    async def record_request(self):
        """Record a request"""
        async with self.lock:
            self.requests.append(datetime.now())
            await self.save_tracking()
    
    async def get_status(self) -> Dict:
        """Get current rate limit status"""
        async with self.lock:
            now = datetime.now()
            
            last_hour = [
                req for req in self.requests 
                if now - req < timedelta(hours=1)
            ]
            
            return {
                "requests_last_hour": len(last_hour),
                "requests_last_day": len(self.requests),
                "remaining_hour": self.per_hour - len(last_hour),
                "remaining_day": self.per_day - len(self.requests)
            }
    
    async def save_tracking(self):
        """Save tracking data to file"""
        data = {
            "requests": [req.isoformat() for req in self.requests]
        }
        async with aiofiles.open(self.tracking_file, 'w') as f:
            await f.write(json.dumps(data))
    
    async def load_tracking(self):
        """Load tracking data from file"""
        if os.path.exists(self.tracking_file):
            async with aiofiles.open(self.tracking_file, 'r') as f:
                data = json.loads(await f.read())
                self.requests = [
                    datetime.fromisoformat(req) 
                    for req in data.get("requests", [])
                ]