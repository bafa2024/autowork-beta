#!/usr/bin/env python3
"""
Test script for contest feature - Safe testing without actual submissions
"""

import os
import sys
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_contest_feature():
    """Test contest functionality"""
    print("="*60)
    print("🏆 CONTEST FEATURE TEST")
    print("="*60)
    
    # Check if we have the required files
    if not os.path.exists('contest_handler.py'):
        print("❌ contest_handler.py not found!")
        print("Please make sure you have the full contest_handler.py file")
        return
    
    # Import the bot
    from autowork_minimal import AutoWorkMinimal
    
    print("\n1️⃣ Initializing bot with contest feature...")
    
    # Create bot instance
    bot = AutoWorkMinimal()
    
    # Check if contests are enabled
    print(f"\nContests enabled in config: {bot.contests_enabled}")
    
    if not bot.contests_enabled:
        print("❌ Contests are disabled in bot_config.json")
        print("\nTo enable contests, update bot_config.json:")
        print("""
  "contests": {
    "enabled": true,
    "min_prize": 100,
    ...
  }
        """)
        return
    
    if not bot.contest_handler:
        print("❌ Contest handler not initialized")
        return
    
    print("✅ Contest handler initialized successfully")
    
    # Test 2: Fetch active contests
    print("\n2️⃣ Fetching active contests...")
    contests = bot.contest_handler.get_active_contests(limit=10)
    
    if not contests:
        print("❌ No active contests found")
        print("This could mean:")
        print("- No contests are currently active on Freelancer")
        print("- API authentication issue")
        print("- Network issue")
        return
    
    print(f"✅ Found {len(contests)} active contests")
    
    # Test 3: Analyze contests
    print("\n3️⃣ Analyzing contests...")
    print("-" * 60)
    
    eligible_contests = []
    
    for i, contest in enumerate(contests[:5], 1):
        contest_id = contest.get('id')
        title = contest.get('title', 'Unknown')[:50]
        prize = contest.get('prize', 0)
        contest_type = contest.get('type', {}).get('name', 'Unknown')
        entry_count = contest.get('entry_count', 0)
        
        print(f"\nContest {i}: {title}...")
        print(f"  ID: {contest_id}")
        print(f"  Type: {contest_type}")
        print(f"  Prize: ${prize}")
        print(f"  Current entries: {entry_count}")
        
        # Check eligibility
        should_enter, reason = bot.contest_handler.should_enter_contest(contest, bot.config)
        
        if should_enter:
            print(f"  ✅ ELIGIBLE: {reason}")
            eligible_contests.append(contest)
        else:
            print(f"  ❌ NOT ELIGIBLE: {reason}")
    
    # Test 4: Test entry creation (without submission)
    print("\n4️⃣ Testing entry creation (DRY RUN - No submission)...")
    print("-" * 60)
    
    if eligible_contests:
        test_contest = eligible_contests[0]
        print(f"\nTesting with contest: {test_contest.get('title', '')[:50]}...")
        print(f"Contest type: {test_contest.get('type', {}).get('name', 'Unknown')}")
        
        # Create entry data
        entry_data = bot.contest_handler.create_contest_entry(test_contest, bot.config)
        
        if entry_data:
            print("\n✅ Entry data created successfully:")
            print(f"Description preview: {entry_data.get('description', '')[:200]}...")
            
            if 'suggestions' in entry_data:
                print(f"Name suggestions: {entry_data['suggestions']}")
            
            print("\n⚠️  This is a DRY RUN - No actual submission")
            print("In production mode, the bot would submit this entry")
        else:
            print("❌ Failed to create entry data")
    else:
        print("No eligible contests found for testing")
    
    # Test 5: Show configuration
    print("\n5️⃣ Current Contest Configuration:")
    print("-" * 60)
    contest_config = bot.config.get('contests', {})
    print(f"Minimum prize: ${contest_config.get('min_prize', 100)}")
    print(f"Max existing entries: {contest_config.get('max_existing_entries', 50)}")
    print(f"Min hours remaining: {contest_config.get('min_hours_remaining', 24)}")
    print(f"Allowed types: {', '.join(contest_config.get('allowed_types', ['All'])[:3])}...")
    
    # Test 6: Contest statistics
    print("\n6️⃣ Contest Statistics:")
    print("-" * 60)
    summary = bot.contest_handler.get_contest_summary()
    print(f"Total contests entered: {summary['total_entered']}")
    print(f"Contests won: {summary['total_wins']}")
    print(f"Win rate: {summary['win_rate']:.1f}%")
    print(f"Total prize money: ${summary['total_prize_money']}")

