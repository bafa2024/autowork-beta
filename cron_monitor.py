#!/usr/bin/env python3
"""
Cron Monitor for Render Deployment - Minimal Version
Runs the AutoWork bot continuously without external dependencies
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the minimal version
from autowork_minimal import AutoWorkMinimal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set"""
    token = os.environ.get('FREELANCER_OAUTH_TOKEN')
    
    if not token:
        logger.error("="*60)
        logger.error("ERROR: FREELANCER_OAUTH_TOKEN environment variable is not set!")
        logger.error("Please set it in Render dashboard under Environment Variables")
        logger.error("="*60)
        return False
    
    logger.info("✓ FREELANCER_OAUTH_TOKEN found")
    logger.info(f"✓ Token preview: {token[:10]}...")
    
    # Check optional variables
    user_id = os.environ.get('FREELANCER_USER_ID', '45214417')
    logger.info(f"✓ FREELANCER_USER_ID: {user_id}")
    
    return True

def run_autowork():
    """Run the AutoWork bot"""
    try:
        logger.info("Starting AutoWork Bot (Minimal Version)...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Environment: {'Render' if os.environ.get('RENDER') else 'Local'}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # List files in current directory for debugging
        files = os.listdir('.')
        logger.info(f"Files in current directory: {files}")
        
        # Check environment first
        if not check_environment():
            raise ValueError("Missing required environment variables")
        
        # Create bot instance
        logger.info("Creating bot instance...")
        app = AutoWorkMinimal()
        
        # Run the real-time monitor
        logger.info("Starting real-time monitoring...")
        app.realtime_monitor_with_bidding()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error in bot: {str(e)}")
        # Log full traceback
        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        raise

def main():
    """Main entry point with restart logic"""
    logger.info("="*60)
    logger.info("AutoWork Bot Starting - Minimal Version")
    logger.info("="*60)
    logger.info(f"Current time: {datetime.now()}")
    logger.info(f"Process ID: {os.getpid()}")
    
    # Log all environment variables (hiding sensitive data)
    logger.info("Environment variables:")
    for key in sorted(os.environ.keys()):
        if 'TOKEN' in key or 'KEY' in key or 'SECRET' in key:
            logger.info(f"  {key}: ***hidden***")
        else:
            logger.info(f"  {key}: {os.environ[key]}")
    
    # Check environment before starting
    if not check_environment():
        logger.error("Exiting due to missing configuration")
        sys.exit(1)
    
    # Run with automatic restart
    restart_count = 0
    max_restarts = 10
    
    while restart_count < max_restarts:
        try:
            logger.info(f"Starting bot (attempt {restart_count + 1}/{max_restarts})...")
            run_autowork()
            # If it exits normally, break
            logger.info("Bot exited normally")
            break
        except Exception as e:
            restart_count += 1
            logger.error(f"Bot crashed (attempt {restart_count}/{max_restarts}): {e}")
            
            if restart_count < max_restarts:
                # Progressive backoff: 60s, 120s, 180s, 240s, 300s (max)
                wait_time = min(60 * restart_count, 300)
                logger.info(f"Restarting in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error("Max restarts reached. Exiting.")
                logger.error("Please check the logs and fix the issue.")
                sys.exit(1)
    
    logger.info("Bot shutdown complete")

if __name__ == "__main__":
    main()