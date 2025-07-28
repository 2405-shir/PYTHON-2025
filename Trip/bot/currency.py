import json
import os
import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict

class CurrencyConverter:
    def __init__(self, rates_file: str = "data/exchange_rates.json"):
        self.rates_file = rates_file
        self.rates = {}
        self.last_updated = None
        self.load_rates()
    
    def load_rates(self):
        """Load exchange rates from file"""
        try:
            if os.path.exists(self.rates_file):
                with open(self.rates_file, 'r') as f:
                    data = json.load(f)
                    self.rates = data.get('rates', {})
                    self.last_updated = data.get('last_updated')
        except (json.JSONDecodeError, FileNotFoundError):
            # Use default rates if file doesn't exist
            self.set_default_rates()
    
    def save_rates(self):
        """Save exchange rates to file"""
        try:
            os.makedirs(os.path.dirname(self.rates_file), exist_ok=True)
            data = {
                'rates': self.rates,
                'last_updated': self.last_updated,
                'base_currency': 'CNY'
            }
            with open(self.rates_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving rates: {e}")
    
    def set_default_rates(self):
        """Set default exchange rates (fallback)"""
        # Default rates from CNY (Chinese Yuan/RMB) to other currencies
        # These are approximate rates and should be updated with real API
        self.rates = {
            'GBP': 0.11,  # CNY to GBP (British Pound) for Sunil
            'AED': 0.52,  # CNY to AED (UAE Dirham) for Shirin
            'USD': 0.14,  # CNY to USD for reference
            'EUR': 0.13   # CNY to EUR for reference
        }
        self.last_updated = datetime.now().isoformat()
        self.save_rates()
    
    async def fetch_live_rates(self) -> bool:
        """Fetch live exchange rates from multiple free APIs"""
        try:
            # Try exchangerate-api.com first (free tier, no key needed for basic usage)
            url = "https://api.exchangerate-api.com/v4/latest/CNY"
            
            # Make async request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, timeout=10)
            )
            
            if response.status_code == 200:
                data = response.json()
                rates_data = data.get('rates', {})
                
                # Extract rates we need
                self.rates = {
                    'GBP': rates_data.get('GBP', self.rates.get('GBP', 0.11)),
                    'AED': rates_data.get('AED', self.rates.get('AED', 0.52)),
                    'USD': rates_data.get('USD', self.rates.get('USD', 0.14)),
                    'EUR': rates_data.get('EUR', self.rates.get('EUR', 0.13))
                }
                
                self.last_updated = datetime.now().isoformat()
                self.save_rates()
                print(f"✅ Live exchange rates updated: 1 CNY = {self.rates['GBP']:.4f} GBP, {self.rates['AED']:.4f} AED")
                return True
            else:
                print(f"❌ HTTP error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error fetching rates: {e}")
        except Exception as e:
            print(f"❌ Error fetching rates: {e}")
        
        # Try backup API if first one fails
        try:
            backup_url = "https://open.er-api.com/v6/latest/CNY"
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(backup_url, timeout=10)
            )
            
            if response.status_code == 200:
                data = response.json()
                rates_data = data.get('rates', {})
                
                self.rates = {
                    'GBP': rates_data.get('GBP', self.rates.get('GBP', 0.11)),
                    'AED': rates_data.get('AED', self.rates.get('AED', 0.52)),
                    'USD': rates_data.get('USD', self.rates.get('USD', 0.14)),
                    'EUR': rates_data.get('EUR', self.rates.get('EUR', 0.13))
                }
                
                self.last_updated = datetime.now().isoformat()
                self.save_rates()
                print(f"✅ Backup API rates updated: 1 CNY = {self.rates['GBP']:.4f} GBP, {self.rates['AED']:.4f} AED")
                return True
        except Exception as e:
            print(f"❌ Backup API also failed: {e}")
        
        return False
    
    async def update_rates(self) -> bool:
        """Update rates if they're stale (older than 24 hours)"""
        if self.should_update_rates():
            success = await self.fetch_live_rates()
            if not success:
                print("⚠️ Using cached/default exchange rates")
            return success
        return True
    
    def should_update_rates(self) -> bool:
        """Check if rates should be updated"""
        if not self.last_updated:
            return True
        
        try:
            last_update = datetime.fromisoformat(self.last_updated)
            time_diff = datetime.now() - last_update
            # Update if rates are older than 4 hours for more real-time accuracy
            return time_diff > timedelta(hours=4)
        except ValueError:
            return True
    
    async def get_rates(self) -> Dict[str, float]:
        """Get current exchange rates"""
        await self.update_rates()
        return self.rates
    
    def convert_rmb_to_gbp(self, amount_rmb: float) -> float:
        """Convert RMB to GBP for Sunil"""
        return amount_rmb * self.rates.get('GBP', 0.11)
    
    def convert_rmb_to_aed(self, amount_rmb: float) -> float:
        """Convert RMB to AED for Shirin"""
        return amount_rmb * self.rates.get('AED', 0.52)
    
    def get_rate_info(self) -> Dict:
        """Get rate information for display"""
        return {
            'rates': self.rates,
            'last_updated': self.last_updated,
            'base_currency': 'CNY (Chinese Yuan/RMB)'
        }
