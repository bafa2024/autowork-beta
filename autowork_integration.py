#!/usr/bin/env python3
"""
AutoWork Bot Integration - Connects bidding bot with project management
Runs alongside the main bot to manage awarded projects
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime, timedelta
from typing import List, Dict

# Import the project management system
from project_management import ProjectManager, ProjectStatus, TaskStatus

# Import the existing bot
from autowork_minimal import AutoWorkMinimal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('project_integration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class AutoWorkIntegration:
    """Integrates the bidding bot with project management"""
    
    def __init__(self):
        # Load environment variables
        self.freelancer_token = os.environ.get('FREELANCER_OAUTH_TOKEN')
        self.user_id = int(os.environ.get('FREELANCER_USER_ID', '45214417'))
        
        # Initialize components
        self.bot = AutoWorkMinimal()
        self.pm = ProjectManager(
            freelancer_token=self.freelancer_token,
            redis_url=os.environ.get('REDIS_URL')
        )
        
        # Track integration state
        self.last_check = datetime.now()
        self.notifications_sent = set()
        
        logging.info("✓ AutoWork Integration initialized")

    def check_awarded_projects(self):
        """Check for newly awarded projects and import them"""
        logging.info("Checking for awarded projects...")
        
        try:
            # Use the project manager's fetch method
            imported_projects = self.pm.fetch_and_import_awarded_projects()
            
            if imported_projects:
                for project in imported_projects:
                    logging.info(f"🎉 New awarded project imported: {project.title}")
                    
                    # Send welcome message to client
                    self._send_welcome_message(project)
                    
                    # Create initial tasks
                    self._setup_initial_workflow(project)
                    
                    # Update bot statistics
                    if self.bot.redis_client:
                        self.bot.redis_client.hincrby('bot_stats', 'projects_won', len(imported_projects))
                        self.bot.redis_client.set('last_project_sync', datetime.now().isoformat())
                
                logging.info(f"✓ Imported {len(imported_projects)} new projects")
            else:
                logging.info("No new awarded projects found")
                
                # Update last check time in Redis
                if self.bot.redis_client:
                    self.bot.redis_client.set('last_project_check', datetime.now().isoformat())
                    
        except Exception as e:
            logging.error(f"Error checking awarded projects: {e}")
            import traceback
            logging.error(traceback.format_exc())

    def _send_welcome_message(self, project):
        """Send welcome message to client for new project"""
        message = f"""Hello {project.client_name},

Thank you for awarding me your project "{project.title}"! I'm excited to work with you.

I've reviewed the project requirements and I'm ready to begin. Here's my plan:

1. Initial Planning & Setup
2. Development/Implementation Phase
3. Testing & Quality Assurance
4. Final Delivery & Support

I'll keep you updated on progress regularly. You can expect the first update within 24 hours.

Please feel free to reach out if you have any questions or additional requirements.

Looking forward to delivering excellent results!

