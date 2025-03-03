"""
Price Fetcher Module

This module fetches current and historical price data for cryptocurrencies
from the KuCoin API. Future versions will include IBKR for stocks.
"""

import os
import json
import time
import logging
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('price_fetcher')

class PriceFetcher:
    """Fetches and stores price data for configured assets."""
    
    def __init__(self, config_path: str, assets_path: str, storage_path: str):
        """
        Initialize the PriceFetcher.
        
        Args:
            config_path: Path to the settings.yaml file
            assets_path: Path to the assets.yaml file
            storage_path: Path to store the price data
        """
        self.config_path = config_path
        self.assets_path = assets_path
        self.storage_path = storage_path
        
        # Load configurations
        self.config = self._load_yaml(config_path)
        self.assets = self._load_yaml(assets_path)
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Initialize API credentials (dummy values for now)
        self.kucoin_api_key = self.config.get('apis', {}).get('kucoin', {}).get('api_key', '')
        self.kucoin_api_secret = self.config.get('apis', {}).get('kucoin', {}).get('api_secret', '')
        self.kucoin_api_passphrase = self.config.get('apis', {}).get('kucoin', {}).get('api_passphrase', '')
        self.kucoin_sandbox = self.config.get('apis', {}).get('kucoin', {}).get('sandbox_mode', True)
        
    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return {}
    
    def _get_kucoin_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current price data for a cryptocurrency from KuCoin.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., BTC, ETH)
            
        Returns:
            Price data dictionary or None if request fails
        """
        # NOTE: This is a dummy implementation
        # In a real implementation, we would use the KuCoin API client
        
        logger.info(f"Fetching KuCoin price for {symbol}")
        
        # For demonstration, return dummy price data
        dummy_prices = {
            "BTC": 67890.42,
            "ETH": 3456.78,
            "SOL": 123.45
        }
        
        if symbol in dummy_prices:
            current_time = datetime.now().isoformat()
            return {
                "symbol": symbol,
                "price": dummy_prices[symbol],
                "timestamp": current_time,
                "source": "kucoin",
                "volume_24h": 123456789.0,
                "change_24h_percent": 2.5
            }
        
        return None

    def _get_kucoin_historical_prices(self, symbol: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """
        Get historical price data for a cryptocurrency from KuCoin.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., BTC, ETH)
            days: Number of days of historical data to fetch
            
        Returns:
            List of historical price data points or None if request fails
        """
        # NOTE: This is a dummy implementation
        logger.info(f"Fetching KuCoin historical prices for {symbol}, {days} days")
        
        # Generate dummy historical data
        historical_data = []
        base_prices = {
            "BTC": 65000,
            "ETH": 3300,
            "SOL": 120
        }
        
        if symbol in base_prices:
            base_price = base_prices[symbol]
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                # Create some random price movement
                price_change = (i % 5 - 2) * (base_price * 0.01)
                price = base_price + price_change
                
                historical_data.append({
                    "symbol": symbol,
                    "date": date.strftime("%Y-%m-%d"),
                    "timestamp": date.isoformat(),
                    "open": price - (price * 0.005),
                    "high": price + (price * 0.01),
                    "low": price - (price * 0.01),
                    "close": price,
                    "volume": 1000000 + (i * 10000),
                    "source": "kucoin"
                })
            
            # Sort by date ascending
            historical_data.sort(key=lambda x: x["date"])
            return historical_data
        
        return None
        
    def _save_price_data(self, symbol: str, price_data: Dict[str, Any]) -> bool:
        """
        Save current price data to storage.
        
        Args:
            symbol: Asset symbol
            price_data: Price data to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            file_path = os.path.join(self.storage_path, f"{symbol}_current_{date_str}.json")
            
            with open(file_path, 'w') as file:
                json.dump(price_data, file, indent=2)
            
            logger.info(f"Saved current price data for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Error saving price data for {symbol}: {e}")
            return False
            
    def _save_historical_data(self, symbol: str, historical_data: List[Dict[str, Any]]) -> bool:
        """
        Save historical price data to storage.
        
        Args:
            symbol: Asset symbol
            historical_data: Historical price data to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            file_path = os.path.join(self.storage_path, f"{symbol}_historical_{date_str}.json")
            
            with open(file_path, 'w') as file:
                json.dump(historical_data, file, indent=2)
            
            logger.info(f"Saved historical price data for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Error saving historical data for {symbol}: {e}")
            return False
    
    def fetch_crypto_prices(self) -> Dict[str, Any]:
        """
        Fetch current prices for all cryptocurrencies in the assets config.
        
        Returns:
            Dictionary of symbol -> price data
        """
        results = {}
        
        crypto_assets = self.assets.get('crypto', [])
        for asset in crypto_assets:
            symbol = asset.get('symbol')
            if not symbol:
                continue
                
            price_data = self._get_kucoin_price(symbol)
            if price_data:
                results[symbol] = price_data
                self._save_price_data(symbol, price_data)
                
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
            
        return results
        
    def fetch_crypto_historical(self, days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch historical prices for all cryptocurrencies in the assets config.
        
        Args:
            days: Number of days of historical data to fetch
            
        Returns:
            Dictionary of symbol -> historical price data list
        """
        results = {}
        
        crypto_assets = self.assets.get('crypto', [])
        for asset in crypto_assets:
            symbol = asset.get('symbol')
            if not symbol:
                continue
                
            historical_data = self._get_kucoin_historical_prices(symbol, days)
            if historical_data:
                results[symbol] = historical_data
                self._save_historical_data(symbol, historical_data)
                
            # Add a small delay to avoid rate limiting
            time.sleep(1)
            
        return results
    
    def get_latest_prices(self) -> Dict[str, Any]:
        """
        Get the most recently saved prices for all assets.
        
        Returns:
            Dictionary of symbol -> latest price data
        """
        results = {}
        
        for filename in os.listdir(self.storage_path):
            if "_current_" in filename and filename.endswith('.json'):
                symbol = filename.split('_')[0]
                try:
                    with open(os.path.join(self.storage_path, filename), 'r') as file:
                        results[symbol] = json.load(file)
                except Exception as e:
                    logger.error(f"Error loading price data from {filename}: {e}")
        
        return results

# Example usage
if __name__ == "__main__":
    # This is for testing the module directly
    fetcher = PriceFetcher(
        config_path="../config/settings.yaml",
        assets_path="../config/assets.yaml",
        storage_path="../data/prices"
    )
    
    # Fetch current prices
    current_prices = fetcher.fetch_crypto_prices()
    print(f"Fetched current prices for {len(current_prices)} cryptocurrencies")
    
    # Fetch historical prices
    historical_prices = fetcher.fetch_crypto_historical(days=7)
    print(f"Fetched historical prices for {len(historical_prices)} cryptocurrencies")