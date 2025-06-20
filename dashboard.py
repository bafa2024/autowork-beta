#!/usr/bin/env python3
"""
Web Dashboard for AutoWork Bot Monitoring
"""

import os
import json
import redis
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# Redis connection (optional - for shared state between worker and dashboard)
REDIS_URL = os.environ.get('REDIS_URL')
redis_client = None

if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        print("✓ Connected to Redis")
    except Exception as e:
        print(f"Redis connection failed: {e}")
        redis_client = None

# Freelancer API setup
FREELANCER_TOKEN = os.environ.get('FREELANCER_OAUTH_TOKEN')
FREELANCER_USER_ID = os.environ.get('FREELANCER_USER_ID', '45214417')
API_BASE = "https://www.freelancer.com/api"

def get_headers():
    return {
        "Freelancer-OAuth-V1": FREELANCER_TOKEN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

def get_bot_stats():
    """Get bot statistics from Redis or default values"""
    if redis_client:
        try:
            stats = {
                'total_bids': int(redis_client.get('total_bids') or 0),
                'bids_today': int(redis_client.get('bids_today') or 0),
                'last_bid_time': redis_client.get('last_bid_time') or 'Never',
                'bot_status': redis_client.get('bot_status') or 'Unknown',
                'processed_projects': int(redis_client.get('processed_projects_count') or 0),
                'uptime': redis_client.get('bot_uptime') or 'Unknown',
                'last_error': redis_client.get('last_error') or 'None',
                'success_rate': float(redis_client.get('success_rate') or 0)
            }
            
            # Get recent bids
            recent_bids = []
            bid_keys = redis_client.keys('bid:*')
            for key in sorted(bid_keys, reverse=True)[:10]:
                bid_data = redis_client.get(key)
                if bid_data:
                    recent_bids.append(json.loads(bid_data))
            stats['recent_bids'] = recent_bids
            
            return stats
        except Exception as e:
            print(f"Error getting stats from Redis: {e}")
    
    # Default stats if Redis not available
    return {
        'total_bids': 0,
        'bids_today': 0,
        'last_bid_time': 'Not available',
        'bot_status': 'Redis not connected',
        'processed_projects': 0,
        'uptime': 'Unknown',
        'last_error': 'None',
        'success_rate': 0,
        'recent_bids': []
    }

def get_account_info():
    """Get Freelancer account information"""
    if not FREELANCER_TOKEN:
        return {'error': 'Token not configured'}
    
    try:
        # Get user info
        response = requests.get(
            f"{API_BASE}/users/0.1/users/{FREELANCER_USER_ID}",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            user = data.get('result', {})
            return {
                'username': user.get('username', 'Unknown'),
                'display_name': user.get('display_name', 'Unknown'),
                'membership': user.get('membership_package', {}).get('name', 'Free'),
                'balance': user.get('balance', {}).get('amount', 0),
                'currency': user.get('balance', {}).get('currency', 'USD'),
                'reputation': user.get('reputation', {}).get('entire_history', {}).get('overall', 0)
            }
        else:
            return {'error': f'API error: {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}

def get_recent_projects():
    """Get recent projects from Freelancer"""
    if not FREELANCER_TOKEN:
        return []
    
    try:
        response = requests.get(
            f"{API_BASE}/projects/0.1/projects/active",
            headers=get_headers(),
            params={'limit': 10, 'job_details': 'true'}
        )
        
        if response.status_code == 200:
            data = response.json()
            projects = data.get('result', {}).get('projects', [])
            return [{
                'id': p['id'],
                'title': p['title'],
                'budget': f"{p['budget']['minimum']} - {p['budget']['maximum']} {p['currency']['code']}",
                'bids': p['bid_stats']['bid_count'],
                'skills': ', '.join([j['name'] for j in p.get('jobs', [])[:3]]),
                'time_posted': p['time_submitted']
            } for p in projects[:5]]
        else:
            return []
    except Exception as e:
        print(f"Error fetching projects: {e}")
        return []

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        # Fallback if template not found
        return f"""
        <html>
        <body>
            <h1>Error Loading Dashboard</h1>
            <p>Could not load dashboard template: {str(e)}</p>
            <p>Make sure templates/dashboard.html exists</p>
            <p><a href="/api/stats">View Raw Stats</a></p>
        </body>
        </html>
        """, 500

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard stats"""
    try:
        stats = get_bot_stats()
        account = get_account_info()
        recent_projects = get_recent_projects()
        
        return jsonify({
            'stats': stats,
            'account': account,
            'recent_projects': recent_projects,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'stats': get_bot_stats(),
            'account': {'error': 'Failed to load'},
            'recent_projects': []
        }), 200  # Return 200 to avoid breaking the dashboard

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'redis_connected': redis_client is not None,
        'token_configured': FREELANCER_TOKEN is not None
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)