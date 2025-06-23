#!/usr/bin/env python3
"""
Test script for contest functionality
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_contest_handler():
    """Test the contest handler"""
    print("="*60)
    print("🏆 CONTEST HANDLER TEST")
    print("="*60)
    
    # Check token
    token = os.environ.get('FREELANCER_OAUTH_TOKEN')
    if not token:
        print("Token not found!")
        token = input("Enter your Freelancer OAuth token: ").strip()
        os.environ['FREELANCER_OAUTH_TOKEN'] = token
    
    user_id = os.environ.get('FREELANCER_USER_ID', '45214417')
    
    # Import contest handler
    from contest_handler import ContestHandler
    
    # Create handler
    print("\nInitializing contest handler...")
    handler = ContestHandler(token, user_id)
    
    # Fetch contests
    print("\nFetching active contests...")
    contests = handler.get_active_contests(limit=20)
    
    if not contests:
        print("❌ No contests found")
        return
    
    print(f"✅ Found {len(contests)} active contests\n")
    
    # Analyze contests
    contest_types = {}
    prize_ranges = {'<$100': 0, '$100-$500': 0, '$500-$1000': 0, '>$1000': 0}
    
    for i, contest in enumerate(contests[:10]):  # Analyze first 10
        contest_id = contest.get('id')
        title = contest.get('title', 'Unknown')
        prize = contest.get('prize', 0)
        contest_type = contest.get('type', {}).get('name', 'Unknown')
        entry_count = contest.get('entry_count', 0)
        
        # Count types
        contest_types[contest_type] = contest_types.get(contest_type, 0) + 1
        
        # Count prize ranges
        if prize < 100:
            prize_ranges['<$100'] += 1
        elif prize < 500:
            prize_ranges['$100-$500'] += 1
        elif prize < 1000:
            prize_ranges['$500-$1000'] += 1
        else:
            prize_ranges['>$1000'] += 1
        
        # Display contest info
        print(f"\nContest {i+1}: {title[:50]}...")
        print(f"  ID: {contest_id}")
        print(f"  Type: {contest_type}")
        print(f"  Prize: ${prize}")
        print(f"  Entries: {entry_count}")
        print(f"  URL: https://www.freelancer.com/contest/{contest_id}")
        
        # Check eligibility
        config = {
            'contests': {
                'min_prize': 100,
                'max_existing_entries': 50,
                'min_hours_remaining': 24,
                'allowed_types': []  # Allow all for testing
            }
        }
        
        should_enter, reason = handler.should_enter_contest(contest, config)
        print(f"  Eligible: {'✅ YES' if should_enter else '❌ NO'} - {reason}")
        
        # Show what entry would look like
        if should_enter and i < 3:  # Show for first 3 eligible
            entry_data = handler.create_contest_entry(contest, config)
            print(f"  Entry preview:")
            print(f"    Description: {entry_data.get('description', '')[:100]}...")
            if 'suggestions' in entry_data:
                print(f"    Name suggestions: {', '.join(entry_data['suggestions'][:3])}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 CONTEST ANALYSIS SUMMARY")
    print("="*60)
    
    print("\nContest Types:")
    for ctype, count in sorted(contest_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ctype}: {count}")
    
    print("\nPrize Distribution:")
    for range_name, count in prize_ranges.items():
        print(f"  {range_name}: {count}")
    
    # Test entry submission (dry run)
    print("\n" + "="*60)
    print("TEST ENTRY SUBMISSION (DRY RUN)")
    print("="*60)
    
    eligible_contests = []
    for contest in contests[:5]:
        should_enter, _ = handler.should_enter_contest(contest, config)
        if should_enter:
            eligible_contests.append(contest)
    
    if eligible_contests:
        test_contest = eligible_contests[0]
        print(f"\nWould enter contest: {test_contest.get('title', '')[:50]}...")
        print(f"Prize: ${test_contest.get('prize', 0)}")
        
        if input("\nTest entry submission? (y/n): ").lower() == 'y':
            entry_data = handler.create_contest_entry(test_contest, config)
            print("\nEntry data prepared:")
            print(f"Description: {entry_data.get('description', '')}")
            
            # Don't actually submit in test mode
            print("\n⚠️  Test mode - not actually submitting")
            print("In production, this would submit the entry")

def test_contest_types():
    """Show different contest types and requirements"""
    print("\n" + "="*60)
    print("📋 CONTEST TYPES ON FREELANCER")
    print("="*60)
    
    contest_types = {
        "Logo Design": {
            "description": "Create logo designs",
            "requirements": "Need to upload logo files (PNG, AI, PSD)",
            "entry_type": "File upload"
        },
        "Naming": {
            "description": "Suggest names for businesses/products",
            "requirements": "Submit 1-5 name suggestions with explanations",
            "entry_type": "Text entries"
        },
        "Article Writing": {
            "description": "Write articles on given topics",
            "requirements": "Submit written content (500-2000 words typical)",
            "entry_type": "Text content"
        },
        "Website Design": {
            "description": "Design website mockups",
            "requirements": "Upload design files or mockup links",
            "entry_type": "File upload or links"
        },
        "T-shirt Design": {
            "description": "Create t-shirt designs",
            "requirements": "Upload design files with mockups",
            "entry_type": "File upload"
        }
    }
    
    for ctype, info in contest_types.items():
        print(f"\n{ctype}:")
        print(f"  Description: {info['description']}")
        print(f"  Requirements: {info['requirements']}")
        print(f"  Entry type: {info['entry_type']}")

if __name__ == "__main__":
    print("Contest Feature Test Suite")
    print("=" * 60)
    
    # Test contest handler
    test_contest_handler()
    
    # Show contest types
    test_contest_types()
    
    print("\n✅ Contest test complete!")