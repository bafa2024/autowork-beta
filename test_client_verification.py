#!/usr/bin/env python3
"""
Test script for client verification features
"""

import json
import logging
from autowork_minimal import AutoWorkMinimal

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_client_verification():
    """Test the client verification features"""
    
    print("🧪 Testing Client Verification Features")
    print("=" * 50)
    
    # Initialize bot
    try:
        bot = AutoWorkMinimal()
        print("✅ Bot initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize bot: {e}")
        return
    
    # Show current configuration
    print("\n📋 Current Client Filtering Configuration:")
    client_config = bot.config['client_filtering']
    for key, value in client_config.items():
        print(f"   {key}: {value}")
    
    # Test client verification with a sample employer ID
    # Note: You'll need to replace this with a real employer ID from Freelancer
    test_employer_id = 123456  # Replace with actual employer ID
    
    print(f"\n🔍 Testing client verification for employer ID: {test_employer_id}")
    
    try:
        client_analysis = bot.analyze_client(test_employer_id)
        
        print(f"\n📊 Client Analysis Results:")
        print(f"   Client Name: {client_analysis.get('client_name', 'Unknown')}")
        print(f"   Is Good Client: {client_analysis.get('is_good_client', False)}")
        
        verification_status = client_analysis.get('verification_status', {})
        print(f"\n🔐 Verification Status:")
        for status_type, status_value in verification_status.items():
            status_icon = "✅" if status_value else "❌"
            print(f"   {status_icon} {status_type}: {status_value}")
        
        reasons = client_analysis.get('reasons', [])
        if reasons:
            print(f"\n❌ Verification Failures:")
            for reason in reasons:
                print(f"   • {reason}")
        else:
            print(f"\n✅ All verification checks passed!")
            
    except Exception as e:
        print(f"❌ Error testing client verification: {e}")
    
    print(f"\n📈 Skip Tracking Categories:")
    for category, count in bot.skipped_projects.items():
        print(f"   {category}: {count}")
    
    print(f"\n🎯 Test completed!")

if __name__ == "__main__":
    test_client_verification() 