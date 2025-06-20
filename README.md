# AutoWork Freelancer Bot - Minimal Version

A lightweight automated bidding bot for Freelancer.com with no external dependencies.

## Features

- 🤖 Real-time project monitoring
- 🎯 Automatic bidding on ALL matching projects
- 📊 No filters - maximum opportunity
- 🔄 Rate limit protection
- ☁️ Render cloud-ready

## Quick Start

### Local Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/autowork-freelancer-bot.git
cd autowork-freelancer-bot

# Install minimal dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your Freelancer OAuth token

# Run the bot
python autowork_minimal.py