#!/usr/bin/env python3
"""
Quick fix for API response handling issues
Apply this patch to your autowork_minimal.py
"""

import json
import logging

# Add this method to your AutoWorkMinimal class:

def validate_api_response(self, response, endpoint_name="API"):
    """Validate API response and handle errors gracefully"""
    
    # Check response status
    if response.status_code == 401:
        error_msg = "Authentication failed - Token expired or invalid"
        logging.error(f"{endpoint_name}: {error_msg}")
        logging.error("Please generate a new token at: https://www.freelancer.com/api/docs/")
        if self.redis_client:
            self.redis_client.set('last_error', error_msg)
            self.redis_client.set('bot_status', 'Error - Invalid Token')
        return None
    
    if response.status_code == 429:
        error_msg = "Rate limit exceeded - Too many requests"
        logging.error(f"{endpoint_name}: {error_msg}")
        if self.redis_client:
            self.redis_client.set('last_error', error_msg)
        return None
    
    if response.status_code != 200:
        error_msg = f"HTTP {response.status_code} error"
        logging.error(f"{endpoint_name}: {error_msg}")
        logging.error(f"Response: {response.text[:500]}")
        if self.redis_client:
            self.redis_client.set('last_error', error_msg)
        return None
    
    # Try to parse JSON
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        logging.error(f"{endpoint_name}: Invalid JSON response - {e}")
        logging.error(f"Raw response: {response.text[:500]}")
        if self.redis_client:
            self.redis_client.set('last_error', 'Invalid JSON response')
        return None
    
    # Validate response structure
    if not isinstance(data, dict):
        logging.error(f"{endpoint_name}: Response is not a dictionary")
        logging.error(f"Type: {type(data)}, Content: {str(data)[:500]}")
        return None
    
    # Check for API errors in response
    if data.get('status') == 'error':
        error_msg = data.get('message', 'Unknown API error')
        logging.error(f"{endpoint_name}: API Error - {error_msg}")
        if self.redis_client:
            self.redis_client.set('last_error', error_msg)
        return None
    
    return data


# Replace your get_active_projects method with this improved version:

def get_active_projects_fixed(self, limit: int = 50) -> List[Dict]:
    """Fetch active projects with better error handling"""
    try:
        endpoint = f"{self.api_base}/projects/0.1/projects/active"
        params = {
            "limit": limit,
            "job_details": "true",
            "full_description": "true",
            "upgrade_details": "true",
            "compact": "false"
        }
        
        logging.debug(f"Fetching projects from: {endpoint}")
        logging.debug(f"Headers: {list(self.headers.keys())}")
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        
        # Use the validation method
        data = self.validate_api_response(response, "Projects API")
        if data is None:
            return []
        
        # Safely extract projects
        result = data.get("result", {})
        if not isinstance(result, dict):
            logging.error(f"Invalid result structure: {type(result)}")
            return []
        
        projects = result.get("projects", [])
        if not isinstance(projects, list):
            logging.error(f"Projects is not a list: {type(projects)}")
            return []
        
        # Filter out any non-dict items
        valid_projects = [p for p in projects if isinstance(p, dict)]
        
        if len(valid_projects) < len(projects):
            logging.warning(f"Filtered out {len(projects) - len(valid_projects)} invalid projects")
        
        # Process with smart bidding if enabled
        if self.config.get('smart_bidding', {}).get('enabled', True):
            projects_with_priority = []
            
            for project in valid_projects:
                try:
                    priority_score, _ = self.calculate_bid_priority(project)
                    projects_with_priority.append((priority_score, project))
                except Exception as e:
                    logging.warning(f"Error calculating priority for project: {e}")
                    continue
            
            # Sort by priority
            projects_with_priority.sort(key=lambda x: x[0], reverse=True)
            sorted_projects = [p[1] for p in projects_with_priority]
            
            # Count elite projects safely
            elite_count = 0
            for p in sorted_projects:
                try:
                    if self.is_elite_project(p):
                        elite_count += 1
                except:
                    pass
            
            logging.info(f"✓ Fetched {len(sorted_projects)} valid projects ({elite_count} elite)")
            return sorted_projects
        else:
            logging.info(f"✓ Fetched {len(valid_projects)} valid projects")
            return valid_projects
            
    except requests.exceptions.Timeout:
        logging.error("Request timeout - Freelancer API may be slow")
        return []
    except requests.exceptions.ConnectionError:
        logging.error("Connection error - Check internet connection")
        return []
    except Exception as e:
        logging.error(f"Unexpected error in get_active_projects: {e}")
        logging.error(f"Error type: {type(e).__name__}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        return []


# Also add this method to check token validity on startup:

def verify_token_on_startup(self):
    """Verify token is valid before starting bot"""
    try:
        logging.info("Verifying token validity...")
        
        # Test with user endpoint
        response = requests.get(
            f"{self.api_base}/users/0.1/users/{self.user_id}",
            headers=self.headers
        )
        
        if response.status_code == 401:
            logging.error("="*60)
            logging.error("TOKEN AUTHENTICATION FAILED!")
            logging.error("Your token is expired or invalid.")
            logging.error("Please get a new token from: https://www.freelancer.com/api/docs/")
            logging.error("="*60)
            
            if self.redis_client:
                self.redis_client.set('bot_status', 'Error - Invalid Token')
                self.redis_client.set('last_error', 'Token authentication failed')
            
            return False
        
        if response.status_code == 200:
            data = response.json()
            username = data.get('result', {}).get('username', 'Unknown')
            logging.info(f"✅ Token valid - Logged in as: {username}")
            return True
        else:
            logging.error(f"Token verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Error verifying token: {e}")
        return False