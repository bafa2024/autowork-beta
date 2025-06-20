#!/usr/bin/env python3
"""
Test script to verify the minimal setup works
"""

import os
import sys

print("Testing AutoWork Minimal Setup")
print("="*40)
print(f"Python version: {sys.version}")

# Test imports
try:
    from dotenv import load_dotenv
    print("✓ python-dotenv imported successfully")
except ImportError as e:
    print(f"✗ Failed to import python-dotenv: {e}")

try:
    from autowork_minimal import AutoWorkMinimal
    print("✓ autowork_minimal imported successfully")
except ImportError as e:
    print(f"✗ Failed to import autowork_minimal: {e}")

# Test environment
print("\nEnvironment Variables:")
print(f"FREELANCER_OAUTH_TOKEN: {'Set' if os.environ.get('FREELANCER_OAUTH_TOKEN') else 'Not set'}")
print(f"RENDER: {'Yes' if os.environ.get('RENDER') else 'No (Local)'}")

# Test bot initialization
try:
    print("\nTesting bot initialization...")
    app = AutoWorkMinimal()
    print("✓ Bot initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize bot: {e}")

print("\nSetup test complete!")