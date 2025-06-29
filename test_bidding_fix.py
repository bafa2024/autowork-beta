#!/usr/bin/env python3
"""
Test script to verify the bot's filtering is now lenient enough to bid on projects
"""

import json
import logging
from autowork_minimal import AutoWorkMinimal

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_filtering():
    """Test the bot's filtering logic with sample projects"""
    
    # Initialize bot
    bot = AutoWorkMinimal()
    
    # Sample projects with different budgets and currencies
    test_projects = [
        {
            'id': 1,
            'title': 'Simple Python script',
            'budget': {'minimum': 100, 'maximum': 200, 'type': 'fixed'},
            'currency': {'code': 'USD'},
            'bid_stats': {'bid_count': 5},
            'owner_id': 12345,
            'jobs': [{'id': '13', 'name': 'Python'}],
            'description': 'Need a simple Python script'
        },
        {
            'id': 2,
            'title': 'Website development',
            'budget': {'minimum': 50, 'maximum': 150, 'type': 'fixed'},
            'currency': {'code': 'CAD'},
            'bid_stats': {'bid_count': 3},
            'owner_id': 12346,
            'jobs': [{'id': '3', 'name': 'PHP'}],
            'description': 'Need a website built'
        },
        {
            'id': 3,
            'title': 'Data entry work',
            'budget': {'minimum': 10, 'maximum': 20, 'type': 'hourly'},
            'currency': {'code': 'USD'},
            'bid_stats': {'bid_count': 8},
            'owner_id': 12347,
            'jobs': [{'id': '9', 'name': 'Data Entry'}],
            'description': 'Need data entry work'
        },
        {
            'id': 4,
            'title': 'Web scraping project',
            'budget': {'minimum': 2000, 'maximum': 5000, 'type': 'fixed'},
            'currency': {'code': 'INR'},
            'bid_stats': {'bid_count': 2},
            'owner_id': 12348,
            'jobs': [{'id': '17', 'name': 'Web Scraping'}],
            'description': 'Need web scraping done'
        }
    ]
    
    print("="*60)
    print("TESTING BOT FILTERING LOGIC")
    print("="*60)
    
    for i, project in enumerate(test_projects, 1):
        print(f"\n--- Testing Project {i} ---")
        print(f"Title: {project['title']}")
        print(f"Budget: {project['budget']['minimum']} {project['currency']['code']} ({project['budget']['type']})")
        print(f"Bids: {project['bid_stats']['bid_count']}")
        
        # Test should_bid_on_project
        should_bid, reason = bot.should_bid_on_project(project)
        
        if should_bid:
            print(f"✅ RESULT: SHOULD BID - {reason}")
            
            # Test bid calculation
            bid_amount = bot.calculate_competitive_bid(project)
            print(f"   💰 Bid amount: ${bid_amount:.2f}")
            
            # Test message selection
            message = bot.select_bid_message(project)
            print(f"   📝 Message length: {len(message)} characters")
            
        else:
            print(f"❌ RESULT: SHOULD NOT BID - {reason}")
        
        print("-" * 40)
    
    print("\n" + "="*60)
    print("FILTERING TEST COMPLETE")
    print("="*60)

def test_minimum_budgets():
    """Test minimum budget calculations"""
    
    bot = AutoWorkMinimal()
    
    print("\n" + "="*60)
    print("TESTING MINIMUM BUDGET CALCULATIONS")
    print("="*60)
    
    currencies = ['USD', 'CAD', 'EUR', 'INR', 'PKR']
    project_types = ['fixed', 'hourly']
    
    for currency in currencies:
        for project_type in project_types:
            min_budget = bot.get_minimum_budget_for_currency(currency, project_type)
            print(f"{currency} ({project_type}): {min_budget:.2f}")
    
    print("="*60)

if __name__ == "__main__":
    test_filtering()
    test_minimum_budgets() 