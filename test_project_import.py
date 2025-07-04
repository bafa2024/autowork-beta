#!/usr/bin/env python3
"""
Test script to manually import a specific project by ID
"""

import os
import sys
import requests
import json

def test_project_import(project_id: int):
    """Test importing a specific project by ID"""
    
    print(f"Testing import of project {project_id}...")
    
    # Test the API endpoint
    try:
        response = requests.post(
            "http://127.0.0.1:5001/api/projects/import",
            json={"freelancer_project_id": project_id},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Successfully imported project {project_id}")
                print(f"Title: {data.get('project', {}).get('title', 'Unknown')}")
                return True
            else:
                print(f"❌ Failed to import project: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_bids_endpoint():
    """Test the bids endpoint to see if we can find awarded projects"""
    
    print("Testing bids endpoint...")
    
    # Get token from environment
    token = os.environ.get('FREELANCER_OAUTH_TOKEN')
    user_id = os.environ.get('FREELANCER_USER_ID', '45214417')
    
    if not token:
        print("❌ FREELANCER_OAUTH_TOKEN not found in environment")
        return
    
    headers = {
        "Freelancer-OAuth-V1": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        # Get user's bids
        response = requests.get(
            f"https://www.freelancer.com/api/projects/0.1/bids",
            headers=headers,
            params={
                "bidders[]": user_id,
                "limit": 50,
                "compact": "false"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            bids = data.get('result', {}).get('bids', [])
            print(f"✅ Found {len(bids)} bids")
            
            # Find awarded bids
            awarded_bids = [bid for bid in bids if bid.get('awarded') == True]
            print(f"✅ Found {len(awarded_bids)} awarded bids")
            
            if awarded_bids:
                print("\nAwarded projects:")
                for bid in awarded_bids:
                    project_id = bid.get('project_id')
                    project_title = bid.get('project', {}).get('title', 'Unknown')
                    print(f"  - Project {project_id}: {project_title}")
                    
                    # Offer to import
                    choice = input(f"\nImport project {project_id}? (y/n): ").lower().strip()
                    if choice == 'y':
                        test_project_import(project_id)
            else:
                print("❌ No awarded projects found")
                
        else:
            print(f"❌ Failed to fetch bids: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("=== Project Import Test ===\n")
    
    # Check if API is running
    try:
        response = requests.get("http://127.0.0.1:5001/api/dashboard")
        if response.status_code == 200:
            print("✅ Project Management API is running")
        else:
            print("❌ Project Management API is not responding")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Project Management API: {e}")
        print("Make sure to run: python project_management_api.py")
        return
    
    print("\n1. Test bids endpoint to find awarded projects")
    print("2. Import specific project by ID")
    print("3. Exit")
    
    choice = input("\nChoose option (1-3): ").strip()
    
    if choice == "1":
        test_bids_endpoint()
    elif choice == "2":
        project_id = input("Enter project ID: ").strip()
        try:
            test_project_import(int(project_id))
        except ValueError:
            print("❌ Invalid project ID")
    elif choice == "3":
        print("Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 