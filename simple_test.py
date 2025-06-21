#!/usr/bin/env python3
"""
Simple test of the bot with NDA/IP logging - no type hints
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("="*60)
print("SIMPLE BOT TEST - NDA/IP Detection")
print("="*60)

# Check for token
if not os.environ.get('FREELANCER_OAUTH_TOKEN'):
    print("\nToken not found in environment.")
    token = input("Enter your Freelancer OAuth token: ").strip()
    os.environ['FREELANCER_OAUTH_TOKEN'] = token

print("\nThis test will:")
print("1. Fetch active projects")
print("2. Show which ones have NDA/IP requirements")
print("3. Show the first 5 projects in detail")

if input("\nContinue? (y/n): ").lower() != 'y':
    sys.exit()

# Import the bot
from autowork_minimal import AutoWorkMinimal

# Create a simple test wrapper
class TestWrapper:
    def __init__(self):
        self.bot = AutoWorkMinimal()
        self.nda_projects = []
        self.ip_projects = []
        self.elite_projects = []
    
    def run_test(self):
        print("\n🚀 Fetching projects...\n")
        
        # Get projects
        projects = self.bot.get_active_projects(limit=30)
        
        if not projects:
            print("❌ No projects fetched. Check your token.")
            return
        
        print(f"✅ Found {len(projects)} projects\n")
        
        # Analyze projects
        for i, project in enumerate(projects):
            details = self.bot.get_project_details(project)
            
            # Track special projects
            if details['is_elite']:
                self.elite_projects.append(project)
            if details['nda']:
                self.nda_projects.append(project)
            if details['ip_contract']:
                self.ip_projects.append(project)
            
            # Show first 5 in detail
            if i < 5:
                print(f"\n{'='*50}")
                print(f"Project {i+1}: {project['title'][:60]}...")
                print(f"ID: {project['id']}")
                print(f"Budget: ${details['budget'].get('minimum', 0)} - ${details['budget'].get('maximum', 0)}")
                
                if details['is_elite']:
                    print("🌟 ELITE PROJECT")
                    flags = []
                    if details['nda']: flags.append("NDA Required")
                    if details['ip_contract']: flags.append("IP Agreement Required")
                    if details['featured']: flags.append("Featured")
                    if details['sealed']: flags.append("Sealed")
                    if details['urgent']: flags.append("Urgent")
                    print(f"Flags: {', '.join(flags)}")
                
                # Show what bot would do
                bid_amount = self.bot.calculate_bid_amount(details['budget'], details['is_elite'])
                print(f"Bot would bid: ${bid_amount:.2f} with 4-day delivery")
                
                if details['nda']:
                    print("📋 Bot would auto-sign NDA")
                if details['ip_contract']:
                    print("📋 Bot would auto-sign IP Agreement")
        
        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total projects analyzed: {len(projects)}")
        print(f"Elite projects: {len(self.elite_projects)}")
        print(f"Projects requiring NDA: {len(self.nda_projects)}")
        print(f"Projects requiring IP agreement: {len(self.ip_projects)}")
        
        # Show some NDA/IP projects
        if self.nda_projects:
            print(f"\n📋 First 3 NDA Projects:")
            for proj in self.nda_projects[:3]:
                print(f"  - {proj['title'][:60]}...")
                print(f"    https://www.freelancer.com/projects/{proj.get('seo_url', '')}")
        
        if self.ip_projects:
            print(f"\n📋 First 3 IP Agreement Projects:")
            for proj in self.ip_projects[:3]:
                print(f"  - {proj['title'][:60]}...")
                print(f"    https://www.freelancer.com/projects/{proj.get('seo_url', '')}")

# Run the test
try:
    tester = TestWrapper()
    tester.run_test()
    print("\n✅ Test completed successfully!")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()