#!/usr/bin/env python3
"""
Test the actual bot locally with enhanced NDA/IP logging
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any  # Add this import

# Set up enhanced logging for testing
log_filename = f"bot_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging to both file and console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

# Import and modify the bot for testing
from autowork_minimal import AutoWorkMinimal

class TestBot(AutoWorkMinimal):
    """Extended bot class for testing with extra logging"""
    
    def __init__(self):
        # Initialize with test configuration
        super().__init__()
        
        # Override config for testing
        self.config['min_bid_delay'] = 2  # Faster for testing
        self.test_mode = True
        self.test_results = {
            'nda_projects': [],
            'ip_projects': [],
            'signed_ndas': [],
            'signed_ips': [],
            'bids_placed': []
        }
        
        logging.info("🧪 TEST MODE ENABLED - Enhanced NDA/IP logging active")
        
    def check_and_sign_nda(self, project_id: int) -> bool:
        """Override to add detailed logging"""
        logging.info(f"\n{'='*50}")
        logging.info(f"🔍 NDA CHECK for project {project_id}")
        logging.info(f"{'='*50}")
        
        result = super().check_and_sign_nda(project_id)
        
        if result:
            self.test_results['signed_ndas'].append(project_id)
            logging.info(f"✅ NDA handled successfully for project {project_id}")
        else:
            logging.info(f"❌ NDA handling failed for project {project_id}")
            
        return result
    
    def check_and_sign_ip_agreement(self, project_id: int) -> bool:
        """Override to add detailed logging"""
        logging.info(f"\n{'='*50}")
        logging.info(f"🔍 IP AGREEMENT CHECK for project {project_id}")
        logging.info(f"{'='*50}")
        
        result = super().check_and_sign_ip_agreement(project_id)
        
        if result:
            self.test_results['signed_ips'].append(project_id)
            logging.info(f"✅ IP agreement handled successfully for project {project_id}")
        else:
            logging.info(f"❌ IP agreement handling failed for project {project_id}")
            
        return result
    
    def place_bid(self, project: Dict) -> bool:
        """Override to add test mode"""
        project_id = project["id"]
        details = self.get_project_details(project)
        
        # Log project details
        logging.info(f"\n{'*'*60}")
        logging.info(f"📄 PROCESSING: {project['title'][:60]}...")
        logging.info(f"   ID: {project_id}")
        logging.info(f"   URL: https://www.freelancer.com/projects/{project.get('seo_url', '')}")
        
        # Log flags
        if details['is_elite']:
            flags = []
            if details['nda']: 
                flags.append("NDA")
                self.test_results['nda_projects'].append(project_id)
            if details['ip_contract']: 
                flags.append("IP")
                self.test_results['ip_projects'].append(project_id)
            if details['featured']: flags.append("Featured")
            if details['sealed']: flags.append("Sealed")
            if details['urgent']: flags.append("Urgent")
            
            logging.info(f"   🌟 ELITE PROJECT - Flags: {', '.join(flags)}")
        
        # In test mode, ask before bidding
        if hasattr(self, 'test_mode') and self.test_mode:
            if details.get('nda') or details.get('ip_contract'):
                logging.info(f"\n   ⚠️  This project requires: {', '.join(filter(None, ['NDA' if details.get('nda') else None, 'IP Agreement' if details.get('ip_contract') else None]))}")
                
                response = input(f"\n   Place bid on this project? (y/n/q to quit): ").lower()
                if response == 'q':
                    logging.info("Test stopped by user")
                    sys.exit(0)
                elif response != 'y':
                    logging.info("   Skipped by user")
                    return False
        
        # Place the bid
        result = super().place_bid(project)
        
        if result:
            self.test_results['bids_placed'].append(project_id)
            
        return result
    
    def print_test_summary(self):
        """Print summary of test results"""
        logging.info("\n" + "="*60)
        logging.info("TEST SUMMARY")
        logging.info("="*60)
        logging.info(f"Projects with NDA: {len(self.test_results['nda_projects'])}")
        logging.info(f"Projects with IP: {len(self.test_results['ip_projects'])}")
        logging.info(f"NDAs signed: {len(self.test_results['signed_ndas'])}")
        logging.info(f"IP agreements signed: {len(self.test_results['signed_ips'])}")
        logging.info(f"Total bids placed: {len(self.test_results['bids_placed'])}")
        logging.info(f"\nLog file: {log_filename}")


def main():
    """Run the bot in test mode"""
    print("="*60)
    print("BOT TEST MODE - NDA/IP Auto-signing")
    print("="*60)
    print("\nThis will run the actual bot with:")
    print("- Enhanced logging for NDA/IP detection")
    print("- Interactive mode for NDA/IP projects")
    print("- All actions logged to file")
    print(f"\nLog file: {log_filename}")
    
    print("\n⚠️  WARNING: This will actually sign NDAs/IPs if you approve!")
    
    if input("\nContinue? (y/n): ").lower() != 'y':
        print("Test cancelled.")
        return
    
    try:
        # Create and run test bot
        bot = TestBot()
        
        # Run for a limited time or number of projects
        print("\nStarting bot in test mode...")
        print("Press Ctrl+C to stop and see summary\n")
        
        # Override the main loop for testing
        bot.realtime_monitor_with_bidding()
        
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
        if 'bot' in locals():
            bot.print_test_summary()
    except Exception as e:
        print(f"\nError: {e}")
        if 'bot' in locals():
            bot.print_test_summary()


if __name__ == "__main__":
    main()