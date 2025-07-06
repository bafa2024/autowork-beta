#!/usr/bin/env python3
"""
Test script to debug Word and PDF export functionality
"""

import json
import io
from datetime import datetime

# Test data
test_srs = {
    "project_title": "Test Project",
    "overview": "This is a test project overview",
    "scope": "Test project scope",
    "functional_requirements": [
        {"id": "FR1", "description": "Test functional requirement 1"},
        {"id": "FR2", "description": "Test functional requirement 2"}
    ],
    "non_functional_requirements": [
        {"id": "NFR1", "category": "Performance", "description": "Test non-functional requirement 1"}
    ],
    "user_stories": [
        {"id": "US1", "story": "As a user, I want to test the system"}
    ],
    "acceptance_criteria": [
        "Test acceptance criteria 1",
        "Test acceptance criteria 2"
    ],
    "constraints": [
        "Budget constraint: Limited to $5000",
        "Time constraint: Must be completed in 2 weeks"
    ],
    "assumptions": [
        "Users have basic computer literacy",
        "Internet connection is available"
    ]
}

test_design = {
    "architecture_type": "Microservices",
    "components": [
        {"name": "Component 1", "description": "Test component 1"},
        {"name": "Component 2", "description": "Test component 2"}
    ],
    "data_models": [
        {"name": "User", "fields": "id, name, email", "relationships": "has many posts"}
    ],
    "api_endpoints": [
        {"method": "GET", "path": "/api/users", "description": "Get all users"}
    ],
    "technology_stack": {
        "Frontend": ["React", "TypeScript"],
        "Backend": ["Python", "Flask"]
    },
    "security_considerations": [
        "Authentication required",
        "Data encryption"
    ],
    "scalability_plan": "Horizontal scaling with load balancers and database sharding"
}

test_plan = {
    "timeline": {
        "total_hours": 80,
        "total_days": 10,
        "total_weeks": 2
    },
    "phases": [
        {"name": "Phase 1", "hours": 40, "days": 5, "description": "Development phase"}
    ],
    "tasks": [
        {"title": "Task 1", "estimated_hours": 8, "description": "Test task 1"}
    ],
    "milestones": [
        {"name": "Milestone 1", "deliverable": "Test deliverable"}
    ],
    "dependencies": [
        {"task": "Task 1", "depends_on": "Setup environment"}
    ],
    "resource_allocation": {
        "developers_needed": 2,
        "roles": ["Developer", "Tester"]
    }
}

def test_word_export():
    """Test Word document generation"""
    try:
        print("Testing Word document generation...")
        
        # Import the function
        from project_management_api import generate_word_document
        
        # Create test objects
        from auto_sdlc_service import SRSDocument, DesignDocument, ImplementationPlan
        
        srs = SRSDocument(**test_srs)
        design = DesignDocument(**test_design)
        plan = ImplementationPlan(**test_plan)
        
        # Generate document
        buffer = generate_word_document(srs, design, plan, "Test Project")
        
        # Check if buffer has content
        buffer.seek(0)
        content = buffer.read()
        print(f"✅ Word document generated successfully! Size: {len(content)} bytes")
        
        # Save to file for inspection
        with open("test_output.docx", "wb") as f:
            f.write(content)
        print("✅ Word document saved as test_output.docx")
        
        return True
        
    except Exception as e:
        print(f"❌ Word export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_export():
    """Test PDF document generation"""
    try:
        print("Testing PDF document generation...")
        
        # Import the function
        from project_management_api import generate_pdf_document
        
        # Create test objects
        from auto_sdlc_service import SRSDocument, DesignDocument, ImplementationPlan
        
        srs = SRSDocument(**test_srs)
        design = DesignDocument(**test_design)
        plan = ImplementationPlan(**test_plan)
        
        # Generate document
        buffer = generate_pdf_document(srs, design, plan, "Test Project")
        
        # Check if buffer has content
        buffer.seek(0)
        content = buffer.read()
        print(f"✅ PDF document generated successfully! Size: {len(content)} bytes")
        
        # Save to file for inspection
        with open("test_output.pdf", "wb") as f:
            f.write(content)
        print("✅ PDF document saved as test_output.pdf")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoint():
    """Test the API endpoint directly"""
    try:
        print("Testing API endpoint...")
        
        import requests
        
        # Test data
        payload = {
            "srs": test_srs,
            "design": test_design,
            "implementation_plan": test_plan,
            "format": "word",
            "project_title": "Test Project"
        }
        
        # Make request
        response = requests.post(
            "http://127.0.0.1:5001/api/sdlc/export",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            # Save the file
            with open("api_test_output.docx", "wb") as f:
                f.write(response.content)
            print("✅ API Word export successful! Saved as api_test_output.docx")
            return True
        else:
            print(f"❌ API request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Testing Word and PDF Export Functionality ===\n")
    
    # Test Word export
    word_success = test_word_export()
    print()
    
    # Test PDF export
    pdf_success = test_pdf_export()
    print()
    
    # Test API endpoint
    api_success = test_api_endpoint()
    print()
    
    # Summary
    print("=== Test Summary ===")
    print(f"Word Export: {'✅ PASS' if word_success else '❌ FAIL'}")
    print(f"PDF Export: {'✅ PASS' if pdf_success else '❌ FAIL'}")
    print(f"API Endpoint: {'✅ PASS' if api_success else '❌ FAIL'}") 