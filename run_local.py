#!/usr/bin/env python3
"""
Run the dashboard locally for testing
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

# Verify required environment variables
required_vars = ['FREELANCER_OAUTH_TOKEN']
missing_vars = [var for var in required_vars if not os.environ.get(var)]

if missing_vars:
    print("❌ Missing required environment variables:")
    for var in missing_vars:
        print(f"   - {var}")
    print("\n📝 Please create a .env.local file with your credentials")
    print("   Copy .env.local.example and fill in your values")
    sys.exit(1)

# Import and run the dashboard
try:
    from dashboard import app
    
    print("✅ Environment variables loaded")
    print(f"📊 Dashboard starting on http://localhost:{os.environ.get('PORT', 5000)}")
    print(f"🔑 Using Freelancer User ID: {os.environ.get('FREELANCER_USER_ID', '45214417')}")
    
    if os.environ.get('REDIS_URL'):
        print("🔴 Redis URL configured - will show live bot data")
    else:
        print("⚠️  No Redis URL - dashboard will work but show zero stats")
    
    print("\n🚀 Dashboard is running! Open http://localhost:5000 in your browser")
    print("Press Ctrl+C to stop\n")
    
    app.run(
        host='127.0.0.1',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', '1') == '1'
    )
    
except ImportError:
    print("❌ Could not import dashboard.py")
    print("   Make sure dashboard.py is in the current directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting dashboard: {e}")
    sys.exit(1)