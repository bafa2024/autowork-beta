#!/usr/bin/env python3
"""
Create dummy files to fix import errors
Run this to create placeholder files
"""

import os

# Create currency_converter_freelancer.py if it doesn't exist
if not os.path.exists('currency_converter_freelancer.py'):
    with open('currency_converter_freelancer.py', 'w') as f:
        f.write('''
class CurrencyConverter:
    def __init__(self, freelancer_token=None):
        self.rates = {'USD': 1.0}
    
    def to_usd(self, amount, currency_code):
        # Simple conversion - just return amount for now
        return amount
    
    def format_budget_info(self, amount, currency_code):
        return f"{currency_code} {amount:.2f}"
''')
    print("✓ Created currency_converter_freelancer.py")

# Create spam_filter.py if it doesn't exist
if not os.path.exists('spam_filter.py'):
    with open('spam_filter.py', 'w') as f:
        f.write('''
class SpamFilter:
    def __init__(self):
        pass
    
    def is_spam(self, project):
        return False, []
    
    def get_stats(self):
        return {'total_checked': 0, 'spam_detected': 0, 'spam_rate': 0, 'top_reasons': []}
''')
    print("✓ Created spam_filter.py")

# Create contest_handler.py if it doesn't exist
if not os.path.exists('contest_handler.py'):
    with open('contest_handler.py', 'w') as f:
        f.write('''
class ContestHandler:
    def __init__(self, token, user_id):
        self.processed_contests = set()
        self.entered_contests = set()
        self.contest_entries = {}
    
    def get_active_contests(self, limit=50):
        return []
    
    def should_enter_contest(self, contest, config):
        return False, "Contests disabled"
    
    def create_contest_entry(self, contest, config):
        return None
    
    def submit_contest_entry(self, contest_id, entry_data):
        return False
    
    def save_contest_state(self):
        pass
    
    def check_contest_results(self):
        pass
    
    def get_contest_summary(self):
        return {'total_entered': 0, 'total_wins': 0, 'win_rate': 0, 'total_prize_money': 0}
''')
    print("✓ Created contest_handler.py")

print("\n✅ All required files created!")
print("You can now run: python autowork_minimal.py")