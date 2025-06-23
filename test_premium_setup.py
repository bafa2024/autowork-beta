#!/usr/bin/env python3
"""
Test script to verify premium project setup
"""

import os
import sys
import json
from datetime import datetime

# Test imports
print("Testing imports...")
try:
    from autowork_minimal import AutoWorkMinimal
    print("✅ AutoWorkMinimal imported")
except ImportError as e:
    print(f"❌ Failed to import AutoWorkMinimal: {e}")
    sys.exit(1)

try:
    from spam_filter import SpamFilter
    print("✅ SpamFilter imported")
except ImportError as e:
    print(f"❌ Failed to import SpamFilter: {e}")

try:
    from premium_filter import PremiumProjectFilter
    print("✅ PremiumProjectFilter imported")
except ImportError as e:
    print(f"❌ Failed to import PremiumProjectFilter: {e}")

print("\n" + "="*60)
print("TESTING PREMIUM PROJECT SETUP")
print("="*60)

# Initialize bot
print("\nInitializing bot...")
try:
    bot = AutoWorkMinimal()
    print("✅ Bot initialized successfully")
    
    # Check configurations
    print("\nChecking configurations:")
    print(f"  Spam filter enabled: {bot.spam_filter_enabled}")
    print(f"  Premium mode enabled: {bot.premium_mode}")
    print(f"  Min budget: ${bot.config['smart_bidding']['min_profitable_budget']}")
    print(f"  Max bids threshold: {bot.config['filtering']['skip_projects_with_bids_above']}")
    
    if bot.premium_mode:
        print(f"  Min quality score: {bot.config.get('quality_filters', {}).get('min_quality_score', 50)}")
        print(f"  Preferred budget: ${bot.config.get('quality_filters', {}).get('preferred_budget_range', {}).get('min', 500)}-${bot.config.get('quality_filters', {}).get('preferred_budget_range', {}).get('max', 5000)}")
    
except Exception as e:
    print(f"❌ Failed to initialize bot: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test with sample projects
print("\n" + "="*60)
print("TESTING PROJECT FILTERING")
print("="*60)

test_projects = [
    {
        'id': 1,
        'title': 'Build Enterprise SaaS Platform with React and Node.js',
        'description': """We are looking for an experienced full-stack developer to build a comprehensive SaaS platform. 
        
        Requirements:
        - Modern React frontend with TypeScript
        - Node.js/Express backend with microservices architecture
        - PostgreSQL database with proper schema design
        - AWS deployment with auto-scaling
        - Integration with Stripe for payments
        - Real-time features using WebSockets
        - Comprehensive testing suite
        
        Please share your portfolio and similar projects. Long-term opportunity for the right candidate.""",
        'budget': {'minimum': 5000, 'maximum': 10000, 'type': 'fixed'},
        'bid_stats': {'bid_count': 5},
        'upgrades': {'featured': True, 'NDA': True},
        'owner': {
            'reputation': {'entire_history': {'overall': 4.8, 'projects': 25}},
            'status': {'payment_verified': True}
        },
        'jobs': [{'id': 323, 'name': 'React.js'}, {'id': 335, 'name': 'Node.js'}]
    },
    {
        'id': 2,
        'title': 'Simple Data Entry - Copy Paste Work $500/day',
        'description': 'Easy work from home. Just copy paste data. Contact me on WhatsApp +1234567890',
        'budget': {'minimum': 500, 'maximum': 1000, 'type': 'fixed'},
        'bid_stats': {'bid_count': 2},
        'upgrades': {},
        'owner': {'reputation': {'entire_history': {'overall': 0, 'projects': 0}}},
        'jobs': [{'id': 9, 'name': 'Data Entry'}]
    },
    {
        'id': 3,
        'title': 'WordPress Bug Fix',
        'description': 'Need to fix a small bug on my WordPress site. Should take 30 minutes.',
        'budget': {'minimum': 30, 'maximum': 50, 'type': 'fixed'},
        'bid_stats': {'bid_count': 45},
        'upgrades': {},
        'owner': {'reputation': {'entire_history': {'overall': 4.2, 'projects': 10}}},
        'jobs': [{'id': 94, 'name': 'WordPress'}]
    },
    {
        'id': 4,
        'title': 'AI-Powered Mobile App Development',
        'description': """Looking for a senior mobile developer to create an AI-powered fitness app.
        
        Tech stack:
        - React Native for cross-platform development
        - Python backend with TensorFlow integration
        - Real-time pose detection using ML
        - Cloud deployment on AWS
        
        This is a 3-month project with possibility of extension. NDA required.""",
        'budget': {'minimum': 8000, 'maximum': 15000, 'type': 'fixed'},
        'bid_stats': {'bid_count': 12},
        'upgrades': {'NDA': True, 'ip_contract': True},
        'owner': {
            'reputation': {'entire_history': {'overall': 4.9, 'projects': 50}},
            'status': {'payment_verified': True}
        },
        'jobs': [{'name': 'React Native'}, {'name': 'Machine Learning'}]
    }
]

# Test each project
for i, project in enumerate(test_projects, 1):
    print(f"\n{'='*40}")
    print(f"Test Project {i}: {project['title'][:50]}...")
    print(f"Budget: ${project['budget']['minimum']} - ${project['budget']['maximum']}")
    print(f"Bids: {project['bid_stats']['bid_count']}")
    
    # Test spam filter
    if bot.spam_filter:
        is_spam, spam_reasons = bot.spam_filter.is_spam(project)
        if is_spam:
            print(f"🚫 SPAM DETECTED: {', '.join(spam_reasons[:2])}")
            continue
        else:
            print("✅ Not spam")
    
    # Test premium filter
    if bot.premium_filter and bot.premium_mode:
        is_premium, quality_score, factors = bot.premium_filter.is_premium_project(project)
        print(f"💎 Quality Score: {quality_score}/100")
        print(f"   Factors: {json.dumps(factors, indent=2)}")
        
        if is_premium:
            print("⭐ PREMIUM PROJECT")
        else:
            print("📊 Regular project")
    
    # Test should bid
    should_bid, reason = bot.should_bid_on_project(project)
    print(f"\nShould bid? {'YES' if should_bid else 'NO'} - {reason}")
    
    # Test priority
    if should_bid:
        priority, priority_reasons = bot.calculate_bid_priority(project)
        print(f"Priority Score: {priority} - {priority_reasons}")
        
        # Test bid message selection
        message = bot.select_bid_message(project, bot.is_elite_project(project))
        print(f"\nBid Message Preview:")
        print(f"{message[:200]}...")

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print(f"✅ Bot initialized: {'Yes' if 'bot' in locals() else 'No'}")
print(f"✅ Spam filter working: {'Yes' if bot.spam_filter else 'No'}")
print(f"✅ Premium filter working: {'Yes' if bot.premium_filter else 'No'}")
print(f"✅ Premium mode enabled: {'Yes' if bot.premium_mode else 'No'}")

# Check for required files
print("\nFile Check:")
files_to_check = [
    'bot_config.json',
    'spam_filter.py',
    'premium_filter.py',
    'bid_messages.json',
    'bid_messages_premium.json',
    'skills_map.json'
]

for file in files_to_check:
    exists = os.path.exists(file)
    print(f"  {file}: {'✅ Found' if exists else '❌ Missing'}")

print("\n✅ Premium setup test complete!")