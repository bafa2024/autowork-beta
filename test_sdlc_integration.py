#!/usr/bin/env python3
"""
Test script for SDLC integration
"""

import requests
import json

def test_sdlc_analysis():
    """Test the SDLC analysis endpoint"""
    
    print("Testing SDLC Analysis Integration...")
    
    # Test data
    test_data = {
        "project_title": "Task Management Web App",
        "project_description": """
        I need a web application for managing tasks and projects. The system should have:
        - User registration and login
        - Task creation and management
        - Project organization
        - Team collaboration features
        - File upload and sharing
        - Real-time notifications
        - Mobile-responsive design
        
        Technologies preferred: React for frontend, Node.js for backend, MongoDB for database.
        The project should be completed within 3 months.
        """,
        "budget": {
            "minimum": 5000,
            "maximum": 10000
        },
        "ai_provider": "openai"
    }
    
    try:
        # Test the analyze endpoint
        print("1. Testing SDLC analyze endpoint...")
        response = requests.post(
            "http://127.0.0.1:5001/api/sdlc/analyze",
            headers={"Content-Type": "application/json"},
            json=test_data
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ SDLC Analysis successful!")
                print(f"Project Type: {data['summary']['project_type']}")
                print(f"Complexity: {data['summary']['complexity']}")
                print(f"Estimated Hours: {data['summary']['estimated_hours']}")
                print(f"Technologies: {', '.join(data['summary']['technologies'])}")
                print(f"Key Features: {len(data['summary']['key_features'])} features identified")
                print(f"Risks: {len(data['summary']['risks'])} risks identified")
                
                # Test export functionality
                print("\n2. Testing SDLC export endpoint...")
                export_response = requests.post(
                    "http://127.0.0.1:5001/api/sdlc/export",
                    headers={"Content-Type": "application/json"},
                    json={
                        "srs": data['srs'],
                        "design": data['design'],
                        "implementation_plan": data['implementation_plan'],
                        "format": "markdown"
                    }
                )
                
                if export_response.status_code == 200:
                    export_data = export_response.json()
                    if export_data.get('success'):
                        print("✅ SDLC Export successful!")
                        print(f"Exported files: {export_data['files']}")
                    else:
                        print(f"❌ Export failed: {export_data.get('error')}")
                else:
                    print(f"❌ Export request failed: {export_response.status_code}")
                
            else:
                print(f"❌ Analysis failed: {data.get('error')}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure it's running on http://127.0.0.1:5001")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_dashboard_access():
    """Test if the dashboard is accessible"""
    
    print("\nTesting Dashboard Access...")
    
    try:
        response = requests.get("http://127.0.0.1:5001/")
        print(f"Dashboard Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard is accessible")
            print("You can now:")
            print("1. Open http://127.0.0.1:5001 in your browser")
            print("2. Click on 'SDLC Analysis' in the navigation")
            print("3. Enter a project description and click 'Analyze Project'")
        else:
            print("❌ Dashboard not accessible")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to dashboard. Make sure the API server is running.")

if __name__ == "__main__":
    test_sdlc_analysis()
    test_dashboard_access() 