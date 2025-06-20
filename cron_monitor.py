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

def run_autowork():
    """Run the AutoWork bot"""
    try:
        logger.info("Starting AutoWork Bot (Minimal Version)...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Environment: Render" if os.environ.get('RENDER') else "Local")
        
        # Check for token
        if not os.environ.get('FREELANCER_OAUTH_TOKEN'):
            # Try to load from .env file
            if os.path.exists('.env'):
                from dotenv import load_dotenv
                load_dotenv()
        
        # Create bot instance
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
        logger.error(traceback.format_exc())
        # Wait before restarting
        time.sleep(60)
        # Re-raise to let Render handle the restart
        raise

def main():
    """Main entry point with restart logic"""
    logger.info("="*50)
    logger.info("AutoWork Bot Starting - Minimal Version")
    logger.info("="*50)
    logger.info(f"Current time: {datetime.now()}")
    
    # Run with automatic restart
    restart_count = 0
    max_restarts = 10
    
    while restart_count < max_restarts:
        try:
            run_autowork()
            # If it exits normally, break
            break
        except Exception as e:
            restart_count += 1
            logger.error(f"Bot crashed (attempt {restart_count}/{max_restarts}): {e}")
            
            if restart_count < max_restarts:
                wait_time = min(60 * restart_count, 300)  # Max 5 minutes
                logger.info(f"Restarting in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error("Max restarts reached. Exiting.")
                sys.exit(1)

if __name__ == "__main__":
    main()