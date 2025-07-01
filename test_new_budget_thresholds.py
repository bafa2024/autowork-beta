#!/usr/bin/env python3
"""
Test script to verify the new minimum budget thresholds
"""

from autowork_minimal import AutoWorkMinimal

def test_new_budget_thresholds():
    """Test that the new minimum budget thresholds work correctly"""
    
    print("="*60)
    print("TESTING NEW MINIMUM BUDGET THRESHOLDS")
    print("="*60)
    print("New thresholds: $100 USD / ₹12000 INR / PKR 12000")
    print("="*60)
    
    # Initialize bot
    bot = AutoWorkMinimal()
    
    # Test projects with different budgets and currencies
    test_projects = [
        # USD Tests
        {
            'id': 1,
            'title': 'USD Project - Below threshold',
            'budget': {'minimum': 50, 'maximum': 100, 'type': 'fixed'},
            'currency': {'code': 'USD'},
            'bid_stats': {'bid_count': 5},
            'jobs': [{'id': '13', 'name': 'Python'}],
            'expected': False,
            'reason': 'Should reject $50 (below $100 minimum)'
        },
        {
            'id': 2,
            'title': 'USD Project - At threshold',
            'budget': {'minimum': 100, 'maximum': 200, 'type': 'fixed'},
            'currency': {'code': 'USD'},
            'bid_stats': {'bid_count': 5},
            'jobs': [{'id': '3', 'name': 'PHP'}],
            'expected': True,
            'reason': 'Should accept $100 (exactly minimum)'
        },
        {
            'id': 3,
            'title': 'USD Project - Above threshold',
            'budget': {'minimum': 150, 'maximum': 300, 'type': 'fixed'},
            'currency': {'code': 'USD'},
            'bid_stats': {'bid_count': 5},
            'jobs': [{'id': '9', 'name': 'Data Entry'}],
            'expected': True,
            'reason': 'Should accept $150 (above minimum)'
        },
        
        # INR Tests
        {
            'id': 4,
            'title': 'INR Project - Below threshold',
            'budget': {'minimum': 8000, 'maximum': 15000, 'type': 'fixed'},
            'currency': {'code': 'INR'},
            'bid_stats': {'bid_count': 5},
            'jobs': [{'id': '17', 'name': 'Web Scraping'}],
            'expected': False,
            'reason': 'Should reject ₹8000 (below ₹12000 minimum)'
        },
        {
            'id': 5,
            'title': 'INR Project - At threshold',
            'budget': {'minimum': 12000, 'maximum': 25000, 'type': 'fixed'},
            'currency': {'code': 'INR'},
            'bid_stats': {'bid_count': 5},
            'jobs': [{'id': '17', 'name': 'Web Scraping'}],
            'expected': True,
            'reason': 'Should accept ₹12000 (exactly minimum)'
        },
        {
            'id': 6,
            'title': 'INR Project - Above threshold',
            'budget': {'minimum': 20000, 'maximum': 50000, 'type': 'fixed'},
            'currency': {'code': 'INR'},
            'bid_stats': {'bid_count': 5},
            'jobs': [{'id': '17', 'name': 'Web Scraping'}],
            'expected': True,
            'reason': 'Should accept ₹20000 (above minimum)'
        },
        
        # PKR Tests
        {
            'id': 7,
            'title': 'PKR Project - Below threshold',
            'budget': {'minimum': 8000, 'maximum': 15000, 'type': 'fixed'},
            'currency': {'code': 'PKR'},
            'bid_stats': {'bid_count': 5},
            'jobs': [{'id': '17', 'name': 'Web Scraping'}],
            'expected': False,
            'reason': 'Should reject PKR 8000 (below PKR 12000 minimum)'
        },
        {
            'id': 8,
            'title': 'PKR Project - At threshold',
            'budget': {'minimum': 12000, 'maximum': 25000, 'type': 'fixed'},
            'currency': {'code': 'PKR'},
            'bid_stats': {'bid_count': 5},
            'jobs': [{'id': '17', 'name': 'Web Scraping'}],
            'expected': True,
            'reason': 'Should accept PKR 12000 (exactly minimum)'
        },
        {
            'id': 9,
            'title': 'PKR Project - Above threshold',
            'budget': {'minimum': 20000, 'maximum': 50000, 'type': 'fixed'},
            'currency': {'code': 'PKR'},
            'bid_stats': {'bid_count': 5},
            'jobs': [{'id': '17', 'name': 'Web Scraping'}],
            'expected': True,
            'reason': 'Should accept PKR 20000 (above minimum)'
        },
        
        # Other Currency Tests
        {
            'id': 10,
            'title': 'EUR Project - Below threshold',
            'budget': {'minimum': 80, 'maximum': 150, 'type': 'fixed'},
            'currency': {'code': 'EUR'},
            'bid_stats': {'bid_count': 5},
            'jobs': [{'id': '13', 'name': 'Python'}],
            'expected': False,
            'reason': 'Should reject EUR 80 (below $100 USD equivalent)'
        },
        {
            'id': 11,
            'title': 'EUR Project - Above threshold',
            'budget': {'minimum': 120, 'maximum': 250, 'type': 'fixed'},
            'currency': {'code': 'EUR'},
            'bid_stats': {'bid_count': 5},
            'jobs': [{'id': '13', 'name': 'Python'}],
            'expected': True,
            'reason': 'Should accept EUR 120 (above $100 USD equivalent)'
        }
    ]
    
    print("\nTesting each project:")
    print("-" * 60)
    
    passed_tests = 0
    total_tests = len(test_projects)
    
    for i, project in enumerate(test_projects, 1):
        print(f"\nTest {i}: {project['title']}")
        print(f"  Budget: {project['budget']['minimum']} {project['currency']['code']}")
        print(f"  Expected: {'ACCEPT' if project['expected'] else 'REJECT'}")
        print(f"  Reason: {project['reason']}")
        
        # Test should_bid_on_project
        should_bid, reason = bot.should_bid_on_project(project)
        
        # Check result
        if should_bid == project['expected']:
            status = "✅ PASS"
            passed_tests += 1
        else:
            status = "❌ FAIL"
        
        print(f"  Result: {status}")
        print(f"  Actual: {'ACCEPT' if should_bid else 'REJECT'} - {reason}")
        
        # Calculate bid amount if accepted
        if should_bid:
            bid_amount = bot.calculate_bid_amount(project)
            print(f"  Bid amount: {bid_amount:.2f}")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests passed: {passed_tests}/{total_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("✅ All tests passed! New budget thresholds are working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    # Configuration check
    print(f"\nConfiguration Check:")
    config = bot.config
    print(f"  min_profitable_budget: ${config['smart_bidding']['min_profitable_budget']}")
    print(f"  inr_minimum_budget: ₹{config['currency_filtering']['inr_minimum_budget']}")
    print(f"  pkr_minimum_budget: PKR {config['currency_filtering']['pkr_minimum_budget']}")

if __name__ == "__main__":
    test_new_budget_thresholds() 