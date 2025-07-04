#!/usr/bin/env python3
"""
AutoWork Project Management System
Manages awarded projects from bidding to successful delivery
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import requests
from dataclasses import dataclass, asdict
import asyncio
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import redis
from jinja2 import Template

Base = declarative_base()

# Project Status Enum
class ProjectStatus(Enum):
    AWARDED = "awarded"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    REVISION = "revision"
    COMPLETED = "completed"
    DELIVERED = "delivered"
    PAID = "paid"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"

# Task Status Enum
class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    COMPLETED = "completed"

# Priority Levels
class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

# Database Models
class ManagedProject(Base):
    __tablename__ = 'managed_projects'
    
    id = Column(Integer, primary_key=True)
    freelancer_project_id = Column(Integer, unique=True, index=True)
    title = Column(String(500))
    description = Column(Text)
    client_id = Column(Integer)
    client_name = Column(String(200))
    budget = Column(Float)
    currency = Column(String(10))
    deadline = Column(DateTime)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.AWARDED)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM)
    
    # Project details
    requirements = Column(JSON)
    deliverables = Column(JSON)
    milestones = Column(JSON)
    technologies = Column(JSON)
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    hours_tracked = Column(Float, default=0.0)
    
    # Dates
    awarded_date = Column(DateTime, default=datetime.utcnow)
    start_date = Column(DateTime)
    planned_end_date = Column(DateTime)
    actual_end_date = Column(DateTime)
    
    # Risk management
    risk_level = Column(String(50))
    risk_factors = Column(JSON)
    
    # Financial
    payment_status = Column(String(50))
    amount_paid = Column(Float, default=0.0)
    
    # Relationships
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    communications = relationship("Communication", back_populates="project", cascade="all, delete-orphan")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    time_logs = relationship("TimeLog", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('managed_projects.id'))
    title = Column(String(500))
    description = Column(Text)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM)
    
    # Task details
    estimated_hours = Column(Float)
    actual_hours = Column(Float, default=0.0)
    assigned_to = Column(String(200))
    
    # Dates
    created_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    completed_date = Column(DateTime)
    
    # Dependencies
    depends_on = Column(JSON)  # List of task IDs
    blocks = Column(JSON)  # List of task IDs this blocks
    
    # Checklist
    checklist = Column(JSON)  # List of {item: str, completed: bool}
    
    project = relationship("ManagedProject", back_populates="tasks")

class Communication(Base):
    __tablename__ = 'communications'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('managed_projects.id'))
    message_type = Column(String(50))  # 'client_message', 'internal_note', 'update'
    sender = Column(String(200))
    recipient = Column(String(200))
    subject = Column(String(500))
    content = Column(Text)
    attachments = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    project = relationship("ManagedProject", back_populates="communications")

class ProjectFile(Base):
    __tablename__ = 'project_files'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('managed_projects.id'))
    filename = Column(String(500))
    file_type = Column(String(50))
    file_path = Column(String(1000))
    file_size = Column(Integer)
    uploaded_by = Column(String(200))
    uploaded_date = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, default=1)
    is_deliverable = Column(Boolean, default=False)
    
    project = relationship("ManagedProject", back_populates="files")

class TimeLog(Base):
    __tablename__ = 'time_logs'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('managed_projects.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    user = Column(String(200))
    hours = Column(Float)
    description = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("ManagedProject", back_populates="time_logs")

@dataclass
class ProjectTemplate:
    """Template for different project types"""
    name: str
    task_templates: List[Dict]
    milestone_templates: List[Dict]
    estimated_duration_days: int
    technologies: List[str]

# Project Manager Class
class ProjectManager:
    def __init__(self, freelancer_token: str, db_url: str = "sqlite:///project_management.db", redis_url: Optional[str] = None):
        self.token = freelancer_token
        self.api_base = "https://www.freelancer.com/api"
        self.headers = {
            "Freelancer-OAuth-V1": self.token,
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Database setup
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Redis for caching and real-time updates
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logging.info("✓ Redis connected for project management")
            except Exception as e:
                logging.warning(f"Redis connection failed: {e}")
        
        # Load project templates
        self.templates = self.load_project_templates()
        
        logging.info("✓ Project Manager initialized")

    def load_project_templates(self) -> Dict[str, ProjectTemplate]:
        """Load project templates for different types of projects"""
        templates = {
            "web_development": ProjectTemplate(
                name="Web Development",
                task_templates=[
                    {"title": "Requirements Analysis", "estimated_hours": 4, "priority": Priority.HIGH},
                    {"title": "Design Mockups", "estimated_hours": 8, "priority": Priority.HIGH},
                    {"title": "Frontend Development", "estimated_hours": 20, "priority": Priority.MEDIUM},
                    {"title": "Backend Development", "estimated_hours": 20, "priority": Priority.MEDIUM},
                    {"title": "Testing & QA", "estimated_hours": 8, "priority": Priority.HIGH},
                    {"title": "Deployment", "estimated_hours": 4, "priority": Priority.CRITICAL},
                    {"title": "Documentation", "estimated_hours": 4, "priority": Priority.LOW}
                ],
                milestone_templates=[
                    {"name": "Design Approval", "percentage": 20},
                    {"name": "Frontend Complete", "percentage": 50},
                    {"name": "Backend Complete", "percentage": 80},
                    {"name": "Final Delivery", "percentage": 100}
                ],
                estimated_duration_days=14,
                technologies=["HTML", "CSS", "JavaScript", "React", "Node.js"]
            ),
            "mobile_app": ProjectTemplate(
                name="Mobile App Development",
                task_templates=[
                    {"title": "Requirements & User Stories", "estimated_hours": 6, "priority": Priority.HIGH},
                    {"title": "UI/UX Design", "estimated_hours": 12, "priority": Priority.HIGH},
                    {"title": "App Architecture", "estimated_hours": 8, "priority": Priority.CRITICAL},
                    {"title": "Core Features Development", "estimated_hours": 40, "priority": Priority.HIGH},
                    {"title": "API Integration", "estimated_hours": 16, "priority": Priority.MEDIUM},
                    {"title": "Testing on Devices", "estimated_hours": 12, "priority": Priority.HIGH},
                    {"title": "App Store Submission", "estimated_hours": 4, "priority": Priority.MEDIUM}
                ],
                milestone_templates=[
                    {"name": "Design Approval", "percentage": 15},
                    {"name": "Alpha Version", "percentage": 40},
                    {"name": "Beta Version", "percentage": 70},
                    {"name": "Final Release", "percentage": 100}
                ],
                estimated_duration_days=21,
                technologies=["React Native", "Flutter", "Swift", "Kotlin"]
            ),
            "data_scraping": ProjectTemplate(
                name="Web Scraping",
                task_templates=[
                    {"title": "Target Analysis", "estimated_hours": 2, "priority": Priority.HIGH},
                    {"title": "Scraper Development", "estimated_hours": 8, "priority": Priority.HIGH},
                    {"title": "Data Validation", "estimated_hours": 4, "priority": Priority.MEDIUM},
                    {"title": "Error Handling", "estimated_hours": 4, "priority": Priority.HIGH},
                    {"title": "Performance Optimization", "estimated_hours": 4, "priority": Priority.MEDIUM},
                    {"title": "Documentation & Delivery", "estimated_hours": 2, "priority": Priority.LOW}
                ],
                milestone_templates=[
                    {"name": "Prototype Working", "percentage": 30},
                    {"name": "Full Scraper Complete", "percentage": 70},
                    {"name": "Final Delivery", "percentage": 100}
                ],
                estimated_duration_days=3,
                technologies=["Python", "BeautifulSoup", "Scrapy", "Selenium"]
            )
        }
        
        return templates

    def import_awarded_project(self, freelancer_project_id: int) -> Optional[ManagedProject]:
        """Import an awarded project from Freelancer API"""
        try:
            # Check if already exists
            existing = self.session.query(ManagedProject).filter_by(
                freelancer_project_id=freelancer_project_id
            ).first()
            
            if existing:
                logging.info(f"Project {freelancer_project_id} already imported")
                return existing
            
            # Fetch project details from Freelancer API
            response = requests.get(
                f"{self.api_base}/projects/0.1/projects/{freelancer_project_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                logging.error(f"Failed to fetch project {freelancer_project_id}: {response.status_code}")
                return None
            
            project_data = response.json().get('result', {})
            if not project_data:
                logging.error(f"No result in Freelancer API response for project {freelancer_project_id}: {response.text}")
                return None
            
            jobs = project_data.get('jobs')
            if jobs is None:
                logging.warning(f"Project {freelancer_project_id} has no jobs field or jobs is None. Response: {response.text}")
                jobs = []
            
            # Create managed project
            managed_project = ManagedProject(
                freelancer_project_id=freelancer_project_id,
                title=project_data.get('title', ''),
                description=project_data.get('description', ''),
                client_id=project_data.get('owner_id'),
                client_name=project_data.get('owner', {}).get('username', ''),
                budget=project_data.get('budget', {}).get('minimum', 0),
                currency=project_data.get('currency', {}).get('code', 'USD'),
                deadline=datetime.now() + timedelta(days=project_data.get('bidperiod', 7)),
                technologies=[job.get('name') for job in jobs if job and isinstance(job, dict)]
            )
            
            self.session.add(managed_project)
            self.session.commit()
            
            # Auto-generate tasks based on project type
            self.auto_generate_tasks(managed_project)
            
            logging.info(f"✓ Imported project: {managed_project.title}")
            return managed_project
            
        except Exception as e:
            logging.error(f"Error importing project: {e}")
            self.session.rollback()
            return None
    
    def fetch_and_import_awarded_projects(self) -> List[ManagedProject]:
        """Fetch all awarded projects from Freelancer and import them"""
        imported_projects = []
        
        try:
            # Get user ID from environment or token
            user_id = os.environ.get('FREELANCER_USER_ID', '45214417')
            
            # First, try to get user's bids to find awarded projects
            logging.info("Fetching user's bids to find awarded projects...")
            
            try:
                # Get user's recent bids
                response = requests.get(
                    f"{self.api_base}/projects/0.1/bids",
                    headers=self.headers,
                    params={
                        "bidders[]": user_id,
                        "limit": 100,
                        "compact": "false"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    bids = data.get('result', {}).get('bids', [])
                    logging.info(f"Found {len(bids)} bids")
                    
                    # Find awarded bids
                    awarded_project_ids = []
                    for bid in bids:
                        if bid.get('awarded') == True:
                            project_id = bid.get('project_id')
                            if project_id:
                                awarded_project_ids.append(project_id)
                    
                    logging.info(f"Found {len(awarded_project_ids)} awarded project IDs from bids")
                    
                    # Import each awarded project
                    for project_id in awarded_project_ids:
                        # Check if already imported
                        existing = self.session.query(ManagedProject).filter_by(
                            freelancer_project_id=project_id
                        ).first()
                        
                        if not existing:
                            # Import the project
                            managed_project = self.import_awarded_project(project_id)
                            if managed_project:
                                imported_projects.append(managed_project)
                                logging.info(f"✓ Imported awarded project {project_id}")
                        else:
                            logging.info(f"Project {project_id} already exists in database")
                    
                    if imported_projects:
                        logging.info(f"✓ Imported {len(imported_projects)} new awarded projects from bids")
                        
                        # Update Redis if available
                        if self.redis_client:
                            self.redis_client.hincrby('pm_stats', 'projects_imported', len(imported_projects))
                        
                        return imported_projects
                    else:
                        logging.info("No new awarded projects to import from bids")
                        
                else:
                    logging.warning(f"Failed to fetch bids: {response.status_code}")
                    
            except Exception as e:
                logging.warning(f"Error fetching bids: {e}")
            
            # Alternative approach: Try to get user's projects directly
            logging.info("Trying alternative approach to find awarded projects...")
            
            try:
                # Get user's projects (this might include projects where user is owner or awarded)
                response = requests.get(
                    f"{self.api_base}/users/0.1/users/{user_id}/projects",
                    headers=self.headers,
                    params={
                        "compact": "false"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    user_projects = data.get('result', {}).get('projects', [])
                    logging.info(f"Found {len(user_projects)} projects via user endpoint")
                    
                    # Filter for projects where user is awarded (not owner)
                    awarded_projects = []
                    for project in user_projects:
                        # Check if user is awarded to this project (not the owner)
                        if project.get('awarded_to') == user_id and project.get('owner_id') != user_id:
                            awarded_projects.append(project)
                    
                    logging.info(f"Found {len(awarded_projects)} awarded projects via user endpoint")
                    
                    # Import each awarded project
                    for project_data in awarded_projects:
                        project_id = project_data.get('id')
                        project_status = project_data.get('status', 'unknown')
                        
                        # Check if already imported
                        existing = self.session.query(ManagedProject).filter_by(
                            freelancer_project_id=project_id
                        ).first()
                        
                        if not existing:
                            # Import the project
                            managed_project = self.import_awarded_project(project_id)
                            if managed_project:
                                # Set appropriate status based on Freelancer status
                                if project_status == 'closed':
                                    managed_project.status = ProjectStatus.COMPLETED
                                elif project_status == 'active':
                                    managed_project.status = ProjectStatus.IN_PROGRESS
                                elif project_status == 'cancelled':
                                    managed_project.status = ProjectStatus.CANCELLED
                                
                                self.session.commit()
                                imported_projects.append(managed_project)
                                
                                # Send initial client message for active projects
                                if project_status == 'active':
                                    self.add_communication(
                                        project_id=managed_project.id,
                                        message_type='client_message',
                                        subject='Project Started',
                                        content=f'Thank you for awarding me your project! I have reviewed the requirements and will begin work immediately. You can expect regular updates on progress.',
                                        sender="System",
                                        recipient=managed_project.client_name
                                    )
                                
                                logging.info(f"✓ Imported project {project_id} with status '{project_status}'")
                        else:
                            logging.info(f"Project {project_id} already exists in database")
                    
                    if imported_projects:
                        logging.info(f"✓ Imported {len(imported_projects)} new projects via user endpoint")
                        
                        # Update Redis if available
                        if self.redis_client:
                            self.redis_client.hincrby('pm_stats', 'projects_imported', len(imported_projects))
                        
                        return imported_projects
                    else:
                        logging.info("No new projects to import via user endpoint")
                        
                else:
                    logging.warning(f"Failed to fetch user projects: {response.status_code}")
                    
            except Exception as e:
                logging.warning(f"Alternative approach failed: {e}")
            
            # If we still haven't found any projects, try manual import approach
            logging.info("No projects found via API. You may need to manually import projects using their IDs.")
            logging.info("Use the dashboard to import specific project IDs that you know you've been awarded.")
            
            return imported_projects
            
        except Exception as e:
            logging.error(f"Error fetching awarded projects: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return imported_projects

    def auto_generate_tasks(self, project: ManagedProject):
        """Auto-generate tasks based on project type"""
        # Determine project type from title and technologies
        project_type = self.detect_project_type(project)
        
        if project_type and project_type in self.templates:
            template = self.templates[project_type]
            
            # Create tasks from template
            for i, task_template in enumerate(template.task_templates):
                task = Task(
                    project_id=project.id,
                    title=task_template['title'],
                    estimated_hours=task_template['estimated_hours'],
                    priority=task_template['priority'],
                    due_date=project.deadline - timedelta(days=len(template.task_templates) - i)
                )
                self.session.add(task)
            
            # Set milestones
            project.milestones = template.milestone_templates
            
            # Update estimated dates
            project.planned_end_date = project.awarded_date + timedelta(days=template.estimated_duration_days)
            
            self.session.commit()
            logging.info(f"✓ Generated {len(template.task_templates)} tasks for project")

    def detect_project_type(self, project: ManagedProject) -> Optional[str]:
        """Detect project type from title and technologies"""
        title_lower = project.title.lower()
        tech_lower = [tech.lower() for tech in (project.technologies or [])]
        
        if any(word in title_lower for word in ['web', 'website', 'webapp']):
            return "web_development"
        elif any(word in title_lower for word in ['mobile', 'app', 'ios', 'android']):
            return "mobile_app"
        elif any(word in title_lower for word in ['scrape', 'scraping', 'extract', 'crawl']):
            return "data_scraping"
        
        # Check technologies
        if any(tech in tech_lower for tech in ['react', 'angular', 'vue', 'django', 'laravel']):
            return "web_development"
        elif any(tech in tech_lower for tech in ['react native', 'flutter', 'swift', 'kotlin']):
            return "mobile_app"
        elif any(tech in tech_lower for tech in ['python', 'scraping', 'beautifulsoup', 'scrapy']):
            return "data_scraping"
        
        return None

    def update_project_status(self, project_id: int, new_status: ProjectStatus) -> bool:
        """Update project status"""
        try:
            project = self.session.query(ManagedProject).filter_by(id=project_id).first()
            if project:
                old_status = project.status
                project.status = new_status
                
                # Update dates based on status
                if new_status == ProjectStatus.IN_PROGRESS and not project.start_date:
                    project.start_date = datetime.utcnow()
                elif new_status == ProjectStatus.COMPLETED:
                    project.actual_end_date = datetime.utcnow()
                
                self.session.commit()
                
                # Log status change
                self.add_communication(
                    project_id=project_id,
                    message_type='internal_note',
                    subject='Status Update',
                    content=f'Project status changed from {old_status.value} to {new_status.value}'
                )
                
                # Update Redis if available
                if self.redis_client:
                    self.redis_client.hset(f'project:{project_id}', 'status', new_status.value)
                
                return True
                
        except Exception as e:
            logging.error(f"Error updating project status: {e}")
            self.session.rollback()
            
        return False

    def update_task_status(self, task_id: int, new_status: TaskStatus) -> bool:
        """Update task status and recalculate project progress"""
        try:
            task = self.session.query(Task).filter_by(id=task_id).first()
            if task:
                task.status = new_status
                
                if new_status == TaskStatus.COMPLETED:
                    task.completed_date = datetime.utcnow()
                
                # Recalculate project progress
                self.recalculate_project_progress(task.project_id)
                
                self.session.commit()
                return True
                
        except Exception as e:
            logging.error(f"Error updating task status: {e}")
            self.session.rollback()
            
        return False

    def recalculate_project_progress(self, project_id: int):
        """Recalculate project progress based on completed tasks"""
        project = self.session.query(ManagedProject).filter_by(id=project_id).first()
        if project:
            total_tasks = len(project.tasks)
            completed_tasks = sum(1 for task in project.tasks if task.status == TaskStatus.COMPLETED)
            
            if total_tasks > 0:
                project.progress_percentage = int((completed_tasks / total_tasks) * 100)
            
            # Update Redis if available
            if self.redis_client:
                self.redis_client.hset(f'project:{project_id}', 'progress', project.progress_percentage)

    def add_communication(self, project_id: int, message_type: str, subject: str, content: str, 
                         sender: str = "System", recipient: str = "All", attachments: Optional[List[str]] = None):
        """Add communication record"""
        communication = Communication(
            project_id=project_id,
            message_type=message_type,
            sender=sender,
            recipient=recipient,
            subject=subject,
            content=content,
            attachments=attachments or []
        )
        
        self.session.add(communication)
        self.session.commit()
        
        # Notify via Redis if available
        if self.redis_client:
            self.redis_client.publish(f'project:{project_id}:updates', json.dumps({
                'type': 'new_communication',
                'subject': subject,
                'timestamp': datetime.utcnow().isoformat()
            }))

    def log_time(self, project_id: int, task_id: Optional[int], hours: float, 
                 description: str, user: str = "Developer"):
        """Log time spent on project/task"""
        time_log = TimeLog(
            project_id=project_id,
            task_id=task_id,
            user=user,
            hours=hours,
            description=description
        )
        
        self.session.add(time_log)
        
        # Update project hours
        project = self.session.query(ManagedProject).filter_by(id=project_id).first()
        if project:
            project.hours_tracked += hours
        
        # Update task hours if specified
        if task_id:
            task = self.session.query(Task).filter_by(id=task_id).first()
            if task:
                task.actual_hours += hours
        
        self.session.commit()

    def assess_project_risk(self, project_id: int) -> Dict[str, Any]:
        """Assess project risk based on various factors"""
        project = self.session.query(ManagedProject).filter_by(id=project_id).first()
        if not project:
            return {"risk_level": "unknown", "factors": []}
        
        risk_factors = []
        risk_score = 0
        
        # Check deadline risk
        days_until_deadline = (project.deadline - datetime.utcnow()).days
        if days_until_deadline < 3:
            risk_factors.append("Very tight deadline")
            risk_score += 30
        elif days_until_deadline < 7:
            risk_factors.append("Tight deadline")
            risk_score += 20
        
        # Check progress vs time elapsed
        if project.start_date:
            time_elapsed_percentage = ((datetime.utcnow() - project.start_date).days / 
                                     (project.deadline - project.start_date).days) * 100
            
            if time_elapsed_percentage > project.progress_percentage + 20:
                risk_factors.append("Behind schedule")
                risk_score += 25
        
        # Check blocked tasks
        blocked_tasks = sum(1 for task in project.tasks if task.status == TaskStatus.BLOCKED)
        if blocked_tasks > 0:
            risk_factors.append(f"{blocked_tasks} blocked tasks")
            risk_score += blocked_tasks * 10
        
        # Check client communication
        recent_comms = self.session.query(Communication).filter(
            Communication.project_id == project_id,
            Communication.message_type == 'client_message',
            Communication.timestamp > datetime.utcnow() - timedelta(days=3)
        ).count()
        
        if recent_comms == 0 and project.status == ProjectStatus.IN_PROGRESS:
            risk_factors.append("No recent client communication")
            risk_score += 15
        
        # Determine risk level
        if risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Update project
        project.risk_level = risk_level
        project.risk_factors = risk_factors
        self.session.commit()
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "factors": risk_factors
        }

    def generate_project_report(self, project_id: int) -> str:
        """Generate comprehensive project report"""
        project = self.session.query(ManagedProject).filter_by(id=project_id).first()
        if not project:
            return "Project not found"
        
        # Calculate metrics
        total_tasks = len(project.tasks)
        completed_tasks = sum(1 for task in project.tasks if task.status == TaskStatus.COMPLETED)
        in_progress_tasks = sum(1 for task in project.tasks if task.status == TaskStatus.IN_PROGRESS)
        blocked_tasks = sum(1 for task in project.tasks if task.status == TaskStatus.BLOCKED)
        
        # Time metrics
        estimated_hours = sum(task.estimated_hours or 0 for task in project.tasks)
        actual_hours = project.hours_tracked
        
        # Generate report using template
        report_template = """
