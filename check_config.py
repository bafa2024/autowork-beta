#!/usr/bin/env python3
"""
Check if bot_config.json exists and is valid
"""

import os
import json
import sys

def check_config():
    print("Checking bot configuration...")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in directory: {os.listdir('.')}")
    
    config_file = "bot_config.json"
    
    if not os.path.exists(config_file):
        print(f"\n❌ ERROR: {config_file} not found!")
        print("\nCreating default configuration...")
        
        default_config = {
            "bidding": {
                "delivery_days": 4,
                "express_delivery_days": 2,
                "min_bid_delay_seconds": 10,
                "bid_multiplier_regular": 1.15,
                "bid_multiplier_elite": 1.2,
                "default_bid_regular": 100,
                "default_bid_elite": 150
            },
            "smart_bidding": {
                "enabled": True,
                "max_existing_bids": 15,
                "early_bird_minutes": 30,
                "instant_bid_threshold": 5,
                "competitive_pricing": True,
                "undercut_percentage": 0.95,
                "min_profitable_budget": 50
            },
            "client_filtering": {
                "enabled": True,
                "min_client_rating": 4.0,
                "min_completion_rate": 0.8,
                "min_projects_posted": 1,
                "check_payment_verified": True
            },
            "elite_projects": {
                "auto_sign_nda": True,
                "auto_sign_ip_agreement": True,
                "track_elite_stats": True
            },
            "filtering": {
                "max_projects_per_cycle": 50,
                "skip_projects_with_bids_above": 25,
                "portfolio_matching": True,
                "min_skill_match_score": 0.3
            },
            "monitoring": {
                "check_interval_seconds": 60,
                "peak_hours_interval": 45,
                "off_hours_interval": 90,
                "error_retry_delay_seconds": 300,
                "max_consecutive_errors": 5,
                "daily_bid_limit": 50
            },
            "performance": {
                "track_analytics": True,
                "ab_testing_enabled": True,
                "analyze_every_n_cycles": 10
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"✅ Created {config_file} with default configuration")
        return default_config
    
    else:
        print(f"\n✅ {config_file} found")
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print("✅ Configuration is valid JSON")
            
            # Check required sections
            required_sections = [
                'bidding', 'smart_bidding', 'client_filtering', 
                'elite_projects', 'filtering', 'monitoring', 'performance'
            ]
            
            missing = []
            for section in required_sections:
                if section not in config:
                    missing.append(section)
                else:
                    print(f"✅ Section '{section}' found")
            
            if missing:
                print(f"\n❌ Missing sections: {', '.join(missing)}")
                print("\nAdding missing sections with defaults...")
                
                # Add missing sections
                if 'smart_bidding' not in config:
                    config['smart_bidding'] = {
                        "enabled": True,
                        "max_existing_bids": 15,
                        "early_bird_minutes": 30,
                        "instant_bid_threshold": 5,
                        "competitive_pricing": True,
                        "undercut_percentage": 0.95,
                        "min_profitable_budget": 50
                    }
                
                # Save updated config
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                print(f"✅ Updated {config_file} with missing sections")
            
            return config
            
        except json.JSONDecodeError as e:
            print(f"\n❌ ERROR: Invalid JSON in {config_file}")
            print(f"Error details: {e}")
            print("\nPlease fix the JSON syntax or delete the file to create a new one")
            return None

if __name__ == "__main__":
    config = check_config()
    if config:
        print("\n✅ Configuration check complete!")
        print(f"\nConfiguration sections: {list(config.keys())}")
    else:
        print("\n❌ Configuration check failed!")
        sys.exit(1)