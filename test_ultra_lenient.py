#!/usr/bin/env python3
"""
Test script for Ultra-Lenient AutoWork Bot
"""

import logging
from autowork_minimal import AutoWorkMinimal

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_ultra_lenient_bot():
    """Test the ultra-lenient bot configuration"""
    try:
        print("🧪 Testing Ultra-Lenient AutoWork Bot...")
        
        # Initialize bot
        bot = AutoWorkMinimal()
        
        # Test configuration
        print("\n📋 Configuration Check:")
        print(f"  Client Filtering: {'Enabled' if bot.config['client_filtering']['enabled'] else 'Disabled'}")
        print(f"  Currency Filtering: {'Enabled' if bot.config['currency_filtering']['enabled'] else 'Disabled'}")
        print(f"  Spam Filtering: {'Enabled' if bot.spam_filter_enabled else 'Disabled'}")
        print(f"  Portfolio Matching: {'Enabled' if bot.config['filtering']['portfolio_matching'] else 'Disabled'}")
        print(f"  Min Profitable Budget: ${bot.config['smart_bidding']['min_profitable_budget']}")
        print(f"  Max Existing Bids: {bot.config['filtering']['skip_projects_with_bids_above']}")
        
        # Test budget requirements
        print("\n💰 Budget Requirements Test:")
        test_currencies = ['USD', 'INR', 'PKR', 'EUR', 'GBP']
        for currency in test_currencies:
            fixed_min = bot.get_minimum_budget_for_currency(currency, 'fixed')
            hourly_min = bot.get_minimum_budget_for_currency(currency, 'hourly')
            print(f"  {currency}: Fixed ${fixed_min:.2f}, Hourly ${hourly_min:.2f}")
        
        # Test project fetching
        print("\n🔍 Testing Project Fetching...")
        projects = bot.get_active_projects(limit=5)
        
        if projects:
            print(f"  ✅ Successfully fetched {len(projects)} projects")
            
            # Test filtering on first project
            if len(projects) > 0:
                first_project = projects[0]
                should_bid, reason = bot.should_bid_on_project(first_project)
                
                print(f"\n🎯 First Project Test:")
                print(f"  Title: {first_project.get('title', 'Unknown')[:50]}...")
                print(f"  Should Bid: {should_bid}")
                print(f"  Reason: {reason}")
                
                if should_bid:
                    print("  ✅ Project passed ultra-lenient filtering!")
                else:
                    print("  ❌ Project still being filtered out")
        else:
            print("  ❌ No projects fetched")
        
        print("\n✅ Ultra-lenient bot test completed!")
        
    except Exception as e:
        print(f"❌ Error testing bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ultra_lenient_bot() 