# Project Report: {{ project.title }}

## Overview
- **Status**: {{ project.status.value }}
- **Progress**: {{ project.progress_percentage }}%
- **Client**: {{ project.client_name }}
- **Budget**: {{ project.currency }} {{ project.budget }}
- **Deadline**: {{ project.deadline.strftime('%Y-%m-%d') }}

## Progress Summary
- **Total Tasks**: {{ total_tasks }}
- **Completed**: {{ completed_tasks }} ({{ (completed_tasks/total_tasks*100)|round|int }}%)
- **In Progress**: {{ in_progress_tasks }}
- **Blocked**: {{ blocked_tasks }}

## Time Tracking
- **Estimated Hours**: {{ estimated_hours }}
- **Actual Hours**: {{ actual_hours }}
- **Efficiency**: {{ ((estimated_hours/actual_hours*100)|round|int if actual_hours > 0 else 'N/A') }}%

## Risk Assessment
- **Risk Level**: {{ project.risk_level or 'Not assessed' }}
{% if project.risk_factors %}
- **Risk Factors**:
{% for factor in project.risk_factors %}
  - {{ factor }}
{% endfor %}
{% endif %}

## Recent Activities
{% for comm in recent_activities %}
- {{ comm.timestamp.strftime('%Y-%m-%d %H:%M') }}: {{ comm.subject }}
{% endfor %}

