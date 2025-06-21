#!/usr/bin/env python3
"""
Validate Freelancer OAuth token and API access
"""

import os
import sys
import requests
import json
from datetime import datetime

def validate_token():
    """Test if the Freelancer OAuth token is valid"""
    
    # Get token from environment
    token = os.environ.get('FREELANCER_OAUTH_TOKEN')
    if not token:
        print("❌ FREELANCER_OAUTH_TOKEN not found in environment")
        print("Set it with: export FREELANCER_OAUTH_TOKEN='your_token_here'")
        return False
    
    print(f"🔑 Token found: {token[:20]}...")
    
    # Test endpoints
    headers = {
        "Freelancer-OAuth-V1": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    user_id = os.environ.get('FREELANCER_USER_ID', '45214417')
    
    print("\n📋 Testing API endpoints...")
    
    # Test 1: User info
    print("\n1. Testing user info endpoint...")
    try:
        response = requests.get(
            f"https://www.freelancer.com/api/users/0.1/users/{user_id}",
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            user = data.get('result', {})
            print(f"   ✅ Success! User: {user.get('username', 'Unknown')}")
            print(f"   Display name: {user.get('display_name', 'Unknown')}")
            print(f"   Member since: {user.get('registration_date', 'Unknown')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Active projects
    print("\n2. Testing active projects endpoint...")
    try:
        response = requests.get(
            "https://www.freelancer.com/api/projects/0.1/projects/active",
            headers=headers,
            params={"limit": 5}
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if response is valid JSON dict
            if isinstance(data, dict):
                projects = data.get('result', {}).get('projects', [])
                print(f"   ✅ Success! Found {len(projects)} projects")
                
                if projects:
                    print(f"   First project: {projects[0].get('title', 'Unknown')[:50]}...")
            else:
                print(f"   ❌ Unexpected response type: {type(data)}")
                print(f"   Response: {str(data)[:200]}")
                return False
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 3: My bids
    print("\n3. Testing my bids endpoint...")
    try:
        response = requests.get(
            "https://www.freelancer.com/api/projects/0.1/bids",
            headers=headers,
            params={"bidders[]": user_id, "limit": 5}
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            bids = data.get('result', {}).get('bids', [])
            print(f"   ✅ Success! Found {len(bids)} recent bids")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ Token validation complete - API access working!")
    return True


def check_rate_limits():
    """Check API rate limit status"""
    token = os.environ.get('FREELANCER_OAUTH_TOKEN')
    if not token:
        return
    
    headers = {
        "Freelancer-OAuth-V1": token,
        "User-Agent": "Mozilla/5.0"
    }
    
    print("\n📊 Checking rate limits...")
    
    # Make a simple request
    response = requests.get(
        "https://www.freelancer.com/api/projects/0.1/projects/active?limit=1",
        headers=headers
    )
    
    # Check rate limit headers
    rate_headers = {
        'X-RateLimit-Limit': 'Requests allowed per period',
        'X-RateLimit-Remaining': 'Requests remaining',
        'X-RateLimit-Reset': 'Reset time'
    }
    
    for header, desc in rate_headers.items():
        value = response.headers.get(header)
        if value:
            print(f"   {header}: {value} ({desc})")
    
    if 'X-RateLimit-Remaining' in response.headers:
        remaining = int(response.headers['X-RateLimit-Remaining'])
        if remaining < 100:
            print(f"   ⚠️  Warning: Only {remaining} requests remaining!")


if __name__ == "__main__":
    print("="*60)
    print("🔍 Freelancer API Token Validator")
    print("="*60)
    
    if validate_token():
        check_rate_limits()
        print("\n✅ Your token is valid and working!")
    else:
        print("\n❌ Token validation failed!")
        print("\nPossible issues:")
        print("1. Token has expired - generate a new one")
        print("2. Token is incorrect - check for typos")
        print("3. API is down - try again later")
        print("\nTo get a new token:")
        print("1. Go to https://www.freelancer.com/api/docs/")
        print("2. Click 'Get OAuth Token'")
        print("3. Copy the token and update your environment variable")