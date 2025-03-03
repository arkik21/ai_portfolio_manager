"""
Price Fetcher Module

This module fetches current and historical price data for cryptocurrencies
from the KuCoin API. Future versions will include IBKR for stocks.
"""
import os
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional
import yaml

from kucoin.client import Client
from kucoin.exceptions import KucoinAPIException, KucoinRequestException

class PriceFetcher:
    """Handler for KuCoin API interactions."""
    
    def __init__(self, config_path: str, assets_path: str, storage_path: str = None):
        """
        Initialize the KuCoin API client.
        
        Args:
            config_path: Path to configuration file containing API credentials
            assets_path: Path to assets configuration file
            storage_path: Path to store price data (optional)
        """
        self.logger = logging.getLogger('price_fetcher')
        self.assets_path = assets_path
        self.storage_path = storage_path
        
        try:
            # Load configuration
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Extract KuCoin credentials
            kucoin_config = config.get('exchanges', {}).get('kucoin', {})
            api_key = kucoin_config.get('api_key')
            api_secret = kucoin_config.get('api_secret')
            api_passphrase = kucoin_config.get('api_passphrase')
            sandbox = kucoin_config.get('sandbox', True)
            
            # Initialize the KuCoin client
            self.client = Client(api_key, api_secret, api_passphrase, sandbox=sandbox)
            self.logger.info("KuCoin client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing KuCoin client: {e}")
            self.client = None
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current price for a trading pair on KuCoin.
        
        Args:
            symbol: Trading pair symbol (e.g., BTC-USDT)
            
        Returns:
            Dictionary with price data or None if request fails
        """
        if not self.client:
            self.logger.error("KuCoin client not initialized")
            return None
            
        try:
            # Format the symbol for KuCoin (add -USDT if not specified)
            kucoin_symbol = symbol if '-' in symbol else f"{symbol}-USDT"
            
            # Get ticker information for the symbol
            ticker = self.client.get_ticker(kucoin_symbol)
            
            # Get 24h stats
            stats = self.client.get_24hr_stats(kucoin_symbol)
            
            # Format the response
            current_time = datetime.now().isoformat()
            return {
                "symbol": symbol,
                "price": float(ticker['price']),
                "timestamp": current_time,
                "source": "kucoin",
                "volume_24h": float(stats['vol']),
                "change_24h_percent": self._calculate_change_percent(stats),
                "raw_data": {
                    "ticker": ticker,
                    "stats": stats
                }
            }
        except KucoinAPIException as e:
            self.logger.error(f"KuCoin API error getting price for {symbol}: {e}")
            return None
        except KucoinRequestException as e:
            self.logger.error(f"KuCoin response error getting price for {symbol}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting price for {symbol}: {e}")
            return None
    
    def _calculate_change_percent(self, stats: Dict[str, Any]) -> float:
        """Calculate 24h price change percentage from stats."""
        try:
            if 'changePrice' in stats and 'last' in stats and float(stats['last']) > 0:
                change_price = float(stats['changePrice'])
                current_price = float(stats['last'])
                previous_price = current_price - change_price
                if previous_price > 0:
                    return (change_price / previous_price) * 100
            elif 'changeRate' in stats:
                # If changeRate is available, use it directly
                return float(stats['changeRate']) * 100
            return 0.0
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def get_historical_prices(self, symbol: str, days: int = 30, interval: str = '1day') -> Optional[List[Dict[str, Any]]]:
        """
        Get historical price data for a symbol from KuCoin.
        
        Args:
            symbol: Trading pair symbol (e.g., BTC-USDT)
            days: Number of days of historical data to fetch
            interval: Kline interval (e.g., 1min, 1hour, 1day)
            
        Returns:
            List of historical price data points or None if request fails
        """
        if not self.client:
            self.logger.error("KuCoin client not initialized")
            return None
            
        try:
            # Format the symbol for KuCoin (add -USDT if not specified)
            kucoin_symbol = symbol if '-' in symbol else f"{symbol}-USDT"
            
            # Calculate start and end time
            end_time = int(datetime.now().timestamp())
            start_time = int((datetime.now() - timedelta(days=days)).timestamp())
            
            # Get kline (candlestick) data
            klines = self.client.get_kline_data(kucoin_symbol, interval, start_time, end_time)
            
            # Format the response
            historical_data = []
            for kline in klines:
                # KuCoin returns klines in the format [timestamp, open, close, high, low, volume, turnover]
                timestamp = datetime.fromtimestamp(kline[0])
                historical_data.append({
                    "symbol": symbol,
                    "date": timestamp.strftime("%Y-%m-%d"),
                    "timestamp": timestamp.isoformat(),
                    "open": float(kline[1]),
                    "close": float(kline[2]),
                    "high": float(kline[3]),
                    "low": float(kline[4]),
                    "volume": float(kline[5]),
                    "source": "kucoin",
                    "raw_data": kline
                })
            
            # Sort by date ascending
            historical_data.sort(key=lambda x: x["date"])
            return historical_data
        except KucoinAPIException as e:
            self.logger.error(f"KuCoin API error getting historical data for {symbol}: {e}")
            return None
        except KucoinRequestException as e:
            self.logger.error(f"KuCoin response error getting historical data for {symbol}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting historical data for {symbol}: {e}")
            return None
    
    def place_market_order(self, symbol: str, side: str, amount: float) -> Optional[Dict[str, Any]]:
        """
        Place a market order on KuCoin.
        
        Args:
            symbol: Trading pair symbol (e.g., BTC-USDT)
            side: Order side (buy or sell)
            amount: Order amount
            
        Returns:
            Dictionary with order result or None if request fails
        """
        if not self.client:
            self.logger.error("KuCoin client not initialized")
            return None
        
        try:
            # Format the symbol for KuCoin (add -USDT if not specified)
            kucoin_symbol = symbol if '-' in symbol else f"{symbol}-USDT"
            
            # Validate the side
            if side.lower() not in [Client.SIDE_BUY, Client.SIDE_SELL]:
                self.logger.error(f"Invalid order side: {side}")
                return None
            
            # Place the market order
            if side.lower() == Client.SIDE_BUY:
                # For buy orders, we specify the amount of the quote currency (USDT)
                response = self.client.create_market_order(
                    kucoin_symbol, 
                    Client.SIDE_BUY, 
                    funds=str(amount)
                )
            else:
                # For sell orders, we specify the amount of the base currency (BTC, ETH, etc.)
                response = self.client.create_market_order(
                    kucoin_symbol, 
                    Client.SIDE_SELL, 
                    size=str(amount)
                )
            
            # Format the response
            return {
                "order_id": response['orderId'],
                "symbol": symbol,
                "type": "market",
                "side": side.lower(),
                "amount": amount,
                "status": "success",
                "exchange": "kucoin",
                "timestamp": datetime.now().isoformat(),
                "raw_data": response
            }
        except KucoinAPIException as e:
            self.logger.error(f"KuCoin API error placing order for {symbol}: {e}")
            return {
                "status": "error",
                "reason": f"KuCoin API error: {str(e)}",
                "symbol": symbol,
                "type": "market",
                "side": side.lower(),
                "amount": amount,
                "exchange": "kucoin",
                "timestamp": datetime.now().isoformat()
            }
        except KucoinRequestException as e:
            self.logger.error(f"KuCoin response error placing order for {symbol}: {e}")
            return {
                "status": "error",
                "reason": f"KuCoin response error: {str(e)}",
                "symbol": symbol,
                "type": "market",
                "side": side.lower(),
                "amount": amount,
                "exchange": "kucoin",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Unexpected error placing order for {symbol}: {e}")
            return {
                "status": "error",
                "reason": f"Unexpected error: {str(e)}",
                "symbol": symbol,
                "type": "market",
                "side": side.lower(),
                "amount": amount,
                "exchange": "kucoin",
                "timestamp": datetime.now().isoformat()
            }
    
    def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict[str, Any]]:
        """
        Place a limit order on KuCoin.
        
        Args:
            symbol: Trading pair symbol (e.g., BTC-USDT)
            side: Order side (buy or sell)
            amount: Order amount (in base currency, e.g., BTC)
            price: Limit price
            
        Returns:
            Dictionary with order result or None if request fails
        """
        if not self.client:
            self.logger.error("KuCoin client not initialized")
            return None
        
        try:
            # Format the symbol for KuCoin (add -USDT if not specified)
            kucoin_symbol = symbol if '-' in symbol else f"{symbol}-USDT"
            
            # Validate the side
            if side.lower() not in [Client.SIDE_BUY, Client.SIDE_SELL]:
                self.logger.error(f"Invalid order side: {side}")
                return None
            
            # Place the limit order
            response = self.client.create_limit_order(
                kucoin_symbol, 
                side.lower(), 
                str(price),
                str(amount)
            )
            
            # Format the response
            return {
                "order_id": response['orderId'],
                "symbol": symbol,
                "type": "limit",
                "side": side.lower(),
                "amount": amount,
                "price": price,
                "status": "success",
                "exchange": "kucoin",
                "timestamp": datetime.now().isoformat(),
                "raw_data": response
            }
        except KucoinAPIException as e:
            self.logger.error(f"KuCoin API error placing limit order for {symbol}: {e}")
            return {
                "status": "error",
                "reason": f"KuCoin API error: {str(e)}",
                "symbol": symbol,
                "type": "limit",
                "side": side.lower(),
                "amount": amount,
                "price": price,
                "exchange": "kucoin",
                "timestamp": datetime.now().isoformat()
            }
        except KucoinRequestException as e:
            self.logger.error(f"KuCoin response error placing limit order for {symbol}: {e}")
            return {
                "status": "error",
                "reason": f"KuCoin response error: {str(e)}",
                "symbol": symbol,
                "type": "limit",
                "side": side.lower(),
                "amount": amount,
                "price": price,
                "exchange": "kucoin",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Unexpected error placing limit order for {symbol}: {e}")
            return {
                "status": "error",
                "reason": f"Unexpected error: {str(e)}",
                "symbol": symbol,
                "type": "limit",
                "side": side.lower(),
                "amount": amount,
                "price": price,
                "exchange": "kucoin",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_account_balance(self) -> Optional[Dict[str, Any]]:
        """
        Get account balance from KuCoin.
        
        Returns:
            Dictionary with balance information or None if request fails
        """
        if not self.client:
            self.logger.error("KuCoin client not initialized")
            return None
        
        try:
            # Get account balances
            accounts = self.client.get_accounts()
            
            # Format the response
            balances = {}
            for account in accounts:
                currency = account['currency']
                account_type = account['type']
                balance = float(account['balance'])
                available = float(account['available'])
                holds = float(account['holds'])
                
                if currency not in balances:
                    balances[currency] = {}
                
                balances[currency][account_type] = {
                    'balance': balance,
                    'available': available,
                    'holds': holds
                }
            
            return {
                "balances": balances,
                "timestamp": datetime.now().isoformat(),
                "raw_data": accounts
            }
        except KucoinAPIException as e:
            self.logger.error(f"KuCoin API error getting account balance: {e}")
            return None
        except KucoinRequestException as e:
            self.logger.error(f"KuCoin response error getting account balance: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting account balance: {e}")
            return None

    def fetch_crypto_prices(self) -> Dict[str, Any]:
        """Fetch current prices for all configured cryptocurrencies."""
        # Load assets config to get list of cryptocurrencies to track
        with open(self.assets_path, 'r') as f:
            assets = yaml.safe_load(f)
        
        prices = {}
        for crypto in assets.get('crypto', []):
            symbol = crypto.get('symbol')
            if symbol:
                price_data = self.get_current_price(symbol)
                if price_data:
                    prices[symbol] = price_data
        
        return prices

    def fetch_crypto_historical(self, days: int = 30) -> Dict[str, Any]:
        """Fetch historical prices for all configured cryptocurrencies."""
        # Load assets config to get list of cryptocurrencies to track
        with open(self.assets_path, 'r') as f:
            assets = yaml.safe_load(f)
        
        historical_data = {}
        for crypto in assets.get('crypto', []):
            symbol = crypto.get('symbol')
            if symbol:
                data = self.get_historical_prices(symbol, days=days)
                if data:
                    historical_data[symbol] = data
        
        return historical_data