#!/usr/bin/env python3
"""
Fixed Cron Monitor for Render Deployment
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


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
        
        # Check if the method exists
        if hasattr(app, 'realtime_monitor_with_bidding'):
            logger.info("Starting real-time monitoring with realtime_monitor_with_bidding...")
            app.realtime_monitor_with_bidding()
        else:
            logger.warning("realtime_monitor_with_bidding method not found, falling back to basic monitoring...")
            # Fallback: Run a simple monitoring loop
            logger.info("Running basic monitoring loop...")
            
            error_count = 0
            max_errors = 5
            
            while True:
                try:
                    # Fetch projects
                    projects = app.get_active_projects(limit=50)
                    
                    if projects:
                        logger.info(f"Found {len(projects)} active projects")
                        
                        new_bids = 0
                        for project in projects:
                            project_id = project.get("id")
                            
                            # Skip if already processed
                            if project_id in app.processed_projects:
                                continue
                            
                            # Check if should bid
                            should_bid, reason = app.should_bid_on_project(project)
                            
                            if should_bid:
                                logger.info(f"Bidding on: {project.get('title', 'Unknown')[:50]}...")
                                success = app.place_bid(project)
                                
                                if success:
                                    new_bids += 1
                                    time.sleep(5)  # Wait between bids
                                
                                # Limit bids per cycle
                                if new_bids >= 5:
                                    break
                            else:
                                app.processed_projects.add(project_id)
                        
                        logger.info(f"Placed {new_bids} new bids this cycle")
                        error_count = 0
                    else:
                        error_count += 1
                        logger.warning(f"No projects fetched (error count: {error_count}/{max_errors})")
                        
                        if error_count >= max_errors:
                            logger.error("Max errors reached. Waiting 5 minutes...")
                            time.sleep(300)
                            error_count = 0
                    
                    # Save state
                    app.save_state_to_redis()
                    
                    # Wait before next cycle
                    wait_time = 60  # 1 minute
                    logger.info(f"Waiting {wait_time} seconds until next cycle...")
                    time.sleep(wait_time)
                    
                except KeyboardInterrupt:
                    logger.info("Bot stopped by user")
                    break
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error in monitoring loop: {e}")
                    if error_count >= max_errors:
                        logger.error("Too many errors. Waiting 5 minutes...")
                        time.sleep(300)
                        error_count = 0
                    else:
                        time.sleep(30)
        
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