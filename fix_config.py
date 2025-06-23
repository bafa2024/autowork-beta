#!/usr/bin/env python3
"""
Fix bot_config.json by adding any missing sections
"""

import json
import os

def fix_bot_config():
    """Ensure bot_config.json has all required sections"""
    
    # Default complete configuration
    default_config = {
        "bidding": {
            "delivery_days": 4,
            "express_delivery_days": 2,
            "min_bid_delay_seconds": 5,
            "bid_multiplier_regular": 1.15,
            "bid_multiplier_elite": 1.2,
            "default_bid_regular": 100,
            "default_bid_elite": 150
        },
        "smart_bidding": {
            "enabled": True,
            "max_existing_bids": 50,
            "early_bird_minutes": 60,
            "instant_bid_threshold": 10,
            "competitive_pricing": True,
            "undercut_percentage": 0.95,
            "min_profitable_budget": 30
        },
        "client_filtering": {
            "enabled": False,
            "min_client_rating": 3.0,
            "min_completion_rate": 0.5,
            "min_projects_posted": 0,
            "check_payment_verified": False
        },
        "elite_projects": {
            "auto_sign_nda": True,
            "auto_sign_ip_agreement": True,
            "track_elite_stats": True
        },
        "filtering": {
            "max_projects_per_cycle": 50,
            "skip_projects_with_bids_above": 100,
            "portfolio_matching": False,
            "min_skill_match_score": 0.1
        },
        "monitoring": {
            "check_interval_seconds": 30,
            "peak_hours_interval": 20,
            "off_hours_interval": 60,
            "error_retry_delay_seconds": 300,
            "max_consecutive_errors": 5,
            "daily_bid_limit": 100
        },
        "performance": {
            "track_analytics": True,
            "ab_testing_enabled": True,
            "analyze_every_n_cycles": 10
        }
    }
    
    config_file = "bot_config.json"
    
    # Load existing config if it exists
    if os.path.exists(config_file):
        print(f"Found existing {config_file}")
        try:
            with open(config_file, 'r') as f:
                existing_config = json.load(f)
            print("✓ Loaded existing configuration")
        except Exception as e:
            print(f"✗ Error loading config: {e}")
            existing_config = {}
    else:
        print(f"No {config_file} found, creating new one")
        existing_config = {}
    
    # Merge configurations (existing values take precedence)
    updated = False
    for section, values in default_config.items():
        if section not in existing_config:
            print(f"✓ Adding missing section: {section}")
            existing_config[section] = values
            updated = True
        else:
            # Check for missing keys within sections
            for key, value in values.items():
                if key not in existing_config[section]:
                    print(f"✓ Adding missing key: {section}.{key}")
                    existing_config[section][key] = value
                    updated = True
    
    # Save the updated config
    with open(config_file, 'w') as f:
        json.dump(existing_config, f, indent=2)
    
    if updated:
        print(f"\n✅ Updated {config_file} with missing sections/keys")
    else:
        print(f"\n✅ {config_file} already has all required sections")
    
    # Show current important settings
    print("\n📋 Current Key Settings:")
    print(f"   Min Budget: ${existing_config['smart_bidding']['min_profitable_budget']}")
    print(f"   Max Bids Allowed: {existing_config['filtering']['skip_projects_with_bids_above']}")
    print(f"   Client Filtering: {'Enabled' if existing_config['client_filtering']['enabled'] else 'Disabled'}")
    print(f"   Portfolio Matching: {'Enabled' if existing_config['filtering']['portfolio_matching'] else 'Disabled'}")
    print(f"   Daily Bid Limit: {existing_config['monitoring']['daily_bid_limit']}")

if __name__ == "__main__":
    fix_bot_config()