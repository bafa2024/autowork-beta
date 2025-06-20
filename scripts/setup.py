#!/usr/bin/env python3
"""
Setup and maintenance scripts
"""

import sys
import os
import sqlite3
from datetime import datetime

def show_stats():
    """Show current statistics"""
    if not os.path.exists('autowork.db'):
        print("No database found")
        return
        
    conn = sqlite3.connect('autowork.db')
    cursor = conn.cursor()
    
    print("\n=== AutoWork Statistics ===")
    print(f"Generated at: {datetime.now()}")
    
    # Get stats
    cursor.execute("SELECT COUNT(*) FROM projects")
    projects = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bids")
    bids = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bids WHERE status = 'success'")
    successful = cursor.fetchone()[0]
    
    print(f"\nTotal Projects: {projects}")
    print(f"Total Bids: {bids}")
    print(f"Successful Bids: {successful}")
    
    if bids > 0:
        print(f"Success Rate: {(successful/bids)*100:.1f}%")
    
    conn.close()

def cleanup_old_data():
    """Clean up old data"""
    if not os.path.exists('autowork.db'):
        return
        
    conn = sqlite3.connect('autowork.db')
    cursor = conn.cursor()
    
    # Delete projects older than 7 days
    cursor.execute("""
        DELETE FROM projects 
        WHERE created_at < datetime('now', '-7 days')
    """)
    
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"Cleaned up {deleted} old projects")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        show_stats()
    elif len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        cleanup_old_data()
    else:
        print("Usage: python setup.py [--stats|--cleanup]")