Best regards"""
        
        self.pm.send_client_update(project.id, "welcome")
        self.pm.add_communication(
            project_id=project.id,
            message_type='client_message',
            subject='Project Kickoff',
            content=message,
            sender="System",
            recipient=project.client_name
        )

    def _setup_initial_workflow(self, project):
        """Setup initial workflow for new project"""
        # Update project status to planning
        self.pm.update_project_status(project.id, ProjectStatus.PLANNING)
        
        # Set initial risk assessment
        self.pm.assess_project_risk(project.id)
        
        # Schedule first client update
        self._schedule_client_update(project.id, datetime.now() + timedelta(days=1))

    def monitor_project_health(self):
        """Monitor health of all active projects"""
        logging.info("Monitoring project health...")
        
        # Get all active projects
        active_projects = self.pm.session.query(self.pm.ManagedProject).filter(
            self.pm.ManagedProject.status.in_([
                ProjectStatus.PLANNING,
                ProjectStatus.IN_PROGRESS,
                ProjectStatus.REVIEW
            ])
        ).all()
        
        for project in active_projects:
            # Assess risk
            risk_assessment = self.pm.assess_project_risk(project.id)
            
            # Handle high-risk projects
            if risk_assessment['risk_level'] == 'high':
                self._handle_high_risk_project(project, risk_assessment)
            
            # Check for stalled projects
            if self._is_project_stalled(project):
                self._handle_stalled_project(project)
            
            # Send scheduled updates
            if self._should_send_update(project):
                self.pm.send_client_update(project.id, "progress")

    def _handle_high_risk_project(self, project, risk_assessment):
        """Handle high-risk projects with special attention"""
        notification_key = f"high_risk_{project.id}_{datetime.now().date()}"
        
        if notification_key not in self.notifications_sent:
            logging.warning(f"⚠️ High risk project: {project.title}")
            logging.warning(f"Risk factors: {', '.join(risk_assessment['factors'])}")
            
            # Send urgent update to client if deadline is very close
            if 'Very tight deadline' in risk_assessment['factors']:
                self._send_deadline_warning(project)
            
            # Mark notification as sent
            self.notifications_sent.add(notification_key)

    def _handle_stalled_project(self, project):
        """Handle projects that haven't progressed"""
        logging.warning(f"Project stalled: {project.title}")
        
        # Find blocked tasks
        blocked_tasks = [t for t in project.tasks if t.status == TaskStatus.BLOCKED]
        
        if blocked_tasks:
            # Send message about blocked tasks
            message = f"Project has {len(blocked_tasks)} blocked tasks requiring attention"
            self.pm.add_communication(
                project_id=project.id,
                message_type='internal_note',
                subject='Blocked Tasks Alert',
                content=message
            )

    def _is_project_stalled(self, project) -> bool:
        """Check if project has stalled"""
        # No progress in 3 days
        recent_logs = self.pm.session.query(self.pm.TimeLog).filter(
            self.pm.TimeLog.project_id == project.id,
            self.pm.TimeLog.date > datetime.now() - timedelta(days=3)
        ).count()
        
        return recent_logs == 0 and project.status == ProjectStatus.IN_PROGRESS

    def _should_send_update(self, project) -> bool:
        """Check if should send client update"""
        # Get last client communication
        last_comm = self.pm.session.query(self.pm.Communication).filter(
            self.pm.Communication.project_id == project.id,
            self.pm.Communication.message_type == 'client_message'
        ).order_by(self.pm.Communication.timestamp.desc()).first()
        
        if not last_comm:
            return True
        
        # Send update every 2-3 days
        days_since_last = (datetime.now() - last_comm.timestamp).days
        return days_since_last >= 2

    def _send_deadline_warning(self, project):
        """Send deadline warning to client"""
        days_left = (project.deadline - datetime.now()).days
        
        message = f"""Hello {project.client_name},

I wanted to update you on the status of "{project.title}".

We have {days_left} days until the deadline, and the project is currently {project.progress_percentage}% complete.

I'm working diligently to ensure timely delivery. Here's what I'm focusing on:
{self._get_current_focus(project)}

If you have any concerns or need to discuss the timeline, please let me know immediately.

Best regards"""
        
        self.pm.add_communication(
            project_id=project.id,
            message_type='client_message',
            subject='Project Timeline Update',
            content=message
        )

    def _get_current_focus(self, project) -> str:
        """Get current focus tasks for project"""
        current_tasks = [t for t in project.tasks if t.status == TaskStatus.IN_PROGRESS][:3]
        if current_tasks:
            return '\n'.join([f"- {task.title}" for task in current_tasks])
        return "- Completing remaining tasks"

    def _schedule_client_update(self, project_id: int, when: datetime):
        """Schedule a client update for specific time"""
        # This would integrate with a task scheduler
        pass

    def sync_time_tracking(self):
        """Sync time tracking with external tools if configured"""
        logging.info("Syncing time tracking...")
        
        # This could integrate with tools like Toggl, Clockify, etc.
        # For now, we'll just log a summary
        
        today_logs = self.pm.session.query(self.pm.TimeLog).filter(
            self.pm.TimeLog.date >= datetime.now().date()
        ).all()
        
        total_hours = sum(log.hours for log in today_logs)
        logging.info(f"Hours tracked today: {total_hours}")

    def generate_daily_summary(self):
        """Generate daily summary of all projects"""
        logging.info("Generating daily summary...")
        
        # Get all active projects
        active_projects = self.pm.session.query(self.pm.ManagedProject).filter(
            self.pm.ManagedProject.status != ProjectStatus.COMPLETED
        ).all()
        
        summary = []
        summary.append("📊 DAILY PROJECT SUMMARY")
        summary.append("=" * 50)
        summary.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        summary.append(f"Active Projects: {len(active_projects)}")
        summary.append("")
        
        for project in active_projects:
            summary.append(f"📁 {project.title}")
            summary.append(f"   Status: {project.status.value}")
            summary.append(f"   Progress: {project.progress_percentage}%")
            summary.append(f"   Risk: {project.risk_level or 'Not assessed'}")
            summary.append(f"   Deadline: {project.deadline.strftime('%Y-%m-%d')}")
            summary.append("")
        
        # Log summary
        summary_text = '\n'.join(summary)
        logging.info(f"\n{summary_text}")
        
        # Save to file
        with open(f"daily_summary_{datetime.now().strftime('%Y%m%d')}.txt", 'w') as f:
            f.write(summary_text)
        
        # Update Redis if available
        if self.bot.redis_client:
            self.bot.redis_client.set('last_daily_summary', summary_text)

    def run_scheduled_tasks(self):
        """Run all scheduled tasks"""
        # Check for awarded projects every 30 minutes
        schedule.every(30).minutes.do(self.check_awarded_projects)
        
        # Monitor project health every hour
        schedule.every().hour.do(self.monitor_project_health)
        
        # Sync time tracking every 4 hours
        schedule.every(4).hours.do(self.sync_time_tracking)
        
        # Generate daily summary at 9 PM
        schedule.every().day.at("21:00").do(self.generate_daily_summary)
        
        logging.info("✓ Scheduled tasks configured")
        
        # Run initial checks
        self.check_awarded_projects()
        self.monitor_project_health()
        
        # Keep running scheduled tasks
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logging.info("Integration stopped by user")
                break
            except Exception as e:
                logging.error(f"Error in scheduled task: {e}")
                time.sleep(300)  # Wait 5 minutes on error

    def handle_bot_webhook(self, event_type: str, data: Dict):
        """Handle webhooks from the main bot"""
        if event_type == "project_awarded":
            # Import the awarded project
            project_id = data.get('project_id')
            if project_id:
                self.pm.import_awarded_project(project_id)
        
        elif event_type == "bid_placed":
            # Track bid in analytics
            if self.bot.redis_client:
                self.bot.redis_client.hincrby('integration_stats', 'bids_tracked', 1)


def main():
    """Main entry point"""
    print("="*60)
    print("AutoWork Project Management Integration")
    print("="*60)
    print(f"Starting at: {datetime.now()}")
    print("This will monitor awarded projects and manage them automatically")
    print("Press Ctrl+C to stop")
    print("="*60)
    
    # Create integration instance
    integration = AutoWorkIntegration()
    
    # Run scheduled tasks
    integration.run_scheduled_tasks()


if __name__ == "__main__":
    main()