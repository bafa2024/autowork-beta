#!/usr/bin/env python3
"""
Test script for task breakdown and versioned releases functionality
"""

import json
import logging
from auto_sdlc_service import AutoSDLCService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_task_breakdown_and_versions():
    """Test the task breakdown and versioned releases functionality"""
    
    # Sample project description
    project_description = """
    Create a comprehensive e-commerce platform with the following features:
    
    Core Features:
    - User authentication and registration system
    - Product catalog with search and filtering
    - Shopping cart and checkout process
    - Order management and tracking
    - Payment integration with multiple gateways
    - Admin dashboard for product and order management
    - Customer reviews and ratings system
    - Email notifications for orders and updates
    - Mobile-responsive design
    - Inventory management system
    
    Technical Requirements:
    - Modern web application with React frontend
    - RESTful API backend with Node.js/Express
    - PostgreSQL database for data storage
    - Redis for caching and session management
    - AWS S3 for file storage
    - Stripe and PayPal payment integration
    - SendGrid for email notifications
    - Docker containerization
    - CI/CD pipeline with GitHub Actions
    
    The platform should be scalable, secure, and provide an excellent user experience.
    """
    
    try:
        logger.info("🚀 Testing task breakdown and versioned releases functionality...")
        
        # Initialize SDLC service
        sdlc_service = AutoSDLCService()
        
        # Generate complete SDLC documents
        result = sdlc_service.generate_complete_sdlc(project_description)
        
        # Verify the result structure
        required_keys = [
            'project_analysis', 'srs_document', 'system_design', 'ui_design',
            'task_breakdowns', 'versioned_releases', 'implementation_plan',
            'test_plan', 'deployment_plan', 'maintenance_plan', 'metadata'
        ]
        
        for key in required_keys:
            if key not in result:
                logger.error(f"❌ Missing required key: {key}")
                return False
        
        logger.info("✅ All required keys present in result")
        
        # Check task breakdowns
        task_breakdowns = result['task_breakdowns']
        logger.info(f"📋 Generated {len(task_breakdowns)} task breakdowns")
        
        total_tasks = sum(len(bd['tasks']) for bd in task_breakdowns)
        total_hours = sum(bd['estimated_hours'] for bd in task_breakdowns)
        logger.info(f"📊 Total tasks: {total_tasks}, Total hours: {total_hours}")
        
        # Check versioned releases
        versioned_releases = result['versioned_releases']
        logger.info(f"📦 Generated {len(versioned_releases)} versioned releases")
        
        for release in versioned_releases:
            logger.info(f"  - {release['version']}: {release['name']} ({release['estimated_hours']}h)")
        
        # Check metadata
        metadata = result['metadata']
        logger.info(f"📈 Project complexity: {metadata['project_complexity']}")
        logger.info(f"👥 Recommended team size: {metadata['recommended_team_size']}")
        logger.info(f"⏱️ Total estimated hours: {metadata['total_estimated_hours']}")
        logger.info(f"📋 Total tasks: {metadata['total_tasks']}")
        logger.info(f"📦 Total versions: {metadata['total_versions']}")
        
        # Save detailed results to file
        with open('test_task_breakdown_results.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info("💾 Detailed results saved to test_task_breakdown_results.json")
        
        logger.info("🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_task_breakdown_and_versions()
    if success:
        print("\n✅ Task breakdown and versioned releases functionality is working correctly!")
    else:
        print("\n❌ Task breakdown and versioned releases functionality has issues!") 