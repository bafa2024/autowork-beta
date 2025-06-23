#!/usr/bin/env python3
"""
Currency converter that uses Freelancer's own exchange rates
This is the most accurate for Freelancer projects
"""

import requests
import json
import os
import logging
from datetime import datetime, timedelta

class CurrencyConverter:
    def __init__(self, freelancer_token=None):
        self.token = freelancer_token or os.environ.get('FREELANCER_OAUTH_TOKEN')
        self.api_base = "https://www.freelancer.com/api"
        self.rates = {}
        self.cache_file = "freelancer_currencies.json"
        self.last_update = None
        
        # Try to load from cache first
        self.load_cache()
        
        # Update if cache is old or empty
        if self.should_update():
            self.update_from_freelancer()
    
    def load_cache(self):
        """Load cached currency data"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.rates = data.get('rates', {})
                    last_update = data.get('last_update')
                    if last_update:
                        self.last_update = datetime.fromisoformat(last_update)
                logging.info("Loaded Freelancer currency cache")
        except Exception as e:
            logging.debug(f"Could not load cache: {e}")
    
    def save_cache(self):
        """Save currency data to cache"""
        try:
            data = {
                'rates': self.rates,
                'last_update': datetime.now().isoformat()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.warning(f"Could not save cache: {e}")
    
    def should_update(self):
        """Check if we should update rates"""
        if not self.rates:
            return True
        if not self.last_update:
            return True
        # Update once per day
        return datetime.now() - self.last_update > timedelta(days=1)
    
    def update_from_freelancer(self):
        """Get currency data from Freelancer API"""
        if not self.token:
            logging.warning("No Freelancer token available for currency update")
            return False
        
        try:
            headers = {
                "Freelancer-OAuth-V1": self.token,
                "Accept": "application/json"
            }
            
            # Freelancer provides currency exchange rates in their API
            response = requests.get(
                f"{self.api_base}/projects/0.1/currencies",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                currencies = data.get('result', {}).get('currencies', [])
                
                # Build exchange rate table
                for currency in currencies:
                    code = currency.get('code')
                    exchange_rate = currency.get('exchange_rate', 1.0)
                    if code and exchange_rate:
                        self.rates[code] = exchange_rate
                
                self.last_update = datetime.now()
                self.save_cache()
                logging.info(f"Updated {len(self.rates)} currency rates from Freelancer")
                return True
                
        except Exception as e:
            logging.warning(f"Could not update from Freelancer API: {e}")
        
        # If Freelancer API fails, use basic rates
        if not self.rates:
            self.use_fallback_rates()
        
        return False
    
    def use_fallback_rates(self):
        """Use basic fallback rates"""
        self.rates = {
            'USD': 1.0,
            'EUR': 0.92,
            'GBP': 0.79,
            'AUD': 1.52,
            'CAD': 1.35,
            'INR': 83.0,
            'PKR': 278.0,
            'PHP': 56.0,
            'BRL': 5.0,
            'MXN': 17.0,
            'JPY': 150.0,
            'CNY': 7.2,
            'ZAR': 18.5,
            'NGN': 450.0,
            'EGP': 31.0,
            'AED': 3.67,
            'SAR': 3.75,
        }
        logging.info("Using fallback exchange rates")
    
    def to_usd(self, amount, currency_code):
        """Convert amount to USD using Freelancer's rates"""
        currency_code = currency_code.upper()
        
        if currency_code == 'USD':
            return amount
        
        # Freelancer's exchange_rate is typically "how many units per USD"
        # So to convert to USD: amount / exchange_rate
        if currency_code in self.rates:
            rate = self.rates[currency_code]
            if rate > 0:
                return amount / rate
        
        # If no rate found, just return amount
        logging.warning(f"No exchange rate for {currency_code}")
        return amount
    
    def get_min_budget_for_currency(self, usd_amount, currency_code):
        """Get minimum budget in target currency"""
        currency_code = currency_code.upper()
        
        if currency_code == 'USD':
            return usd_amount
        
        if currency_code in self.rates:
            rate = self.rates[currency_code]
            return usd_amount * rate
        
        return usd_amount
    
    def format_budget_info(self, amount, currency_code):
        """Format budget info with USD equivalent"""
        usd_amount = self.to_usd(amount, currency_code)
        
        if currency_code == 'USD':
            return f"${amount:.2f} USD"
        else:
            return f"{currency_code} {amount:.2f} (${usd_amount:.2f} USD)"