## Next Steps
{% for task in upcoming_tasks %}
- {{ task.title }} (Due: {{ task.due_date.strftime('%Y-%m-%d') if task.due_date else 'Not set' }})
{% endfor %}

---
*Report generated on {{ now.strftime('%Y-%m-%d %H:%M:%S') }}*
        """
        
        # Get recent activities
        recent_activities = self.session.query(Communication).filter(
            Communication.project_id == project_id
        ).order_by(Communication.timestamp.desc()).limit(5).all()
        
        # Get upcoming tasks
        upcoming_tasks = self.session.query(Task).filter(
            Task.project_id == project_id,
            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
        ).order_by(Task.due_date).limit(5).all()
        
        # Render template
        template = Template(report_template)
        report = template.render(
            project=project,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            blocked_tasks=blocked_tasks,
            estimated_hours=estimated_hours,
            actual_hours=actual_hours,
            recent_activities=recent_activities,
            upcoming_tasks=upcoming_tasks,
            now=datetime.utcnow()
        )
        
        return report

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for project management dashboard"""
        # Active projects
        active_projects = self.session.query(ManagedProject).filter(
            ManagedProject.status.in_([
                ProjectStatus.PLANNING,
                ProjectStatus.IN_PROGRESS,
                ProjectStatus.REVIEW
            ])
        ).all()
        
        # Upcoming deadlines
        upcoming_deadlines = self.session.query(ManagedProject).filter(
            ManagedProject.deadline > datetime.utcnow(),
            ManagedProject.deadline < datetime.utcnow() + timedelta(days=7),
            ManagedProject.status != ProjectStatus.COMPLETED
        ).order_by(ManagedProject.deadline).all()
        
        # High risk projects
        high_risk_projects = self.session.query(ManagedProject).filter(
            ManagedProject.risk_level == 'high'
        ).all()
        
        # Today's tasks
        today_tasks = self.session.query(Task).filter(
            Task.due_date >= datetime.utcnow().date(),
            Task.due_date < datetime.utcnow().date() + timedelta(days=1),
            Task.status != TaskStatus.COMPLETED
        ).all()
        
        # Calculate metrics
        total_projects = self.session.query(ManagedProject).count()
        completed_projects = self.session.query(ManagedProject).filter(
            ManagedProject.status == ProjectStatus.COMPLETED
        ).count()
        
        total_hours = self.session.query(func.sum(TimeLog.hours)).scalar() or 0
        
        return {
            "active_projects": [self._project_summary(p) for p in active_projects],
            "upcoming_deadlines": [self._project_summary(p) for p in upcoming_deadlines],
            "high_risk_projects": [self._project_summary(p) for p in high_risk_projects],
            "today_tasks": [self._task_summary(t) for t in today_tasks],
            "metrics": {
                "total_projects": total_projects,
                "active_projects": len(active_projects),
                "completed_projects": completed_projects,
                "total_hours_tracked": total_hours,
                "completion_rate": (completed_projects / total_projects * 100) if total_projects > 0 else 0
            }
        }

    def _project_summary(self, project: ManagedProject) -> Dict:
        """Generate project summary for dashboard"""
        return {
            "id": project.id,
            "title": project.title,
            "client": project.client_name,
            "status": project.status.value,
            "progress": project.progress_percentage,
            "deadline": project.deadline.isoformat(),
            "risk_level": project.risk_level
        }

    def _task_summary(self, task: Task) -> Dict:
        """Generate task summary for dashboard"""
        return {
            "id": task.id,
            "title": task.title,
            "project_title": task.project.title if task.project else "Unknown",
            "status": task.status.value,
            "priority": task.priority.value,
            "due_date": task.due_date.isoformat() if task.due_date else None
        }

    def send_client_update(self, project_id: int, update_type: str = "progress"):
        """Send automated update to client via Freelancer messaging"""
        project = self.session.query(ManagedProject).filter_by(id=project_id).first()
        if not project:
            return False
        
        # Generate update message based on type
        if update_type == "progress":
            message = self._generate_progress_update(project)
        elif update_type == "milestone":
            message = self._generate_progress_update(project)  # Use progress update for milestone
        elif update_type == "completion":
            message = self._generate_progress_update(project)  # Use progress update for completion
        else:
            message = "Project update"
        
        # Send via Freelancer API
        try:
            response = requests.post(
                f"{self.api_base}/messages/0.1/messages",
                headers=self.headers,
                json={
                    "project_id": project.freelancer_project_id,
                    "message": message,
                    "to_users": [project.client_id]
                }
            )
            
            if response.status_code in [200, 201]:
                # Log communication
                self.add_communication(
                    project_id=project_id,
                    message_type='client_message',
                    subject=f'{update_type.title()} Update',
                    content=message,
                    sender="System",
                    recipient=project.client_name
                )
                return True
                
        except Exception as e:
            logging.error(f"Error sending client update: {e}")
            
        return False

    def _generate_progress_update(self, project: ManagedProject) -> str:
        """Generate progress update message"""
        return f"""Hello {project.client_name},

I wanted to provide you with an update on your project "{project.title}".

Current Progress: {project.progress_percentage}%
Status: {project.status.value.replace('_', ' ').title()}

Completed Tasks:
{self._list_completed_tasks(project)}

Currently Working On:
{self._list_current_tasks(project)}

The project is progressing well and we're on track to meet the deadline.

Please let me know if you have any questions or need any clarification.

Best regards"""

    def _list_completed_tasks(self, project: ManagedProject) -> str:
        """List recently completed tasks"""
        completed_tasks = [task for task in project.tasks if task.status == TaskStatus.COMPLETED][-3:]
        return '\n'.join([f"✓ {task.title}" for task in completed_tasks]) or "No tasks completed yet"

    def _list_current_tasks(self, project: ManagedProject) -> str:
        """List current tasks in progress"""
        current_tasks = [task for task in project.tasks if task.status == TaskStatus.IN_PROGRESS][:3]
        return '\n'.join([f"→ {task.title}" for task in current_tasks]) or "Preparing next phase"

