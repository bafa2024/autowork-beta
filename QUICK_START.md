# Quick Start Guide - AutoWork Minimal Bot

## 🚀 Get Started in 3 Steps

### Step 1: Set Your Token
```bash
# Windows (PowerShell)
$env:FREELANCER_OAUTH_TOKEN="your_token_here"

# Windows (Command Prompt)
set FREELANCER_OAUTH_TOKEN=your_token_here

# Linux/Mac
export FREELANCER_OAUTH_TOKEN="your_token_here"
```

### Step 2: Test the Bot
```bash
python test_minimal_bot.py
```
This will verify everything is working correctly.

### Step 3: Run the Bot
```bash
python autowork_minimal.py
```

## 🔧 What the Bot Does

The AutoWork Minimal Bot automatically:

1. **Scans** for new projects on Freelancer
2. **Filters** for high-quality projects only
3. **Analyzes** client reputation and project requirements
4. **Calculates** optimal bid amounts
5. **Places** professional bids automatically
6. **Tracks** performance and success rates

## 📊 Bot Features

### Smart Filtering
- ✅ Only bids on quality projects (score > 50)
- ✅ Filters out spam and low-budget projects
- ✅ Verifies client payment status
- ✅ Matches your skills and specializations

### Intelligent Bidding
- ✅ Adjusts bid amounts based on project type
- ✅ Considers competition level
- ✅ Uses professional bid messages
- ✅ Respects daily bid limits

### Performance Tracking
- ✅ Tracks win rates and success metrics
- ✅ Logs all activities for analysis
- ✅ Saves state between runs (with Redis)

## ⚙️ Configuration

Edit `bot_config.json` to customize:

```json
{
  "bidding": {
    "delivery_days": 3,
    "bid_multiplier_regular": 1.15,
    "default_bid_regular": 150
  },
  "filtering": {
    "max_projects_per_cycle": 50,
    "skip_projects_with_bids_above": 30
  },
  "monitoring": {
    "daily_bid_limit": 30,
    "check_interval_seconds": 30
  }
}
```

## 🛠️ Troubleshooting

### Common Issues

**"Token validation failed"**
- Make sure your token is valid and not expired
- Get a new token from: https://www.freelancer.com/api/docs/

**"Redis connection failed"**
- This is normal if Redis isn't running
- The bot works fine without Redis (just won't save state)

**"No projects fetched"**
- Check your internet connection
- Verify your token has proper permissions

### Logs
The bot provides detailed logging. Look for:
- ✅ Success messages
- ⚠️ Warnings (usually safe to ignore)
- ❌ Errors (need attention)

## 📈 Monitoring

The bot logs its activities in real-time. Key metrics to watch:

- **Bids placed**: Number of successful bids
- **Quality projects found**: Projects that passed filters
- **Win rate**: Percentage of bids that won
- **Filtered projects**: Projects that were rejected and why

## 🔒 Safety Features

- **Daily limits**: Prevents over-bidding
- **Rate limiting**: Respects API limits
- **Error recovery**: Continues running after errors
- **Quality filters**: Only bids on good projects

## 🎯 Tips for Success

1. **Start conservatively**: Begin with low daily limits
2. **Monitor logs**: Watch for patterns in filtered projects
3. **Adjust filters**: Tune quality thresholds based on results
4. **Update messages**: Customize bid messages in `bid_messages.json`
5. **Review performance**: Analyze win rates and adjust strategy

## 🆘 Need Help?

1. Check the logs for error messages
2. Verify your token is valid
3. Test with `python test_minimal_bot.py`
4. Review the configuration in `bot_config.json`

The bot is designed to be safe and conservative by default. It will only bid on projects that meet strict quality criteria, helping you focus on the best opportunities! 