#!/usr/bin/env python3
"""
Test Freelancer API connection
"""

import os
import urllib.request
import json

def test_api():
    """Test API connection"""
    token = os.environ.get('FREELANCER_OAUTH_TOKEN')
    
    if not token:
        print("❌ FREELANCER_OAUTH_TOKEN not set!")
        return False
    
    print("Testing Freelancer API connection...")
    
    try:
        request = urllib.request.Request(
            'https://www.freelancer.com/api/users/0.1/self',
            headers={'Freelancer-OAuth-V1': token}
        )
        
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read())
            
        if 'result' in data:
            user = data['result']
            print(f"✅ Connected as: {user.get('username', 'Unknown')}")
            print(f"✅ User ID: {user.get('id', 'Unknown')}")
            return True
        else:
            print("❌ Invalid response from API")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_api()