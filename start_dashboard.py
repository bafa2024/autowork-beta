#!/usr/bin/env python3
"""
Dashboard Startup Script
Provides an easy way to start the AutoWork Bot Dashboard
"""

import os
import sys
from dotenv import load_dotenv

def check_requirements():
    """Check if required packages are installed"""
    print("Checking requirements...")
    
    required_packages = ['flask', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} (missing)")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("   Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_environment():
    """Check environment variables"""
    print("\nChecking environment...")
    
    # Load .env file if it exists
    if os.path.exists('.env'):
        load_dotenv('.env')
        print("✅ Loaded .env file")
    elif os.path.exists('.env.local'):
        load_dotenv('.env.local')
        print("✅ Loaded .env.local file")
    else:
        print("⚠️  No .env file found")
    
    # Check for token
    token = os.environ.get('FREELANCER_OAUTH_TOKEN')
    if token:
        print("✅ Freelancer token configured")
    else:
        print("⚠️  FREELANCER_OAUTH_TOKEN not set")
        print("   Dashboard will work but account info will show errors")
    
    # Check for Redis
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        print("✅ Redis URL configured")
    else:
        print("⚠️  REDIS_URL not set")
        print("   Dashboard will work but stats will show zero values")
    
    return True

def start_dashboard():
    """Start the dashboard"""
    print("\n🚀 Starting AutoWork Bot Dashboard...")
    
    try:
        from dashboard import app
        
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '127.0.0.1')
        
        print(f"📊 Dashboard will be available at: http://{host}:{port}")
        print("   Press Ctrl+C to stop the dashboard")
        print("\n" + "="*50)
        
        app.run(
            host=host,
            port=port,
            debug=os.environ.get('FLASK_DEBUG', '0') == '1'
        )
        
    except KeyboardInterrupt:
        print("\n⏹️  Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")
        print("   Make sure dashboard.py exists and is working correctly")
        return False
    
    return True

def main():
    """Main function"""
    print("=" * 60)
    print("🤖 AUTOWORK BOT DASHBOARD")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed")
        sys.exit(1)
    
    # Check environment
    check_environment()
    
    # Start dashboard
    print("\n" + "=" * 60)
    start_dashboard()

if __name__ == "__main__":
    main() 