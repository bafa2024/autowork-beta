#!/usr/bin/env python3
"""
Simple Test Script for Project Management System
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_basic_imports():
    """Test basic imports"""
    print("Testing basic imports...")
    
    try:
        import requests
        print("✅ requests imported")
    except ImportError as e:
        print(f"❌ requests import failed: {e}")
        return False
    
    try:
        import redis
        print("✅ redis imported")
    except ImportError as e:
        print(f"❌ redis import failed: {e}")
        return False
    
    try:
        from sqlalchemy import create_engine
        print("✅ SQLAlchemy imported")
    except ImportError as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    try:
        from flask import Flask
        print("✅ Flask imported")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    return True

def test_project_management_import():
    """Test project management import"""
    print("\nTesting project management import...")
    
    try:
        from project_management import ProjectManager
        print("✅ ProjectManager imported")
        return True
    except Exception as e:
        print(f"❌ ProjectManager import failed: {e}")
        return False

def test_autowork_integration_import():
    """Test autowork integration import"""
    print("\nTesting autowork integration import...")
    
    try:
        from autowork_integration import AutoWorkIntegration
        print("✅ AutoWorkIntegration imported")
        return True
    except Exception as e:
        print(f"❌ AutoWorkIntegration import failed: {e}")
        return False

def test_api_server_import():
    """Test API server import"""
    print("\nTesting API server import...")
    
    try:
        from project_management_api import app
        print("✅ API server imported")
        return True
    except Exception as e:
        print(f"❌ API server import failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Simple Test Suite")
    print("=" * 30)
    
    # Test basic imports
    if not test_basic_imports():
        print("❌ Basic imports failed")
        return False
    
    # Test project management
    if not test_project_management_import():
        print("❌ Project management import failed")
        return False
    
    # Test autowork integration
    if not test_autowork_integration_import():
        print("❌ AutoWork integration import failed")
        return False
    
    # Test API server
    if not test_api_server_import():
        print("❌ API server import failed")
        return False
    
    print("\n✅ All imports successful!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)