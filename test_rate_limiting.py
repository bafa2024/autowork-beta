#!/usr/bin/env python3
"""
Test script to verify rate limiting functionality
"""

import time
import logging
from autowork_minimal import AutoWorkMinimal

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_rate_limiting():
    """Test the rate limiting functionality"""
    print("🧪 Testing Rate Limiting Functionality")
    print("=" * 50)
    
    try:
        # Initialize bot
        bot = AutoWorkMinimal()
        
        print("✅ Bot initialized successfully")
        print(f"📊 Configuration:")
        print(f"   - Min bid delay: {bot.config['bidding']['min_bid_delay_seconds']} seconds")
        print(f"   - Check interval: {bot.config['monitoring']['check_interval_seconds']} seconds")
        print(f"   - Peak hours interval: {bot.config['monitoring']['peak_hours_interval']} seconds")
        print(f"   - Daily bid limit: {bot.config['monitoring']['daily_bid_limit']} bids")
        
        # Test rate limiting
        print("\n🔍 Testing rate limiting...")
        
        # First check - should not be rate limited
        is_limited = bot.is_rate_limited()
        print(f"   Initial rate limit check: {'Rate Limited' if is_limited else 'Not Rate Limited'}")
        
        # Set a timestamp
        bot.set_rate_limit_timestamp()
        print("   Set rate limit timestamp")
        
        # Check again - should be rate limited
        is_limited = bot.is_rate_limited()
        print(f"   After setting timestamp: {'Rate Limited' if is_limited else 'Not Rate Limited'}")
        
        # Wait and check again
        print("   Waiting 30 seconds...")
        time.sleep(30)
        
        is_limited = bot.is_rate_limited()
        print(f"   After 30 seconds: {'Rate Limited' if is_limited else 'Not Rate Limited'}")
        
        # Wait full 60 seconds
        print("   Waiting additional 30 seconds...")
        time.sleep(30)
        
        is_limited = bot.is_rate_limited()
        print(f"   After 60 seconds: {'Rate Limited' if is_limited else 'Not Rate Limited'}")
        
        print("\n✅ Rate limiting test completed successfully!")
        print("\n📋 Summary of changes made to prevent rate limiting:")
        print("   - Increased min bid delay to 60 seconds")
        print("   - Reduced max bids per cycle to 3")
        print("   - Increased check intervals (120s, 90s, 180s)")
        print("   - Reduced daily bid limit to 50")
        print("   - Added 60-second rate limit check")
        print("   - Added 2-minute wait on 429 errors")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rate_limiting() 