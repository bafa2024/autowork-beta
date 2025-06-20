#!/usr/bin/env python3
"""
Cron Monitor for Render Deployment
Runs the AutoWork bot continuously as a background worker
"""

import os
import sys
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_autowork():
    """Run the AutoWork bot"""
    try:
        # Import here to ensure all modules are loaded
        from autowork_minimal import AutoWorkMinimal
        
        logger.info("Starting AutoWork Bot...")
        logger.info(f"Environment: {os.environ.get('RENDER', 'Local')}")
        logger.info(f"Auto-bid enabled: {os.environ.get('AUTO_BID_ENABLED', 'true')}")
        
        # Create bot instance
        app = AutoWorkMinimal()
        
        # Run the real-time monitor
        logger.info("Starting real-time monitoring...")
        app.realtime_monitor_with_bidding()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        # Wait before restarting
        time.sleep(60)
        # Re-raise to let Render handle the restart
        raise

def main():
    """Main entry point with restart logic"""
    logger.info("=== AutoWork Bot Starting ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current time: {datetime.now()}")
    
    # Check for required environment variables
    if not os.environ.get('FREELANCER_OAUTH_TOKEN'):
        logger.error("FREELANCER_OAUTH_TOKEN not set!")
        sys.exit(1)
    
    # Run with automatic restart
    while True:
        try:
            run_autowork()
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            logger.info("Restarting in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main()