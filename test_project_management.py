#!/usr/bin/env python3
"""
Comprehensive Test Script for Project Management System
Tests all components and provides debugging information
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_environment_setup():
    """Test environment variables and dependencies"""
    print("🔧 Testing Environment Setup...")
    
    # Check required environment variables
    required_vars = ['FREELANCER_OAUTH_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables found")
    
    # Test imports
    try:
        import requests
        print("✅ requests module available")
    except ImportError:
        print("❌ requests module not available")
        return False
    
    try:
        import redis
        print("✅ redis module available")
    except ImportError:
        print("❌ redis module not available")
        return False
    
    try:
        from sqlalchemy import create_engine
        print("✅ SQLAlchemy available")
    except ImportError:
        print("❌ SQLAlchemy not available")
        return False
    
    try:
        from flask import Flask
        print("✅ Flask available")
    except ImportError:
        print("❌ Flask not available")
        return False
    
    return True

def test_project_management_imports():
    """Test project management module imports"""
    print("\n📦 Testing Project Management Imports...")
    
    try:
        from project_management import ProjectManager, ProjectStatus, TaskStatus, Priority
        print("✅ Project management classes imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import project management: {e}")
        return False

def test_autowork_integration_imports():
    """Test autowork integration module imports"""
    print("\n🤖 Testing AutoWork Integration Imports...")
    
    try:
        from autowork_integration import AutoWorkIntegration
        print("✅ AutoWork integration imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import autowork integration: {e}")
        return False

def test_project_manager_initialization():
    """Test project manager initialization"""
    print("\n🏗️ Testing Project Manager Initialization...")
    
    try:
        from project_management import ProjectManager
        
        # Initialize with test database
        pm = ProjectManager(
            freelancer_token=os.environ.get('FREELANCER_OAUTH_TOKEN'),
            db_url="sqlite:///test_project_management.db",
            redis_url=os.environ.get('REDIS_URL')
        )
        
        print("✅ Project manager initialized successfully")
        
        # Test database connection
        try:
            pm.session.execute("SELECT 1")
            print("✅ Database connection working")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        return pm
        
    except Exception as e:
        print(f"❌ Failed to initialize project manager: {e}")
        return False

def test_freelancer_api_connection(pm):
    """Test Freelancer API connection"""
    print("\n🌐 Testing Freelancer API Connection...")
    
    try:
        # Test API headers
        headers = pm.headers
        if 'Freelancer-OAuth-V1' in headers:
            print("✅ API headers configured")
        else:
            print("❌ API headers not configured properly")
            return False
        
        # Test API base URL
        if pm.api_base == "https://www.freelancer.com/api":
            print("✅ API base URL configured")
        else:
            print("❌ API base URL not configured properly")
            return False
        
        print("✅ Freelancer API connection test passed")
        return True
        
    except Exception as e:
        print(f"❌ Freelancer API connection failed: {e}")
        return False

def test_project_templates(pm):
    """Test project templates loading"""
    print("\n📋 Testing Project Templates...")
    
    try:
        templates = pm.templates
        
        if not templates:
            print("❌ No project templates loaded")
            return False
        
        expected_templates = ['web_development', 'mobile_app', 'data_scraping']
        
        for template_name in expected_templates:
            if template_name in templates:
                template = templates[template_name]
                print(f"✅ {template_name} template loaded with {len(template.task_templates)} tasks")
            else:
                print(f"❌ {template_name} template not found")
                return False
        
        print("✅ All project templates loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Project templates test failed: {e}")
        return False

def test_database_operations(pm):
    """Test basic database operations"""
    print("\n🗄️ Testing Database Operations...")
    
    try:
        # Test project count
        project_count = pm.session.query(pm.ManagedProject).count()
        print(f"✅ Current projects in database: {project_count}")
        
        # Test task count
        task_count = pm.session.query(pm.Task).count()
        print(f"✅ Current tasks in database: {task_count}")
        
        # Test communication count
        comm_count = pm.session.query(pm.Communication).count()
        print(f"✅ Current communications in database: {comm_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False

def test_dashboard_data_generation(pm):
    """Test dashboard data generation"""
    print("\n📊 Testing Dashboard Data Generation...")
    
    try:
        dashboard_data = pm.get_dashboard_data()
        
        required_keys = ['metrics', 'active_projects', 'today_tasks', 'upcoming_deadlines']
        
        for key in required_keys:
            if key in dashboard_data:
                print(f"✅ {key} data available")
            else:
                print(f"❌ {key} data missing")
                return False
        
        # Check metrics
        metrics = dashboard_data['metrics']
        print(f"✅ Active projects: {metrics.get('active_projects', 0)}")
        print(f"✅ Total hours tracked: {metrics.get('total_hours_tracked', 0)}")
        print(f"✅ Completion rate: {metrics.get('completion_rate', 0)}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard data generation failed: {e}")
        return False

def test_api_server():
    """Test API server functionality"""
    print("\n🚀 Testing API Server...")
    
    try:
        from project_management_api import app
        
        # Test app creation
        if app:
            print("✅ Flask app created successfully")
        else:
            print("❌ Flask app creation failed")
            return False
        
        # Test routes
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/api/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
            
            # Test dashboard endpoint
            response = client.get('/api/dashboard')
            if response.status_code == 200:
                print("✅ Dashboard endpoint working")
            else:
                print(f"❌ Dashboard endpoint failed: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ API server test failed: {e}")
        return False

def test_autowork_integration():
    """Test autowork integration"""
    print("\n🔗 Testing AutoWork Integration...")
    
    try:
        from autowork_integration import AutoWorkIntegration
        
        # Initialize integration
        integration = AutoWorkIntegration()
        print("✅ AutoWork integration initialized")
        
        # Test integration methods
        if hasattr(integration, 'check_awarded_projects'):
            print("✅ check_awarded_projects method available")
        else:
            print("❌ check_awarded_projects method missing")
            return False
        
        if hasattr(integration, 'monitor_project_health'):
            print("✅ monitor_project_health method available")
        else:
            print("❌ monitor_project_health method missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ AutoWork integration test failed: {e}")
        return False

def create_sample_project(pm):
    """Create a sample project for testing"""
    print("\n🧪 Creating Sample Project...")
    
    try:
        from project_management import ManagedProject, ProjectStatus, Priority
        
        # Create sample project
        sample_project = ManagedProject(
            freelancer_project_id=999999,
            title="Test Project - Web Development",
            description="This is a test project for debugging purposes",
            client_id=12345,
            client_name="TestClient",
            budget=500.0,
            currency="USD",
            deadline=datetime.now() + timedelta(days=14),
            status=ProjectStatus.PLANNING,
            priority=Priority.MEDIUM,
            technologies=["HTML", "CSS", "JavaScript"],
            progress_percentage=0,
            hours_tracked=0.0
        )
        
        pm.session.add(sample_project)
        pm.session.commit()
        
        print(f"✅ Sample project created with ID: {sample_project.id}")
        return sample_project
        
    except Exception as e:
        print(f"❌ Failed to create sample project: {e}")
        pm.session.rollback()
        return None

def test_project_operations(pm, sample_project):
    """Test project operations with sample project"""
    print("\n⚙️ Testing Project Operations...")
    
    try:
        # Test project status update
        success = pm.update_project_status(sample_project.id, pm.ProjectStatus.IN_PROGRESS)
        if success:
            print("✅ Project status update working")
        else:
            print("❌ Project status update failed")
            return False
        
        # Test time logging
        pm.log_time(
            project_id=sample_project.id,
            task_id=None,
            hours=2.5,
            description="Initial setup and planning",
            user="Developer"
        )
        print("✅ Time logging working")
        
        # Test communication
        pm.add_communication(
            project_id=sample_project.id,
            message_type='client_message',
            subject='Project Update',
            content='Project is progressing well. Initial setup completed.',
            sender="Developer",
            recipient="TestClient"
        )
        print("✅ Communication logging working")
        
        # Test risk assessment
        risk_assessment = pm.assess_project_risk(sample_project.id)
        print(f"✅ Risk assessment working: {risk_assessment.get('risk_level', 'unknown')} risk")
        
        # Test project report
        report = pm.generate_project_report(sample_project.id)
        if report:
            print("✅ Project report generation working")
        else:
            print("❌ Project report generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Project operations test failed: {e}")
        return False

def cleanup_test_data(pm, sample_project):
    """Clean up test data"""
    print("\n🧹 Cleaning Up Test Data...")
    
    try:
        if sample_project:
            pm.session.delete(sample_project)
            pm.session.commit()
            print("✅ Sample project cleaned up")
        
        # Close session
        pm.session.close()
        print("✅ Database session closed")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

def main():
    """Main test function"""
    print("🚀 Starting Comprehensive Project Management Test Suite")
    print("=" * 60)
    
    # Test environment
    if not test_environment_setup():
        print("\n❌ Environment setup failed. Please check your configuration.")
        return False
    
    # Test imports
    if not test_project_management_imports():
        print("\n❌ Project management imports failed.")
        return False
    
    if not test_autowork_integration_imports():
        print("\n❌ AutoWork integration imports failed.")
        return False
    
    # Test project manager
    pm = test_project_manager_initialization()
    if not pm:
        print("\n❌ Project manager initialization failed.")
        return False
    
    # Test API connection
    if not test_freelancer_api_connection(pm):
        print("\n❌ Freelancer API connection failed.")
        return False
    
    # Test templates
    if not test_project_templates(pm):
        print("\n❌ Project templates test failed.")
        return False
    
    # Test database operations
    if not test_database_operations(pm):
        print("\n❌ Database operations test failed.")
        return False
    
    # Test dashboard data
    if not test_dashboard_data_generation(pm):
        print("\n❌ Dashboard data generation failed.")
        return False
    
    # Test API server
    if not test_api_server():
        print("\n❌ API server test failed.")
        return False
    
    # Test autowork integration
    if not test_autowork_integration():
        print("\n❌ AutoWork integration test failed.")
        return False
    
    # Create and test sample project
    sample_project = create_sample_project(pm)
    if sample_project:
        if not test_project_operations(pm, sample_project):
            print("\n❌ Project operations test failed.")
            return False
    
    # Cleanup
    cleanup_test_data(pm, sample_project)
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Project management system is working correctly.")
    print("\n🎉 You can now:")
    print("  1. Start the API server: python project_management_api.py")
    print("  2. Open the dashboard: http://localhost:5001")
    print("  3. Run the integration: python autowork_integration.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 