#!/usr/bin/env python3
"""
Test script for INR/PKR currency filtering feature
Tests the strict filtering requirements for INR and PKR currencies
"""

import json
import logging
from autowork_minimal import AutoWorkMinimal

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_inr_pkr_filtering():
    """Test the INR/PKR currency filtering feature"""
    
    print("="*60)
    print("🧪 TESTING INR/PKR CURRENCY FILTERING FEATURE")
    print("="*60)
    
    try:
        # Initialize bot
        bot = AutoWorkMinimal()
        
        print("\n✅ Bot initialized successfully")
        print(f"Currency filtering enabled: {bot.config.get('currency_filtering', {}).get('enabled', False)}")
        print(f"INR/PKR strict filtering: {bot.config.get('currency_filtering', {}).get('inr_pkr_strict_filtering', False)}")
        
        # Test minimum budget thresholds
        print("\n💰 Testing minimum budget thresholds:")
        
        # Test INR minimums
        inr_fixed_min = bot.get_minimum_budget_for_currency('INR', 'fixed')
        inr_hourly_min = bot.get_minimum_budget_for_currency('INR', 'hourly')
        print(f"   INR Fixed projects minimum: ₹{inr_fixed_min:,.2f}")
        print(f"   INR Hourly projects minimum: ₹{inr_hourly_min:,.2f}")
        
        # Test PKR minimums
        pkr_fixed_min = bot.get_minimum_budget_for_currency('PKR', 'fixed')
        pkr_hourly_min = bot.get_minimum_budget_for_currency('PKR', 'hourly')
        print(f"   PKR Fixed projects minimum: ₨{pkr_fixed_min:,.2f}")
        print(f"   PKR Hourly projects minimum: ₨{pkr_hourly_min:,.2f}")
        
        # Test other currencies for comparison
        usd_fixed_min = bot.get_minimum_budget_for_currency('USD', 'fixed')
        usd_hourly_min = bot.get_minimum_budget_for_currency('USD', 'hourly')
        print(f"   USD Fixed projects minimum: ${usd_fixed_min:.2f}")
        print(f"   USD Hourly projects minimum: ${usd_hourly_min:.2f}")
        
        # Test sample projects with different currencies
        print("\n📋 Testing sample projects:")
        
        # Test 1: INR project with low budget (should be rejected)
        inr_low_budget_project = {
            'id': 1001,
            'title': 'Test INR Project - Low Budget',
            'budget': {
                'minimum': 5000.0,  # Below 16000 INR minimum
                'maximum': 10000.0,
                'type': 'fixed'
            },
            'currency': {'code': 'INR'},
            'bid_stats': {'bid_count': 5},
            'owner_id': 12345
        }
        
        should_bid, reason = bot.should_bid_on_project(inr_low_budget_project)
        print(f"   INR Low Budget Project (₹5,000): {'✅ PASS' if not should_bid else '❌ FAIL'}")
        print(f"      Reason: {reason}")
        
        # Test 2: INR project with adequate budget (should pass budget check)
        inr_adequate_budget_project = {
            'id': 1002,
            'title': 'Test INR Project - Adequate Budget',
            'budget': {
                'minimum': 20000.0,  # Above 16000 INR minimum
                'maximum': 50000.0,
                'type': 'fixed'
            },
            'currency': {'code': 'INR'},
            'bid_stats': {'bid_count': 5},
            'owner_id': 12346
        }
        
        should_bid, reason = bot.should_bid_on_project(inr_adequate_budget_project)
        print(f"   INR Adequate Budget Project (₹20,000): {'✅ PASS' if should_bid or 'client verification' in reason else '❌ FAIL'}")
        print(f"      Reason: {reason}")
        
        # Test 3: PKR project with low budget (should be rejected)
        pkr_low_budget_project = {
            'id': 1003,
            'title': 'Test PKR Project - Low Budget',
            'budget': {
                'minimum': 20000.0,  # Below 55600 PKR minimum
                'maximum': 40000.0,
                'type': 'fixed'
            },
            'currency': {'code': 'PKR'},
            'bid_stats': {'bid_count': 5},
            'owner_id': 12347
        }
        
        should_bid, reason = bot.should_bid_on_project(pkr_low_budget_project)
        print(f"   PKR Low Budget Project (₨20,000): {'✅ PASS' if not should_bid else '❌ FAIL'}")
        print(f"      Reason: {reason}")
        
        # Test 4: USD project (should use regular filtering)
        usd_project = {
            'id': 1004,
            'title': 'Test USD Project',
            'budget': {
                'minimum': 100.0,  # Below 250 USD minimum
                'maximum': 200.0,
                'type': 'fixed'
            },
            'currency': {'code': 'USD'},
            'bid_stats': {'bid_count': 5},
            'owner_id': 12348
        }
        
        should_bid, reason = bot.should_bid_on_project(usd_project)
        print(f"   USD Low Budget Project ($100): {'✅ PASS' if not should_bid else '❌ FAIL'}")
        print(f"      Reason: {reason}")
        
        # Test 5: INR hourly project
        inr_hourly_project = {
            'id': 1005,
            'title': 'Test INR Hourly Project',
            'budget': {
                'minimum': 1000.0,  # Below 1600 INR hourly minimum
                'maximum': 2000.0,
                'type': 'hourly'
            },
            'currency': {'code': 'INR'},
            'bid_stats': {'bid_count': 5},
            'owner_id': 12349
        }
        
        should_bid, reason = bot.should_bid_on_project(inr_hourly_project)
        print(f"   INR Hourly Project (₹1,000/hr): {'✅ PASS' if not should_bid else '❌ FAIL'}")
        print(f"      Reason: {reason}")
        
        # Test 6: INR hourly project with adequate budget
        inr_hourly_adequate_project = {
            'id': 1006,
            'title': 'Test INR Hourly Project - Adequate',
            'budget': {
                'minimum': 2000.0,  # Above 1600 INR hourly minimum
                'maximum': 5000.0,
                'type': 'hourly'
            },
            'currency': {'code': 'INR'},
            'bid_stats': {'bid_count': 5},
            'owner_id': 12350
        }
        
        should_bid, reason = bot.should_bid_on_project(inr_hourly_adequate_project)
        print(f"   INR Hourly Adequate Project (₹2,000/hr): {'✅ PASS' if should_bid or 'client verification' in reason else '❌ FAIL'}")
        print(f"      Reason: {reason}")
        
        # Display skip statistics
        print("\n📊 Skip Statistics:")
        for reason, count in bot.skipped_projects.items():
            if count > 0:
                print(f"   {reason}: {count}")
        
        # Test configuration
        print("\n⚙️ Configuration Check:")
        currency_config = bot.config.get('currency_filtering', {})
        print(f"   Currency filtering enabled: {currency_config.get('enabled', False)}")
        print(f"   INR/PKR strict filtering: {currency_config.get('inr_pkr_strict_filtering', False)}")
        print(f"   INR minimum budget: ₹{currency_config.get('inr_minimum_budget', 0):,.2f}")
        print(f"   PKR minimum budget: ₨{currency_config.get('pkr_minimum_budget', 0):,.2f}")
        print(f"   Require payment verified for INR/PKR: {currency_config.get('require_payment_verified_for_inr_pkr', False)}")
        print(f"   Require identity verified for INR/PKR: {currency_config.get('require_identity_verified_for_inr_pkr', False)}")
        print(f"   Skip phone/email only for INR/PKR: {currency_config.get('skip_phone_email_only_for_inr_pkr', False)}")
        
        print("\n✅ INR/PKR currency filtering test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_inr_pkr_filtering() 