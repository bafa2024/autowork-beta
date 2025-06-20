from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from datetime import datetime
import json

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=True, index=True)
    title = Column(String(500))
    description = Column(Text)
    budget_min = Column(Float)
    budget_max = Column(Float)
    currency = Column(String(10))
    bid_count = Column(Integer, default=0)
    skills = Column(JSON)
    country = Column(String(100))
    search_keyword = Column(String(100))
    is_elite = Column(Boolean, default=False)
    time_submitted = Column(DateTime)
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class Bid(Base):
    __tablename__ = "bids"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, index=True)
    bid_id = Column(Integer, unique=True, nullable=True)
    amount = Column(Float)
    period = Column(Integer)
    description = Column(Text)
    status = Column(String(50))  # success, failed, pending
    response_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class RateLimit(Base):
    __tablename__ = "rate_limits"
    
    id = Column(Integer, primary_key=True)
    endpoint = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)

async def init_db(database_url: str):
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    return engine, async_session