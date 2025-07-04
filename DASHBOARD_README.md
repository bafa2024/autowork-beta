# AutoWork Bot Dashboard

A beautiful, real-time web dashboard for monitoring your AutoWork bot's performance and statistics.

## Features

### 📊 Real-time Statistics
- **Total Bids**: All-time bid count
- **Today's Bids**: Bids placed today
- **Success Rate**: Percentage of successful bids
- **Projects Processed**: Unique projects analyzed
- **Elite Bids**: Bids on elite projects
- **Win Rate**: Projects awarded percentage
- **Projects Filtered**: Projects skipped by filters

### 🤖 Bot Status Monitoring
- **Live Status**: Real-time bot running status
- **Last Bid Time**: When the last bid was placed
- **Uptime**: How long the bot has been running
- **Last Error**: Most recent error encountered

### 💰 Account Information
- **Username**: Your Freelancer username
- **Balance**: Current account balance
- **Membership**: Account membership level
- **Reputation**: Overall reputation score

### 📋 Recent Activity
- **Recent Projects**: Latest projects from Freelancer
- **Recent Bids**: Your latest bid placements with status

## Quick Start

### 1. Install Requirements
```bash
pip install flask requests python-dotenv redis
```

### 2. Set Environment Variables
Create a `.env` file with your configuration:

```env
# Required for full functionality
FREELANCER_OAUTH_TOKEN=your_freelancer_token_here
FREELANCER_USER_ID=your_user_id_here

# Optional - for live bot data
REDIS_URL=redis://localhost:6379

# Optional - dashboard configuration
PORT=5000
HOST=127.0.0.1
FLASK_DEBUG=0
```

### 3. Start the Dashboard

#### Option A: Using the startup script (Recommended)
```bash
python start_dashboard.py
```

#### Option B: Direct start
```bash
python dashboard.py
```

### 4. Access the Dashboard
Open your browser and go to: `http://localhost:5000`

## Dashboard Modes

### Full Functionality Mode
- **Requirements**: Freelancer token + Redis
- **Features**: All statistics, live bot data, account info, recent projects
- **Best for**: Production monitoring

### Basic Mode
- **Requirements**: Freelancer token only
- **Features**: Account info, recent projects (no live bot stats)
- **Best for**: Account monitoring without bot

### Minimal Mode
- **Requirements**: None
- **Features**: Dashboard interface only (all stats show zero)
- **Best for**: Testing dashboard functionality

## API Endpoints

### Main Dashboard
- `GET /` - Main dashboard page

### API Endpoints
- `GET /api/stats` - Get all dashboard statistics
- `GET /api/health` - Health check endpoint

### Example API Response
```json
{
  "stats": {
    "total_bids": 25,
    "bids_today": 5,
    "success_rate": 12.0,
    "processed_projects": 150,
    "elite_bids": 8,
    "win_rate": 8.0,
    "filtered_projects": 125,
    "bot_status": "Running - Ultra Simple Filtering Mode",
    "last_bid_time": "2024-01-15T10:30:00",
    "uptime": "2:15:30",
    "last_error": "None",
    "recent_bids": [...]
  },
  "account": {
    "username": "your_username",
    "balance": 150.50,
    "currency": "USD",
    "membership": "Basic",
    "reputation": 4.8
  },
  "recent_projects": [...],
  "timestamp": "2024-01-15T10:30:00"
}
```

## Integration with Bot

The dashboard automatically connects to your AutoWork bot when:

1. **Redis is configured**: The bot saves statistics to Redis
2. **Bot is running**: Status updates in real-time
3. **Same environment**: Both dashboard and bot use same Redis instance

### Bot Data Flow
```
AutoWork Bot → Redis → Dashboard → Web Interface
```

### Redis Keys Used
- `bid_count` - Total bids placed
- `bids_today` - Today's bid count
- `wins_count` - Successful bids
- `elite_bid_count` - Elite project bids
- `bot_status` - Current bot status
- `last_update` - Last update timestamp
- `bot_start_time` - Bot start time
- `processed_projects` - List of processed project IDs
- `skipped_projects` - Filtering statistics
- `bid:*` - Recent bid details

## Troubleshooting

### Dashboard Shows Zero Stats
- **Cause**: No Redis connection or bot not running
- **Solution**: Start the bot or configure Redis

### Account Info Shows Error
- **Cause**: Missing or invalid Freelancer token
- **Solution**: Check your `FREELANCER_OAUTH_TOKEN` environment variable

### Recent Projects Empty
- **Cause**: No Freelancer token or API issues
- **Solution**: Verify token and check API connectivity

### Dashboard Won't Start
- **Cause**: Missing dependencies or port conflicts
- **Solution**: Install requirements and check port availability

### Redis Connection Issues
- **Cause**: Redis not running or wrong URL
- **Solution**: Start Redis server or update `REDIS_URL`

## Customization

### Styling
The dashboard uses a modern dark theme with CSS animations. To customize:
1. Edit `templates/dashboard.html`
2. Modify the `<style>` section
3. Restart the dashboard

### Adding New Stats
To add new statistics:
1. Update `get_bot_stats()` in `dashboard.py`
2. Add corresponding HTML elements in the template
3. Update JavaScript to display the new data

### Custom Endpoints
Add new API endpoints in `dashboard.py`:
```python
@app.route('/api/custom')
def custom_endpoint():
    return jsonify({'data': 'your_data'})
```

## Security Notes

- The dashboard runs on localhost by default
- For production, use proper authentication
- Don't expose sensitive tokens in logs
- Use HTTPS in production environments

## Performance

- **Auto-refresh**: Every 30 seconds
- **Data retention**: Recent bids kept for 24 hours
- **Memory usage**: Minimal (statistics only)
- **CPU usage**: Very low (static file serving)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify environment variables
3. Test with the startup script
4. Check bot logs for errors

---

**Dashboard Version**: 2.0  
**Compatible Bot Version**: AutoWork Minimal v2.0+  
**Last Updated**: January 2024 