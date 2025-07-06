#!/usr/bin/env python3
"""
Test script for Implementation Tools functionality
"""

import json
import logging
from datetime import datetime
from auto_sdlc_service import AutoSDLCService, ProjectAnalysis, DesignDocument

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_implementation_tools():
    """Test implementation tools generation"""
    logging.info("🛠️ Testing implementation tools functionality...")
    
    try:
        # Initialize SDLC service
        sdlc_service = AutoSDLCService()
        
        # Create sample project analysis
        analysis = ProjectAnalysis(
            project_type="web_app",
            complexity="medium",
            estimated_hours=120,
            technologies=["python", "javascript", "html", "css"],
            key_features=["user authentication", "database integration", "responsive design"],
            risks=["scope creep", "technical debt"]
        )
        
        # Create sample design document
        design = DesignDocument(
            architecture_type="MVC",
            components=[
                {"name": "Frontend", "description": "React-based user interface"},
                {"name": "Backend", "description": "Python Flask API"},
                {"name": "Database", "description": "PostgreSQL database"}
            ],
            data_models=[
                {"name": "User", "fields": "id, name, email, password", "relationships": "has many projects"}
            ],
            api_endpoints=[
                {"method": "GET", "path": "/api/users", "description": "Get all users"}
            ],
            technology_stack={
                "frontend": ["React", "HTML5", "CSS3"],
                "backend": ["Python", "Flask"],
                "database": ["PostgreSQL"]
            },
            security_considerations=["HTTPS", "Input validation", "SQL injection prevention"],
            scalability_plan="Horizontal scaling with load balancers"
        )
        
        # Generate implementation tools
        logging.info("🛠️ Generating implementation tools...")
        tools = sdlc_service.generate_implementation_tools(analysis, design)
        
        # Verify tools structure
        logging.info("✅ Implementation tools generated successfully")
        logging.info(f"📊 Development tools: {len(tools.development_tools)}")
        logging.info(f"⚡ Frameworks: {len(tools.frameworks)}")
        logging.info(f"🗄️ Databases: {len(tools.databases)}")
        logging.info(f"☁️ Cloud services: {len(tools.cloud_services)}")
        logging.info(f"🚀 DevOps tools: {len(tools.devops_tools)}")
        logging.info(f"🧪 Testing tools: {len(tools.testing_tools)}")
        logging.info(f"📊 Monitoring tools: {len(tools.monitoring_tools)}")
        logging.info(f"🔒 Security tools: {len(tools.security_tools)}")
        logging.info(f"👥 Collaboration tools: {len(tools.collaboration_tools)}")
        logging.info(f"📚 Learning resources: {len(tools.learning_resources)}")
        
        # Display sample tools
        logging.info("\n📋 Sample Development Tools:")
        for tool in tools.development_tools[:3]:
            logging.info(f"  - {tool['name']}: {tool['description']}")
        
        logging.info("\n⚡ Sample Frameworks:")
        for framework in tools.frameworks[:3]:
            logging.info(f"  - {framework['name']}: {framework['description']}")
        
        logging.info("\n🗄️ Sample Databases:")
        for db in tools.databases[:2]:
            logging.info(f"  - {db['name']}: {db['description']}")
        
        # Test complete SDLC generation
        logging.info("\n🚀 Testing complete SDLC generation with tools...")
        project_description = "A modern web application for project management with user authentication, real-time collaboration, and mobile responsiveness."
        
        result = sdlc_service.generate_complete_sdlc(project_description)
        
        # Verify implementation tools are included
        if 'implementation_tools' in result:
            logging.info("✅ Implementation tools included in complete SDLC")
            tools_data = result['implementation_tools']
            logging.info(f"📊 Total tool categories: {len(tools_data.keys())}")
        else:
            logging.error("❌ Implementation tools not found in complete SDLC")
            return False
        
        # Save results for inspection
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_implementation_tools_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logging.info(f"💾 Results saved to {filename}")
        
        logging.info("🎉 All implementation tools tests completed successfully!")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error testing implementation tools: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_implementation_tools()
    if success:
        print("\n✅ Implementation tools functionality is working correctly!")
    else:
        print("\n❌ Implementation tools functionality has issues!")
        exit(1) 