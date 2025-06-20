#!/usr/bin/env python3
"""
Web Dashboard for AutoWork Bot
Provides a simple interface to view bot statistics
"""

from flask import Flask, jsonify, render_template_string
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AutoWork Bot Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .status {
            padding: 10px;
            background: #4CAF50;
            color: white;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .error {
            background: #f44336;
        }
    </style>
    <script>
        function refreshStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-projects').textContent = data.total_projects;
                    document.getElementById('total-bids').textContent = data.total_bids;
                    document.getElementById('success-rate').textContent = data.success_rate + '%';
                    document.getElementById('today-bids').textContent = data.today_bids;
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                });
        }
        
        setInterval(refreshStats, 30000); // Refresh every 30 seconds
    </script>
</head>
<body>
    <div class="container">
        <h1>🤖 AutoWork Bot Dashboard</h1>
        
        <div class="status">
            Bot Status: <strong>{{ status }}</strong> | 
            Last Update: <span id="last-update">{{ last_update }}</span>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="total-projects">{{ stats.total_projects }}</div>
                <div class="stat-label">Total Projects Tracked</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value" id="total-bids">{{ stats.total_bids }}</div>
                <div class="stat-label">Total Bids Placed</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value" id="success-rate">{{ stats.success_rate }}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value" id="today-bids">{{ stats.today_bids }}</div>
                <div class="stat-label">Bids Today</div>
            </div>
        </div>
        
        <div style="margin-top: 40px; text-align: center; color: #666;">
            <p>AutoWork Bot v2.0 - No Filters Edition</p>
            <p>Monitoring and bidding on all matching projects 24/7</p>
        </div>
    </div>
</body>
</html>
"""

def get_db_stats():
    """Get statistics from database"""
    stats = {
        'total_projects': 0,
        'total_bids': 0,
        'success_rate': 0,
        'today_bids': 0
    }
    
    try:
        # Check if database exists
        if not os.path.exists('autowork.db'):
            return stats
            
        conn = sqlite3.connect('autowork.db')
        cursor = conn.cursor()
        
        # Total projects
        cursor.execute("SELECT COUNT(*) FROM projects")
        stats['total_projects'] = cursor.fetchone()[0]
        
        # Total bids
        cursor.execute("SELECT COUNT(*) FROM bids")
        stats['total_bids'] = cursor.fetchone()[0]
        
        # Success rate
        cursor.execute("SELECT COUNT(*) FROM bids WHERE status = 'success'")
        successful = cursor.fetchone()[0]
        if stats['total_bids'] > 0:
            stats['success_rate'] = round((successful / stats['total_bids']) * 100, 1)
        
        # Today's bids
        cursor.execute("""
            SELECT COUNT(*) FROM bids 
            WHERE created_at > datetime('now', '-1 day')
        """)
        stats['today_bids'] = cursor.fetchone()[0]
        
        conn.close()
        
    except Exception as e:
        print(f"Database error: {e}")
    
    return stats

@app.route('/')
def dashboard():
    """Main dashboard page"""
    stats = get_db_stats()
    return render_template_string(
        HTML_TEMPLATE,
        status="Running" if os.environ.get('RENDER') else "Local",
        last_update=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        stats=stats
    )

@app.route('/api/stats')
def api_stats():
    """API endpoint for stats"""
    return jsonify(get_db_stats())

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)