# Integration with AutoWork Bot
class AutoWorkProjectIntegration:
    """Integrates project management with the existing AutoWork bot"""
    
    def __init__(self, project_manager: ProjectManager, autowork_bot):
        self.pm = project_manager
        self.bot = autowork_bot
        
    def check_awarded_projects(self):
        """Check for newly awarded projects and import them"""
        try:
            # Get user's projects
            response = requests.get(
                f"{self.bot.api_base}/projects/0.1/projects",
                headers=self.bot.headers,
                params={
                    "owners[]": self.bot.user_id,
                    "statuses[]": "awarded",
                    "compact": "false"
                }
            )
            
            if response.status_code == 200:
                projects = response.json().get('result', {}).get('projects', [])
                
                for project in projects:
                    project_id = project['id']
                    
                    # Check if already imported
                    existing = self.pm.session.query(ManagedProject).filter_by(
                        freelancer_project_id=project_id
                    ).first()
                    
                    if not existing:
                        logging.info(f"New awarded project detected: {project['title']}")
                        self.pm.import_awarded_project(project_id)
                        
                        # Send initial message to client
                        self.pm.send_client_update(project_id, "welcome")
                        
        except Exception as e:
            logging.error(f"Error checking awarded projects: {e}")

    def update_bot_stats(self):
        """Update bot statistics with project management data"""
        if self.bot.redis_client:
            # Get project stats
            active_projects = self.pm.session.query(ManagedProject).filter(
                ManagedProject.status.in_([ProjectStatus.IN_PROGRESS, ProjectStatus.REVIEW])
            ).count()
            
            completed_projects = self.pm.session.query(ManagedProject).filter(
                ManagedProject.status == ProjectStatus.COMPLETED
            ).count()
            
            # Update Redis
            self.bot.redis_client.hset('bot_stats', mapping={
                'active_projects': active_projects,
                'completed_projects': completed_projects,
                'last_pm_update': datetime.utcnow().isoformat()
            })

