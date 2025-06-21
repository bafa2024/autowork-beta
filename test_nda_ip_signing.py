#!/usr/bin/env python3
"""
Test script for NDA/IP auto-signing functionality
Run this locally to test the bot's ability to detect and sign agreements
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional  # Add proper imports

# Enhanced logging for testing
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('nda_ip_test.log')
    ]
)

class NDAIPTester:
    def __init__(self):
        self.token = self.load_token()
        self.user_id = os.environ.get('FREELANCER_USER_ID', '45214417')
        self.api_base = "https://www.freelancer.com/api"
        self.headers = {
            "Freelancer-OAuth-V1": self.token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        self.nda_projects = []
        self.ip_projects = []
        self.elite_projects = []
        
        logging.info("="*60)
        logging.info("NDA/IP AUTO-SIGNING TEST STARTED")
        logging.info("="*60)
        logging.info(f"User ID: {self.user_id}")
        logging.info(f"Token: {self.token[:20]}...")

    def load_token(self) -> str:
        """Load token from environment or .env file"""
        token = os.environ.get('FREELANCER_OAUTH_TOKEN')
        
        if token:
            return token.strip()
        
        # Try .env file
        if os.path.exists('.env'):
            try:
                from dotenv import load_dotenv
                load_dotenv()
                token = os.environ.get('FREELANCER_OAUTH_TOKEN')
                if token:
                    return token.strip()
            except ImportError:
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('FREELANCER_OAUTH_TOKEN='):
                            token = line.split('=', 1)[1].strip()
                            if token:
                                return token
        
        # Ask for token
        print("Token not found in environment.")
        token = input("Enter your Freelancer OAuth token: ").strip()
        return token

    def get_project_details(self, project: Dict) -> Dict:
        """Extract detailed information about a project"""
        upgrades = project.get('upgrades', {})
        
        details = {
            'id': project['id'],
            'title': project['title'],
            'featured': upgrades.get('featured', False),
            'sealed': upgrades.get('sealed', False),
            'nda': upgrades.get('NDA', False),
            'ip_contract': upgrades.get('ip_contract', False),
            'non_compete': upgrades.get('non_compete', False),
            'urgent': upgrades.get('urgent', False),
            'qualified': upgrades.get('qualified', False),
            'budget': project.get('budget', {}),
            'url': f"https://www.freelancer.com/projects/{project['seo_url']}"
        }
        
        return details

    def check_nda_status(self, project_id: int) -> Dict:
        """Check NDA status for a project"""
        try:
            endpoint = f"{self.api_base}/projects/0.1/projects/{project_id}/nda"
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                status = result.get('status', 'unknown')
                
                logging.info(f"   NDA Status: {status}")
                logging.debug(f"   NDA Response: {json.dumps(result, indent=2)}")
                
                return {
                    'exists': True,
                    'status': status,
                    'data': result
                }
            elif response.status_code == 404:
                logging.info("   No NDA required for this project")
                return {
                    'exists': False,
                    'status': 'not_required'
                }
            else:
                logging.error(f"   Error checking NDA: {response.status_code}")
                return {
                    'exists': False,
                    'status': 'error',
                    'error': response.text
                }
                
        except Exception as e:
            logging.error(f"   Exception checking NDA: {e}")
            return {
                'exists': False,
                'status': 'error',
                'error': str(e)
            }

    def check_ip_status(self, project_id: int) -> Dict:
        """Check IP agreement status for a project"""
        try:
            endpoint = f"{self.api_base}/projects/0.1/projects/{project_id}/ip_contract"
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                status = result.get('status', 'unknown')
                
                logging.info(f"   IP Agreement Status: {status}")
                logging.debug(f"   IP Response: {json.dumps(result, indent=2)}")
                
                return {
                    'exists': True,
                    'status': status,
                    'data': result
                }
            elif response.status_code == 404:
                logging.info("   No IP agreement required for this project")
                return {
                    'exists': False,
                    'status': 'not_required'
                }
            else:
                logging.error(f"   Error checking IP agreement: {response.status_code}")
                return {
                    'exists': False,
                    'status': 'error',
                    'error': response.text
                }
                
        except Exception as e:
            logging.error(f"   Exception checking IP agreement: {e}")
            return {
                'exists': False,
                'status': 'error',
                'error': str(e)
            }

    def sign_nda(self, project_id: int) -> bool:
        """Attempt to sign NDA for a project"""
        try:
            logging.info(f"   🖊️  Attempting to sign NDA...")
            
            endpoint = f"{self.api_base}/projects/0.1/projects/{project_id}/nda/sign"
            response = requests.post(endpoint, headers=self.headers, json={})
            
            if response.status_code in [200, 201]:
                logging.info(f"   ✅ Successfully signed NDA!")
                return True
            else:
                logging.error(f"   ❌ Failed to sign NDA: {response.status_code}")
                logging.error(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"   ❌ Exception signing NDA: {e}")
            return False

    def sign_ip_agreement(self, project_id: int) -> bool:
        """Attempt to sign IP agreement for a project"""
        try:
            logging.info(f"   🖊️  Attempting to sign IP agreement...")
            
            endpoint = f"{self.api_base}/projects/0.1/projects/{project_id}/ip_contract/sign"
            response = requests.post(endpoint, headers=self.headers, json={})
            
            if response.status_code in [200, 201]:
                logging.info(f"   ✅ Successfully signed IP agreement!")
                return True
            else:
                logging.error(f"   ❌ Failed to sign IP agreement: {response.status_code}")
                logging.error(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"   ❌ Exception signing IP agreement: {e}")
            return False

    def test_single_project(self, project: Dict):
        """Test NDA/IP detection and signing for a single project"""
        details = self.get_project_details(project)
        project_id = details['id']
        
        logging.info(f"\n{'='*60}")
        logging.info(f"Testing Project: {details['title'][:50]}...")
        logging.info(f"Project ID: {project_id}")
        logging.info(f"URL: {details['url']}")
        
        # Log project flags
        flags = []
        if details['featured']: flags.append("Featured")
        if details['sealed']: flags.append("Sealed")
        if details['nda']: flags.append("NDA")
        if details['ip_contract']: flags.append("IP Contract")
        if details['urgent']: flags.append("Urgent")
        if details['qualified']: flags.append("Qualified")
        
        if flags:
            logging.info(f"Flags: {', '.join(flags)}")
            self.elite_projects.append(details)
        
        # Test NDA
        if details['nda']:
            logging.info("\n📋 PROJECT HAS NDA FLAG - Checking NDA status...")
            self.nda_projects.append(details)
            
            nda_status = self.check_nda_status(project_id)
            
            if nda_status['exists'] and nda_status['status'] == 'unsigned':
                logging.info("   NDA is UNSIGNED - Will attempt to sign")
                
                # Simulate what the bot would do
                if input("   Sign this NDA? (y/n): ").lower() == 'y':
                    success = self.sign_nda(project_id)
                    if success:
                        # Verify it was signed
                        new_status = self.check_nda_status(project_id)
                        logging.info(f"   Verification: NDA is now {new_status['status']}")
        
        # Test IP Agreement
        if details['ip_contract']:
            logging.info("\n📋 PROJECT HAS IP CONTRACT FLAG - Checking IP agreement status...")
            self.ip_projects.append(details)
            
            ip_status = self.check_ip_status(project_id)
            
            if ip_status['exists'] and ip_status['status'] == 'unsigned':
                logging.info("   IP agreement is UNSIGNED - Will attempt to sign")
                
                # Simulate what the bot would do
                if input("   Sign this IP agreement? (y/n): ").lower() == 'y':
                    success = self.sign_ip_agreement(project_id)
                    if success:
                        # Verify it was signed
                        new_status = self.check_ip_status(project_id)
                        logging.info(f"   Verification: IP agreement is now {new_status['status']}")

    def run_test(self, limit: int = 20, test_mode: str = 'detect'):
        """
        Run the test
        test_mode: 'detect' - only detect NDA/IP projects
                  'interactive' - ask before signing
                  'auto' - automatically sign (like the bot would)
        """
        logging.info(f"\nFetching {limit} active projects...")
        logging.info(f"Test mode: {test_mode}")
        
        try:
            # Fetch projects
            endpoint = f"{self.api_base}/projects/0.1/projects/active"
            params = {
                "limit": limit,
                "job_details": "true",
                "upgrade_details": "true",
                "compact": "false"
            }
            
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                projects = data.get("result", {}).get("projects", [])
                
                logging.info(f"✓ Fetched {len(projects)} projects")
                
                # Test each project
                for project in projects:
                    self.test_single_project(project)
                    time.sleep(1)  # Small delay between tests
                
                # Summary
                self.print_summary()
                
            else:
                logging.error(f"Failed to fetch projects: {response.status_code}")
                
        except Exception as e:
            logging.error(f"Error in test: {e}")

    def print_summary(self):
        """Print test summary"""
        logging.info("\n" + "="*60)
        logging.info("TEST SUMMARY")
        logging.info("="*60)
        
        logging.info(f"\n📊 Elite Projects Found: {len(self.elite_projects)}")
        for proj in self.elite_projects[:5]:  # Show first 5
            logging.info(f"   - {proj['title'][:50]}...")
        
        logging.info(f"\n📋 Projects with NDA: {len(self.nda_projects)}")
        for proj in self.nda_projects[:5]:
            logging.info(f"   - {proj['title'][:50]}...")
            logging.info(f"     URL: {proj['url']}")
        
        logging.info(f"\n📋 Projects with IP Agreement: {len(self.ip_projects)}")
        for proj in self.ip_projects[:5]:
            logging.info(f"   - {proj['title'][:50]}...")
            logging.info(f"     URL: {proj['url']}")
        
        logging.info(f"\n✅ Test completed. Check nda_ip_test.log for full details.")


def main():
    """Main test function"""
    print("NDA/IP Auto-signing Test Script")
    print("================================")
    print("\nThis script will:")
    print("1. Fetch active projects")
    print("2. Identify projects with NDA/IP requirements")
    print("3. Check the status of agreements")
    print("4. Optionally test signing them")
    print("\n⚠️  WARNING: Signing NDAs/IP agreements is legally binding!")
    
    if input("\nContinue? (y/n): ").lower() != 'y':
        print("Test cancelled.")
        return
    
    # Create tester
    tester = NDAIPTester()
    
    # Choose test mode
    print("\nSelect test mode:")
    print("1. Detect only (find NDA/IP projects but don't sign)")
    print("2. Interactive (ask before signing each)")
    print("3. Auto-sign (simulate bot behavior - CAREFUL!)")
    
    mode_choice = input("\nChoice (1-3): ").strip()
    
    if mode_choice == '1':
        mode = 'detect'
    elif mode_choice == '2':
        mode = 'interactive'
    elif mode_choice == '3':
        print("\n⚠️  AUTO-SIGN MODE - This will automatically sign agreements!")
        if input("Are you SURE? (type 'yes' to confirm): ").lower() != 'yes':
            print("Cancelled.")
            return
        mode = 'auto'
    else:
        print("Invalid choice.")
        return
    
    # Run test
    limit = int(input("\nHow many projects to test? (default 20): ") or "20")
    tester.run_test(limit=limit, test_mode=mode)


if __name__ == "__main__":
    main()