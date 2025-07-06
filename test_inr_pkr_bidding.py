#!/usr/bin/env python3
"""
Test script to verify INR/PKR bidding at minimum budget in original currency
"""

import os
import sys
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('inr_pkr_bidding_test.log')
    ]
)

def test_inr_pkr_bidding():
    """Test that INR/PKR projects bid at minimum budget in original currency"""
    try:
        from autowork.core.autowork_minimal import AutoWorkMinimal
        
        bot = AutoWorkMinimal()
        
        logging.info("="*60)
        logging.info("TESTING INR/PKR BIDDING AT MINIMUM BUDGET")
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
                'jobs': [{'id': '13', 'name': 'Python'}]
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
                'jobs': [{'id': '3', 'name': 'PHP'}]
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
                'jobs': [{'id': '9', 'name': 'Data Entry'}]
            }
        ]
        
        logging.info("\nTesting bid amount calculations:")
        logging.info("-" * 60)
        
        for i, project in enumerate(test_projects, 1):
            currency = project['currency']['code']
            min_budget = project['budget']['minimum']
            
            logging.info(f"\nTest {i}: {project['title']}")
            logging.info(f"  Currency: {currency}")
            logging.info(f"  Minimum Budget: {min_budget} {currency}")
            
            # Calculate bid amount
            bid_amount = bot.calculate_bid_amount(project)
            
            logging.info(f"  Calculated Bid: {bid_amount:.2f} USD")
            
            # Check if this is correct behavior
            if currency == 'USD':
                expected = min_budget
                success = abs(bid_amount - expected) < 0.01
                logging.info(f"  Expected: {expected} USD")
                logging.info(f"  Result: {'✅ PASS' if success else '❌ FAIL'}")
            else:
                # For INR/PKR, we should bid at the minimum budget in original currency
                # But current implementation converts to USD
                logging.info(f"  Current behavior: Converts to USD")
                logging.info(f"  Issue: Should bid at {min_budget} {currency}, not {bid_amount:.2f} USD")
                logging.info(f"  Result: ❌ FAIL - Wrong behavior")
        
        # Test the issue more specifically
        logging.info("\n" + "="*60)
        logging.info("DETAILED ANALYSIS OF THE ISSUE")
        logging.info("="*60)
        
        inr_project = test_projects[0]
        pkr_project = test_projects[1]
        
        # Current behavior
        inr_bid_usd = bot.calculate_bid_amount(inr_project)
        pkr_bid_usd = bot.calculate_bid_amount(pkr_project)
        
        logging.info(f"INR Project (₹15,000):")
        logging.info(f"  Should bid: ₹15,000")
        logging.info(f"  Currently bids: ${inr_bid_usd:.2f} USD")
        logging.info(f"  Issue: Bidding in USD instead of INR")
        
        logging.info(f"\nPKR Project (PKR 20,000):")
        logging.info(f"  Should bid: PKR 20,000")
        logging.info(f"  Currently bids: ${pkr_bid_usd:.2f} USD")
        logging.info(f"  Issue: Bidding in USD instead of PKR")
        
        # Check currency converter rates
        if bot.currency_converter:
            inr_rate = bot.currency_converter.rates.get('INR', 0)
            pkr_rate = bot.currency_converter.rates.get('PKR', 0)
            
            logging.info(f"\nCurrency Conversion Rates:")
            logging.info(f"  INR to USD: 1 INR = ${1/inr_rate:.4f} USD")
            logging.info(f"  PKR to USD: 1 PKR = ${1/pkr_rate:.4f} USD")
            
            # Calculate what the current bid amounts represent in original currency
            inr_equivalent = inr_bid_usd * inr_rate
            pkr_equivalent = pkr_bid_usd * pkr_rate
            
            logging.info(f"\nCurrent bid amounts in original currency:")
            logging.info(f"  INR bid: ₹{inr_equivalent:.2f} (should be ₹15,000)")
            logging.info(f"  PKR bid: PKR {pkr_equivalent:.2f} (should be PKR 20,000)")
        
        logging.info("\n" + "="*60)
        logging.info("CONCLUSION")
        logging.info("="*60)
        logging.info("❌ ISSUE CONFIRMED: The bot is converting INR/PKR minimum budgets to USD")
        logging.info("✅ SOLUTION: Should bid at the minimum budget in the original currency")
        logging.info("✅ FIX NEEDED: Modify calculate_bid_amount() to return original currency amount")
        
    except Exception as e:
        logging.error(f"Error in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_inr_pkr_bidding() 