#!/usr/bin/env python3
"""
Simple test script to verify NDA/IP auto-signing functionality
"""

import os
import sys
import json
import logging
from datetime import datetime

# Set up simple logging without Unicode
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('nda_simple_test.log')
    ]
)

def test_nda_methods_exist():
    """Test that the NDA methods exist in the main bot"""
    try:
        from autowork.core.autowork_minimal import AutoWorkMinimal
        
        bot = AutoWorkMinimal()
        
        # Check if methods exist
        if hasattr(bot, 'check_and_sign_nda'):
            logging.info("PASS: check_and_sign_nda method exists")
        else:
            logging.error("FAIL: check_and_sign_nda method is missing")
            return False
            
        if hasattr(bot, 'check_and_sign_ip_agreement'):
            logging.info("PASS: check_and_sign_ip_agreement method exists")
        else:
            logging.error("FAIL: check_and_sign_ip_agreement method is missing")
            return False
            
        if hasattr(bot, 'get_project_details'):
            logging.info("PASS: get_project_details method exists")
        else:
            logging.error("FAIL: get_project_details method is missing")
            return False
            
        return True
        
    except Exception as e:
        logging.error(f"ERROR testing NDA methods: {e}")
        return False

def test_config_nda_settings():
    """Test that NDA settings are properly configured"""
    try:
        from autowork.core.autowork_minimal import AutoWorkMinimal
        
        bot = AutoWorkMinimal()
        
        # Check config
        elite_config = bot.config.get('elite_projects', {})
        
        auto_sign_nda = elite_config.get('auto_sign_nda', False)
        auto_sign_ip = elite_config.get('auto_sign_ip_agreement', False)
        
        logging.info(f"Auto-sign NDA: {auto_sign_nda}")
        logging.info(f"Auto-sign IP agreement: {auto_sign_ip}")
        
        if auto_sign_nda and auto_sign_ip:
            logging.info("PASS: NDA/IP auto-signing is enabled in config")
            return True
        else:
            logging.warning("WARNING: NDA/IP auto-signing is disabled in config")
            return False
            
    except Exception as e:
        logging.error(f"ERROR testing config: {e}")
        return False

def test_project_details_method():
    """Test the get_project_details method"""
    try:
        from autowork.core.autowork_minimal import AutoWorkMinimal
        
        bot = AutoWorkMinimal()
        
        # Create a dummy project
        dummy_project = {
            'id': 12345,
            'title': 'Test Project',
            'upgrades': {
                'NDA': True,
                'ip_contract': False,
                'featured': True,
                'sealed': False,
                'urgent': False,
                'qualified': False,
                'non_compete': False
            },
            'budget': {'minimum': 100, 'maximum': 500},
            'seo_url': 'test-project'
        }
        
        details = bot.get_project_details(dummy_project)
        
        logging.info(f"Project details: {json.dumps(details, indent=2)}")
        
        # Check if NDA flag is detected
        if details.get('nda', False):
            logging.info("PASS: NDA flag is properly detected")
        else:
            logging.error("FAIL: NDA flag not detected")
            return False
            
        return True
        
    except Exception as e:
        logging.error(f"ERROR testing project details: {e}")
        return False

def test_nda_method_structure():
    """Test the structure of NDA methods without calling them"""
    try:
        from autowork.core.autowork_minimal import AutoWorkMinimal
        
        bot = AutoWorkMinimal()
        
        # Test that methods are callable
        if callable(bot.check_and_sign_nda):
            logging.info("PASS: check_and_sign_nda is callable")
        else:
            logging.error("FAIL: check_and_sign_nda is not callable")
            return False
            
        if callable(bot.check_and_sign_ip_agreement):
            logging.info("PASS: check_and_sign_ip_agreement is callable")
        else:
            logging.error("FAIL: check_and_sign_ip_agreement is not callable")
            return False
            
        return True
        
    except Exception as e:
        logging.error(f"ERROR testing method structure: {e}")
        return False

def main():
    """Run all tests"""
    logging.info("="*60)
    logging.info("NDA/IP AUTO-SIGNING SIMPLE TEST")
    logging.info("="*60)
    
    tests = [
        ("NDA Methods Exist", test_nda_methods_exist),
        ("Config NDA Settings", test_config_nda_settings),
        ("Project Details Method", test_project_details_method),
        ("NDA Method Structure", test_nda_method_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logging.info(f"\n{'='*40}")
        logging.info(f"Running: {test_name}")
        logging.info(f"{'='*40}")
        
        try:
            if test_func():
                logging.info(f"PASS: {test_name}")
                passed += 1
            else:
                logging.error(f"FAIL: {test_name}")
        except Exception as e:
            logging.error(f"ERROR: {test_name} - {e}")
    
    logging.info(f"\n{'='*60}")
    logging.info("TEST SUMMARY")
    logging.info(f"{'='*60}")
    logging.info(f"Passed: {passed}/{total}")
    logging.info(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        logging.info("SUCCESS: ALL TESTS PASSED - NDA functionality should be working!")
    else:
        logging.warning("WARNING: Some tests failed - check the logs above")
    
    logging.info(f"\nLog file: nda_simple_test.log")

if __name__ == "__main__":
    main() 