# API Endpoints for Dashboard (using Flask)
from flask import Flask, jsonify, request, render_template_string
from sqlalchemy import func

def create_project_management_api(project_manager: ProjectManager):
    """Create Flask API for project management dashboard"""
    app = Flask(__name__)
    
    @app.route('/api/projects', methods=['GET'])
    def get_projects():
        """Get all projects with optional filtering"""
        status = request.args.get('status')
        
        query = project_manager.session.query(ManagedProject)
        if status:
            query = query.filter(ManagedProject.status == ProjectStatus[status.upper()])
        
        projects = query.all()
        return jsonify([project_manager._project_summary(p) for p in projects])
    
    @app.route('/api/projects/sync', methods=['POST'])
    def sync_projects():
        """Fetch and import awarded projects from Freelancer"""
        try:
            imported_projects = project_manager.fetch_and_import_awarded_projects()
            return jsonify({
                "success": True,
                "imported_count": len(imported_projects),
                "projects": [project_manager._project_summary(p) for p in imported_projects]
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/projects/<int:project_id>', methods=['GET'])
    def get_project(project_id):
        """Get detailed project information"""
        project = project_manager.session.query(ManagedProject).filter_by(id=project_id).first()
        if not project:
            return jsonify({"error": "Project not found"}), 404
        
        return jsonify({
            **project_manager._project_summary(project),
            "tasks": [project_manager._task_summary(t) for t in project.tasks],
            "recent_communications": [
                {
                    "subject": c.subject,
                    "timestamp": c.timestamp.isoformat(),
                    "type": c.message_type
                } for c in project.communications[-5:]
            ],
            "time_tracked": project.hours_tracked,
            "risk_assessment": {
                "level": project.risk_level,
                "factors": project.risk_factors
            }
        })
    
    @app.route('/api/projects/<int:project_id>/status', methods=['PUT'])
    def update_project_status(project_id):
        """Update project status"""
        data = request.json
        new_status = ProjectStatus[data.get('status').upper()]
        
        if project_manager.update_project_status(project_id, new_status):
            return jsonify({"success": True})
        return jsonify({"error": "Failed to update status"}), 400
    
    @app.route('/api/tasks/<int:task_id>/status', methods=['PUT'])
    def update_task_status(task_id):
        """Update task status"""
        data = request.json
        new_status = TaskStatus[data.get('status').upper()]
        
        if project_manager.update_task_status(task_id, new_status):
            return jsonify({"success": True})
        return jsonify({"error": "Failed to update task"}), 400
    
    @app.route('/api/projects/<int:project_id>/time', methods=['POST'])
    def log_time(project_id):
        """Log time for a project"""
        data = request.json
        project_manager.log_time(
            project_id=project_id,
            task_id=data.get('task_id'),
            hours=float(data.get('hours')),
            description=data.get('description', ''),
            user=data.get('user', 'Developer')
        )
        return jsonify({"success": True})
    
    @app.route('/api/projects/<int:project_id>/report', methods=['GET'])
    def get_project_report(project_id):
        """Get project report"""
        report = project_manager.generate_project_report(project_id)
        return jsonify({"report": report})
    
    @app.route('/api/dashboard', methods=['GET'])
    def get_dashboard():
        """Get dashboard data"""
        return jsonify(project_manager.get_dashboard_data())
    
    @app.route('/api/projects/<int:project_id>/client-update', methods=['POST'])
    def send_client_update(project_id):
        """Send update to client"""
        update_type = request.json.get('type', 'progress')
        if project_manager.send_client_update(project_id, update_type):
            return jsonify({"success": True})
        return jsonify({"error": "Failed to send update"}), 400
    
    return app

# Main execution example
if __name__ == "__main__":
    # Initialize project manager
    token = os.environ.get('FREELANCER_OAUTH_TOKEN')
    if not token:
        print("❌ FREELANCER_OAUTH_TOKEN not found in environment")
        sys.exit(1)
        
    pm = ProjectManager(
        freelancer_token=token,
        redis_url=os.environ.get('REDIS_URL')
    )
    
    # Example: Import an awarded project
    # pm.import_awarded_project(12345678)
    
    # Example: Update project status
    # pm.update_project_status(1, ProjectStatus.IN_PROGRESS)
    
    # Example: Log time
    # pm.log_time(project_id=1, task_id=1, hours=2.5, description="Implemented login functionality")
    
    # Example: Generate report
    # report = pm.generate_project_report(1)
    # print(report)
    
    # Start API server
    app = create_project_management_api(pm)
    app.run(host='0.0.0.0', port=5001, debug=True)