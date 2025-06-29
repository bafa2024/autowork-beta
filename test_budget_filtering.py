#!/usr/bin/env python3
"""
Test script for project type-based budget filtering
"""

import json
import logging
from autowork_minimal import AutoWorkMinimal

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_budget_filtering():
    """Test the project type-based budget filtering features"""
    
    print("🧪 Testing Project Type-Based Budget Filtering")
    print("=" * 60)
    
    # Initialize bot
    try:
        bot = AutoWorkMinimal()
        print("✅ Bot initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize bot: {e}")
        return
    
    # Test different currencies and project types
    test_cases = [
        # Fixed projects
        {'currency': 'USD', 'type': 'fixed', 'budget': 200, 'expected': False},
        {'currency': 'USD', 'type': 'fixed', 'budget': 300, 'expected': True},
        {'currency': 'CAD', 'type': 'fixed', 'budget': 200, 'expected': False},
        {'currency': 'CAD', 'type': 'fixed', 'budget': 300, 'expected': True},
        {'currency': 'INR', 'type': 'fixed', 'budget': 15000, 'expected': False},
        {'currency': 'INR', 'type': 'fixed', 'budget': 25000, 'expected': True},
        
        # Hourly projects
        {'currency': 'USD', 'type': 'hourly', 'budget': 15, 'expected': False},
        {'currency': 'USD', 'type': 'hourly', 'budget': 25, 'expected': True},
        {'currency': 'CAD', 'type': 'hourly', 'budget': 15, 'expected': False},
        {'currency': 'CAD', 'type': 'hourly', 'budget': 25, 'expected': True},
        {'currency': 'INR', 'type': 'hourly', 'budget': 1200, 'expected': False},
        {'currency': 'INR', 'type': 'hourly', 'budget': 2000, 'expected': True},
    ]
    
    print(f"\n📊 Budget Filtering Test Results:")
    print(f"{'Currency':<8} {'Type':<8} {'Budget':<10} {'Min Required':<12} {'Pass':<6} {'Status'}")
    print("-" * 70)
    
    for test_case in test_cases:
        currency = test_case['currency']
        project_type = test_case['type']
        budget = test_case['budget']
        expected = test_case['expected']
        
        # Get minimum required for this currency and project type
        min_required = bot.get_minimum_budget_for_currency(currency, project_type)
        
        # Check if budget passes
        passes = budget >= min_required
        status = "✅ PASS" if passes else "❌ FAIL"
        
        print(f"{currency:<8} {project_type:<8} {budget:<10} {min_required:<12} {passes:<6} {status}")
    
    # Test with sample project data
    print(f"\n🔍 Sample Project Testing:")
    
    # Fixed project test
    fixed_project = {
        'id': 12345,
        'title': 'Build a website',
        'budget': {
            'type': 'fixed',
            'minimum': 200,
            'maximum': 500
        },
        'currency': {
            'code': 'USD'
        },
        'bid_stats': {'bid_count': 5},
        'owner_id': 67890
    }
    
    should_bid, reason = bot.should_bid_on_project(fixed_project)
    print(f"Fixed Project (USD 200): {'✅ PASS' if should_bid else '❌ FAIL'} - {reason}")
    
    # Hourly project test
    hourly_project = {
        'id': 12346,
        'title': 'Hourly web development',
        'budget': {
            'type': 'hourly',
            'minimum': 15,
            'maximum': 30
        },
        'currency': {
            'code': 'USD'
        },
        'bid_stats': {'bid_count': 3},
        'owner_id': 67891
    }
    
    should_bid, reason = bot.should_bid_on_project(hourly_project)
    print(f"Hourly Project (USD 15): {'✅ PASS' if should_bid else '❌ FAIL'} - {reason}")
    
    # Test with different currencies
    print(f"\n🌍 Multi-Currency Testing:")
    
    currencies_to_test = ['USD', 'CAD', 'EUR', 'INR', 'PKR']
    
    for currency in currencies_to_test:
        # Fixed project
        fixed_min = bot.get_minimum_budget_for_currency(currency, 'fixed')
        print(f"Fixed {currency}: {fixed_min}")
        
        # Hourly project
        hourly_min = bot.get_minimum_budget_for_currency(currency, 'hourly')
        print(f"Hourly {currency}: {hourly_min}")
        print()
    
    print(f"🎯 Test completed!")

if __name__ == "__main__":
    test_budget_filtering() 