#!/usr/bin/env python3
"""
Dry run test - Shows what the bot would do without actually bidding
"""

import os
import sys
from datetime import datetime

# Set environment for dry run
os.environ['DRY_RUN'] = 'true'

# Set up your token
if not os.environ.get('FREELANCER_OAUTH_TOKEN'):
    print("Please set your Freelancer OAuth token")
    token = input("Token: ").strip()
    os.environ['FREELANCER_OAUTH_TOKEN'] = token

print("="*60)
print("DRY RUN MODE - No actual bids will be placed")
print("="*60)
print("\nThis will:")
print("1. Fetch active projects")
print("2. Show which ones have NDA/IP requirements")
print("3. Show what the bot WOULD do (without actually doing it)")
print("\nStarting in 3 seconds...")

import time
time.sleep(3)

# Import the bot
from autowork_minimal import AutoWorkMinimal

# Monkey patch the bid placement to prevent actual bidding
original_place_bid = AutoWorkMinimal.place_bid

def mock_place_bid(self, project):
    """Mock bid placement for dry run"""
    project_id = project["id"]
    details = self.get_project_details(project)
    
    print(f"\n{'='*60}")
    print(f"🎯 WOULD BID ON: {project['title'][:50]}...")
    print(f"   Project ID: {project_id}")
    print(f"   Budget: ${details['budget'].get('minimum', 0)} - ${details['budget'].get('maximum', 0)}")
    
    if details['is_elite']:
        print("   🌟 ELITE PROJECT")
        flags = []
        if details['nda']: flags.append("NDA Required")
        if details['ip_contract']: flags.append("IP Agreement Required")
        if details['featured']: flags.append("Featured")
        if details['sealed']: flags.append("Sealed")
        print(f"   Flags: {', '.join(flags)}")
    
    # Calculate what bid would be
    bid_amount = self.calculate_bid_amount(details['budget'], details['is_elite'])
    print(f"   Would bid: ${bid_amount:.2f} with 4-day delivery")
    
    if details.get('nda'):
        print("   📋 Would auto-sign NDA")
    
    if details.get('ip_contract'):
        print("   📋 Would auto-sign IP Agreement")
    
    # Mark as processed so we don't see it again
    self.processed_projects.add(project_id)
    self.bid_count += 1
    if details['is_elite']:
        self.elite_bid_count += 1
    
    return True

# Replace the method
AutoWorkMinimal.place_bid = mock_place_bid

# Also mock the NDA/IP signing
def mock_check_and_sign_nda(self, project_id):
    print(f"   🔍 Would check NDA status for project {project_id}")
    print(f"   ✅ Would auto-sign if unsigned")
    return True

def mock_check_and_sign_ip(self, project_id):
    print(f"   🔍 Would check IP agreement status for project {project_id}")
    print(f"   ✅ Would auto-sign if unsigned")
    return True

AutoWorkMinimal.check_and_sign_nda = mock_check_and_sign_nda
AutoWorkMinimal.check_and_sign_ip_agreement = mock_check_and_sign_ip

# Run the bot
try:
    print("\n🚀 Starting dry run...\n")
    bot = AutoWorkMinimal()
    
    # Just run one cycle for testing
    projects = bot.get_active_projects(limit=20)
    
    elite_count = 0
    nda_count = 0
    ip_count = 0
    
    for project in projects:
        details = bot.get_project_details(project)
        if details['is_elite']:
            elite_count += 1
        if details['nda']:
            nda_count += 1
        if details['ip_contract']:
            ip_count += 1
        
        # Process first 5 projects in dry run
        if bot.bid_count < 5:
            bot.place_bid(project)
    
    # Summary
    print(f"\n{'='*60}")
    print("DRY RUN SUMMARY")
    print(f"{'='*60}")
    print(f"Total projects fetched: {len(projects)}")
    print(f"Elite projects: {elite_count}")
    print(f"Projects requiring NDA: {nda_count}")
    print(f"Projects requiring IP agreement: {ip_count}")
    print(f"Would have placed {bot.bid_count} bids")
    print(f"\n✅ Dry run complete - no actual bids were placed")
    
except KeyboardInterrupt:
    print("\n\nDry run stopped by user")
except Exception as e:
    print(f"\nError during dry run: {e}")
    import traceback
    traceback.print_exc()