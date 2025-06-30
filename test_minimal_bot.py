#!/usr/bin/env python3
"""
Test script for autowork_minimal.py
Verifies that the bot can be imported and initialized
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_bot_import():
    """Test that the bot can be imported"""
    try:
        from autowork_minimal import AutoWorkMinimal
        print("✅ Successfully imported AutoWorkMinimal class")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False

def test_bot_initialization():
    """Test that the bot can be initialized (without running)"""
    try:
        from autowork_minimal import AutoWorkMinimal
        
        # Set a dummy token for testing
        os.environ['FREELANCER_OAUTH_TOKEN'] = 'test_token_for_initialization'
        
        # Try to create an instance (this will fail at token verification, but that's expected)
        bot = AutoWorkMinimal()
        print("✅ Bot initialized successfully")
        return True
        
    except ValueError as e:
        if "Token validation failed" in str(e):
            print("✅ Bot initialization test passed (token validation failed as expected)")
            return True
        else:
            print(f"❌ Unexpected ValueError: {e}")
            return False
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False

def test_config_loading():
    """Test that configuration can be loaded"""
    try:
        from autowork_minimal import AutoWorkMinimal
        
        # Create a minimal bot instance just to test config loading
        bot = AutoWorkMinimal.__new__(AutoWorkMinimal)
        config = bot.load_config()
        
        if isinstance(config, dict) and 'bidding' in config:
            print("✅ Configuration loaded successfully")
            return True
        else:
            print("❌ Configuration loading failed")
            return False
            
    except Exception as e:
        print(f"❌ Configuration test error: {e}")
        return False

def test_required_files():
    """Test that all required files exist"""
    required_files = [
        'bid_messages.json',
        'skills_map.json', 
        'specializations.json',
        'bot_config.json',
        'premium_filter.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    else:
        print("✅ All required files found")
        return True

def main():
    """Run all tests"""
    print("🧪 Testing AutoWork Minimal Bot")
    print("=" * 50)
    
    tests = [
        ("Required Files", test_required_files),
        ("Bot Import", test_bot_import),
        ("Configuration Loading", test_config_loading),
        ("Bot Initialization", test_bot_initialization),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"   ❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The bot should be ready to run.")
        print("\n📝 Next steps:")
        print("   1. Set your FREELANCER_OAUTH_TOKEN environment variable")
        print("   2. Run: python autowork_minimal.py")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 