def test_manual_contest_process():
    """Test the contest process step by step"""
    print("\n" + "="*60)
    print("🎯 MANUAL CONTEST PROCESS TEST")
    print("="*60)
    
    from autowork_minimal import AutoWorkMinimal
    
    bot = AutoWorkMinimal()
    
    if not bot.contests_enabled or not bot.contest_handler:
        print("❌ Contests not enabled")
        return
    
    print("\nThis will walk through the contest process step by step.")
    print("You can stop at any point by pressing Ctrl+C\n")
    
    # Process contests (same as bot does)
    bot.process_contests()
    
    print("\n✅ Contest process test completed!")

def test_contest_types():
    """Show what contest types are supported"""
    print("\n" + "="*60)
    print("📋 SUPPORTED CONTEST TYPES")
    print("="*60)
    
    contest_types = {
        "Logo Design": "Upload logo files (PNG, AI, PSD)",
        "Naming": "Submit 1-5 name suggestions",
        "Article Writing": "Submit written content",
        "Graphic Design": "Upload design files",
        "Website Design": "Upload mockups or links",
        "T-shirt Design": "Upload design files",
        "Business Card": "Upload card designs",
        "Banner Design": "Upload banner designs"
    }
    
    print("\nThe bot can automatically enter these contest types:")
    for ctype, description in contest_types.items():
        print(f"\n{ctype}:")
        print(f"  → {description}")
    
    print("\n⚠️  Note: For design contests, the bot prepares entries but")
    print("   doesn't upload files. You'd need to add file upload")
    print("   functionality for full automation.")

def safe_test_mode():
    """Run bot in safe test mode - no actual submissions"""
    print("\n" + "="*60)
    print("🛡️ SAFE TEST MODE - View Only")
    print("="*60)
    
    # Temporarily override the submit function
    from autowork_minimal import AutoWorkMinimal
    from contest_handler import ContestHandler
    
    # Save original method
    original_submit = ContestHandler.submit_contest_entry
    
    # Override with test version
    def test_submit(self, contest_id, entry_data):
        print(f"\n🔍 TEST MODE: Would submit to contest {contest_id}")
        print(f"   Entry description: {entry_data.get('description', '')[:100]}...")
        if 'suggestions' in entry_data:
            print(f"   Name suggestions: {entry_data['suggestions']}")
        print("   ✅ TEST MODE: No actual submission")
        return True
    
    # Replace method
    ContestHandler.submit_contest_entry = test_submit
    
    try:
        # Create bot and process contests
        bot = AutoWorkMinimal()
        if bot.contests_enabled and bot.contest_handler:
            bot.process_contests()
        else:
            print("Contests not enabled")
    finally:
        # Restore original method
        ContestHandler.submit_contest_entry = original_submit
    
    print("\n✅ Safe test completed - no entries were submitted")

def check_contest_config():
    """Check and validate contest configuration"""
    print("\n" + "="*60)
    print("⚙️ CONTEST CONFIGURATION CHECK")
    print("="*60)
    
    config_file = "bot_config.json"
    
    if not os.path.exists(config_file):
        print(f"❌ {config_file} not found!")
        return
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    if 'contests' not in config:
        print("❌ No contest configuration found!")
        print("\nAdd this to your bot_config.json:")
        print("""
  "contests": {
    "enabled": true,
    "min_prize": 100,
    "max_existing_entries": 50,
    "min_hours_remaining": 24,
    "allowed_types": ["Logo Design", "Naming", "Article Writing"],
    "skills": ["Logo Design", "Graphic Design", "Content Writing"]
  }
        """)
        return
    
    contest_config = config['contests']
    print("✅ Contest configuration found:")
    print(json.dumps(contest_config, indent=2))
    
    # Validate settings
    if not contest_config.get('enabled', False):
        print("\n⚠️  Contests are DISABLED. Set 'enabled': true to activate")
    
    if contest_config.get('min_prize', 0) < 50:
        print("\n⚠️  Warning: min_prize is very low. Consider setting to at least $100")

if __name__ == "__main__":
    print("Contest Feature Test Suite")
    print("========================\n")
    
    print("Select test option:")
    print("1. Basic contest feature test")
    print("2. Manual contest process test") 
    print("3. Safe test mode (no submissions)")
    print("4. Check contest configuration")
    print("5. Show supported contest types")
    print("6. Run all tests")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice == '1':
        test_contest_feature()
    elif choice == '2':
        test_manual_contest_process()
    elif choice == '3':
        safe_test_mode()
    elif choice == '4':
        check_contest_config()
    elif choice == '5':
        test_contest_types()
    elif choice == '6':
        check_contest_config()
        test_contest_types()
        test_contest_feature()
    else:
        print("Invalid choice")
    
    print("\n✅ Test completed!")