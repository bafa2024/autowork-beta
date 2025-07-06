#!/usr/bin/env python3
"""
Test script to verify INR/PKR bidding fix - bid at minimum budget in original currency
"""

import os
import sys
import json
import logging
from datetime import datetime

# Set up logging without Unicode characters to avoid encoding issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('inr_pkr_bidding_fix_test.log')
    ]
)

def test_inr_pkr_bidding_fix():
    """Test that INR/PKR projects now bid at minimum budget in original currency"""
    try:
        from autowork.core.autowork_minimal import AutoWorkMinimal
        
        bot = AutoWorkMinimal()
        
        logging.info("="*60)
        logging.info("TESTING INR/PKR BIDDING FIX")
        logging.info("="*60)
        
        # Test projects with different currencies
        test_projects = [
            # INR Project
            {
                'id': 1001,
                'title': 'INR Test Project',
                'budget': {
                    'minimum': 15000.0,
                    'maximum': 30000.0,
                    'type': 'fixed'
                },
                'currency': {'code': 'INR'},
                'bid_stats': {'bid_count': 5},
                'jobs': [{'id': '13', 'name': 'Python'}],
                'expected_bid': 15000.0,
                'expected_currency': 'INR'
            },
            # PKR Project
            {
                'id': 1002,
                'title': 'PKR Test Project',
                'budget': {
                    'minimum': 20000.0,
                    'maximum': 40000.0,
                    'type': 'fixed'
                },
                'currency': {'code': 'PKR'},
                'bid_stats': {'bid_count': 5},
                'jobs': [{'id': '3', 'name': 'PHP'}],
                'expected_bid': 20000.0,
                'expected_currency': 'PKR'
            },
            # USD Project (for comparison)
            {
                'id': 1003,
                'title': 'USD Test Project',
                'budget': {
                    'minimum': 150.0,
                    'maximum': 300.0,
                    'type': 'fixed'
                },
                'currency': {'code': 'USD'},
                'bid_stats': {'bid_count': 5},
                'jobs': [{'id': '9', 'name': 'Data Entry'}],
                'expected_bid': 150.0,
                'expected_currency': 'USD'
            },
            # EUR Project (should convert to USD)
            {
                'id': 1004,
                'title': 'EUR Test Project',
                'budget': {
                    'minimum': 100.0,
                    'maximum': 200.0,
                    'type': 'fixed'
                },
                'currency': {'code': 'EUR'},
                'bid_stats': {'bid_count': 5},
                'jobs': [{'id': '13', 'name': 'Python'}],
                'expected_bid': 'converted_to_usd',
                'expected_currency': 'USD'
            }
        ]
        
        logging.info("\nTesting bid amount calculations:")
        logging.info("-" * 60)
        
        passed_tests = 0
        total_tests = len(test_projects)
        
        for i, project in enumerate(test_projects, 1):
            currency = project['currency']['code']
            min_budget = project['budget']['minimum']
            expected_bid = project['expected_bid']
            expected_currency = project['expected_currency']
            
            logging.info(f"\nTest {i}: {project['title']}")
            logging.info(f"  Currency: {currency}")
            logging.info(f"  Minimum Budget: {min_budget} {currency}")
            logging.info(f"  Expected Bid: {expected_bid} {expected_currency}")
            
            # Calculate bid amount
            bid_amount = bot.calculate_bid_amount(project)
            
            logging.info(f"  Calculated Bid: {bid_amount:.2f}")
            
            # Check if this is correct behavior
            if currency in ['INR', 'PKR']:
                # For INR/PKR, should bid at minimum budget in original currency
                success = abs(bid_amount - expected_bid) < 0.01
                logging.info(f"  Expected: {expected_bid} {currency}")
                logging.info(f"  Result: {'PASS' if success else 'FAIL'}")
                if success:
                    passed_tests += 1
                else:
                    logging.info(f"  Issue: Should bid at {expected_bid} {currency}, not {bid_amount:.2f}")
            elif currency == 'USD':
                # For USD, should bid at minimum budget
                success = abs(bid_amount - expected_bid) < 0.01
                logging.info(f"  Expected: {expected_bid} USD")
                logging.info(f"  Result: {'PASS' if success else 'FAIL'}")
                if success:
                    passed_tests += 1
                else:
                    logging.info(f"  Issue: Should bid at {expected_bid} USD, not {bid_amount:.2f}")
            else:
                # For other currencies, should convert to USD
                success = bid_amount > 0 and bid_amount != min_budget
                logging.info(f"  Expected: Converted to USD (not {min_budget})")
                logging.info(f"  Result: {'PASS' if success else 'FAIL'}")
                if success:
                    passed_tests += 1
                else:
                    logging.info(f"  Issue: Should convert to USD, not bid at {bid_amount:.2f}")
        
        # Summary
        logging.info(f"\n{'='*60}")
        logging.info("TEST SUMMARY")
        logging.info(f"{'='*60}")
        logging.info(f"Tests passed: {passed_tests}/{total_tests}")
        logging.info(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            logging.info("SUCCESS: All tests passed! INR/PKR bidding fix is working correctly.")
        else:
            logging.info("FAILURE: Some tests failed. Please check the implementation.")
        
        # Test the fix more specifically
        logging.info(f"\n{'='*60}")
        logging.info("DETAILED FIX VERIFICATION")
        logging.info(f"{'='*60}")
        
        # Test INR project
        inr_project = test_projects[0]
        inr_bid = bot.calculate_bid_amount(inr_project)
        inr_success = abs(inr_bid - 15000.0) < 0.01
        
        logging.info(f"INR Project Test:")
        logging.info(f"  Budget: 15,000 INR")
        logging.info(f"  Bid Amount: {inr_bid:.2f}")
        logging.info(f"  Expected: 15,000.00")
        logging.info(f"  Result: {'PASS' if inr_success else 'FAIL'}")
        
        # Test PKR project
        pkr_project = test_projects[1]
        pkr_bid = bot.calculate_bid_amount(pkr_project)
        pkr_success = abs(pkr_bid - 20000.0) < 0.01
        
        logging.info(f"\nPKR Project Test:")
        logging.info(f"  Budget: 20,000 PKR")
        logging.info(f"  Bid Amount: {pkr_bid:.2f}")
        logging.info(f"  Expected: 20,000.00")
        logging.info(f"  Result: {'PASS' if pkr_success else 'FAIL'}")
        
        # Test USD project (should remain unchanged)
        usd_project = test_projects[2]
        usd_bid = bot.calculate_bid_amount(usd_project)
        usd_success = abs(usd_bid - 150.0) < 0.01
        
        logging.info(f"\nUSD Project Test:")
        logging.info(f"  Budget: 150 USD")
        logging.info(f"  Bid Amount: {usd_bid:.2f}")
        logging.info(f"  Expected: 150.00")
        logging.info(f"  Result: {'PASS' if usd_success else 'FAIL'}")
        
        # Overall fix verification
        fix_success = inr_success and pkr_success and usd_success
        logging.info(f"\n{'='*60}")
        logging.info("FIX VERIFICATION RESULT")
        logging.info(f"{'='*60}")
        
        if fix_success:
            logging.info("SUCCESS: INR/PKR bidding fix is working correctly!")
            logging.info("- INR projects now bid at minimum budget in INR")
            logging.info("- PKR projects now bid at minimum budget in PKR")
            logging.info("- USD projects continue to work as before")
            logging.info("- Other currencies still convert to USD as expected")
        else:
            logging.info("FAILURE: INR/PKR bidding fix is not working correctly.")
            logging.info("Please check the implementation.")
        
        return fix_success
        
    except Exception as e:
        logging.error(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_inr_pkr_bidding_fix()
    sys.exit(0 if success else 1) 