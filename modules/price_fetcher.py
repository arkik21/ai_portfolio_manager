"""
Price Fetcher Module

This module fetches current and historical price data for cryptocurrencies
from the KuCoin API. Future versions will include IBKR for stocks.
"""
import os
import json
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional
import yaml
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
        self.client = None
        
        # Create storage directory if it doesn't exist and it's specified
        if storage_path:
            os.makedirs(storage_path, exist_ok=True)
        
        try:
            # Check if the KuCoin SDK is available
            try:
                from kucoin.client import Client
                KUCOIN_SDK_AVAILABLE = True
                self.logger.info("KuCoin SDK is available")
            except ImportError:
                KUCOIN_SDK_AVAILABLE = False
                self.logger.warning("KuCoin SDK not available. Install with: pip install python-kucoin")
            
            # Load settings from the config file
            settings = self._load_config(config_path)
            if not settings:
                self.logger.warning("Empty or invalid settings.yaml")
                
            # Load secrets for API credentials
            secrets_path = os.path.join(os.path.dirname(config_path), 'secrets.yaml')
            self.logger.info(f"Looking for secrets file at: {secrets_path}")
            
            if not os.path.exists(secrets_path):
                self.logger.warning(f"Secrets file not found: {secrets_path}")
                secrets = {}
            else:
                secrets = self._load_config(secrets_path)
                if not secrets:
                    self.logger.warning("Empty or invalid secrets.yaml")
            
            # Get KuCoin API credentials from secrets
            api_key = None
            api_secret = None
            api_passphrase = None
            
            if secrets and 'apis' in secrets and 'kucoin' in secrets['apis']:
                kucoin_secrets = secrets['apis']['kucoin']
                api_key = kucoin_secrets.get('api_key')
                api_secret = kucoin_secrets.get('api_secret')
                api_passphrase = kucoin_secrets.get('api_passphrase')
            
            # Get sandbox setting from main config
            sandbox_mode = True
            if settings and 'apis' in settings and 'kucoin' in settings['apis']:
                sandbox_mode = settings['apis']['kucoin'].get('sandbox_mode', True)
            
            self.logger.info(f"API Key present: {bool(api_key)}")
            self.logger.info(f"API Secret present: {bool(api_secret)}")
            self.logger.info(f"API Passphrase present: {bool(api_passphrase)}")
            self.logger.info(f"Using sandbox mode: {sandbox_mode}")
            
            # Initialize the KuCoin client if the SDK is available and credentials are present
            if KUCOIN_SDK_AVAILABLE and all([api_key, api_secret, api_passphrase]):
                from kucoin.client import Client
                
                try:
                    self.client = Client(api_key, api_secret, api_passphrase, sandbox_mode)
                    self.logger.info("KuCoin client initialized successfully")
                    
                    # Test connection with a simple request
                    _ = self.client.get_timestamp()
                    self.logger.info("KuCoin API connection test successful")
                    
                except Exception as e:
                    self.logger.error(f"Error initializing KuCoin client: {str(e)}")
                    self.logger.debug(traceback.format_exc())
                    self.client = None
            else:
                self.logger.warning("Using dummy KuCoin client due to missing SDK or credentials")
                self.client = DummyKuCoinClient()
                
        except Exception as e:
            self.logger.error(f"Unexpected error during initialization: {str(e)}")
            self.logger.debug(traceback.format_exc())
            self.client = DummyKuCoinClient()
    
    def _load_config(self, file_path: str) -> Dict[str, Any]:
        """Load YAML configuration file with improved error handling."""
        try:
            with open(file_path, 'r') as file:
                config = yaml.safe_load(file)
                if config is None:
                    self.logger.error(f"Config file {file_path} was loaded but is empty or invalid")
                    return {}
                return config
        except FileNotFoundError:
            self.logger.error(f"Config file not found: {file_path}")
            return {}
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML in {file_path}: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Unexpected error loading {file_path}: {e}")
            return {}
    
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
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
            self.logger.debug(traceback.format_exc())
            return None
    
    def _calculate_change_percent(self, stats: Dict[str, Any]) -> float:
        """Calculate 24h price change percentage from stats."""
        try:
            if 'changeRate' in stats:
                # If changeRate is available, use it directly
                return float(stats['changeRate']) * 100
                
            if 'changePrice' in stats and 'last' in stats and float(stats['last']) > 0:
                change_price = float(stats['changePrice'])
                current_price = float(stats['last'])
                previous_price = current_price - change_price
                if previous_price > 0:
                    return (change_price / previous_price) * 100
            
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
                timestamp = datetime.fromtimestamp(int(kline[0]))
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
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            self.logger.debug(traceback.format_exc())
            return None
    
    def fetch_crypto_prices(self) -> Dict[str, Any]:
        """Fetch current prices for all configured cryptocurrencies."""
        # Load assets config to get list of cryptocurrencies to track
        assets = self._load_config(self.assets_path)
        
        prices = {}
        for crypto in assets.get('crypto', []):
            symbol = crypto.get('symbol')
            if symbol:
                price_data = self.get_current_price(symbol)
                if price_data:
                    prices[symbol] = price_data
                    
                    # Save to file if storage path is provided
                    if self.storage_path:
                        self._save_price_data(symbol, price_data)
        
        return prices
    
    def _save_price_data(self, symbol: str, price_data: Dict[str, Any]) -> bool:
        """Save price data to a file."""
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            file_path = os.path.join(self.storage_path, f"{symbol}_current_{date_str}.json")
            
            with open(file_path, 'w') as file:
                json.dump(price_data, file, indent=2)
                
            self.logger.info(f"Saved current price data for {symbol}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving price data for {symbol}: {e}")
            return False

    def fetch_crypto_historical(self, days: int = 30) -> Dict[str, Any]:
        """Fetch historical prices for all configured cryptocurrencies."""
        # Load assets config to get list of cryptocurrencies to track
        assets = self._load_config(self.assets_path)
        
        historical_data = {}
        for crypto in assets.get('crypto', []):
            symbol = crypto.get('symbol')
            if symbol:
                data = self.get_historical_prices(symbol, days=days)
                if data:
                    historical_data[symbol] = data
                    
                    # Save to file if storage path is provided
                    if self.storage_path:
                        self._save_historical_data(symbol, data)
        
        return historical_data
    
    def _save_historical_data(self, symbol: str, data: List[Dict[str, Any]]) -> bool:
        """Save historical data to a file."""
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            file_path = os.path.join(self.storage_path, f"{symbol}_historical_{date_str}.json")
            
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=2)
                
            self.logger.info(f"Saved historical data for {symbol}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving historical data for {symbol}: {e}")
            return False
    
    def get_latest_prices(self) -> Dict[str, Dict[str, Any]]:
        """Get the latest available prices for all configured cryptocurrencies."""
        return self.fetch_crypto_prices()
        
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
            # Import constants if using the real client
            from kucoin.client import Client
            
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
                "order_id": response.get('orderId', ''),
                "symbol": symbol,
                "type": "market",
                "side": side.lower(),
                "amount": amount,
                "status": "success",
                "exchange": "kucoin",
                "timestamp": datetime.now().isoformat(),
                "raw_data": response
            }
        except Exception as e:
            self.logger.error(f"Error placing market order for {symbol}: {e}")
            self.logger.debug(traceback.format_exc())
            return {
                "status": "error",
                "reason": f"Error: {str(e)}",
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
            # Import constants if using the real client
            from kucoin.client import Client
            
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
                "order_id": response.get('orderId', ''),
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
        except Exception as e:
            self.logger.error(f"Error placing limit order for {symbol}: {e}")
            self.logger.debug(traceback.format_exc())
            return {
                "status": "error",
                "reason": f"Error: {str(e)}",
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
        except Exception as e:
            self.logger.error(f"Error getting account balance: {e}")
            self.logger.debug(traceback.format_exc())
            return None


# Dummy KuCoin client for development and testing
class DummyKuCoinClient:
    """A dummy implementation of the KuCoin client for development and testing."""
    
    # Constants from KuCoin API
    SIDE_BUY = 'buy'
    SIDE_SELL = 'sell'

    ACCOUNT_MAIN = 'main'
    ACCOUNT_TRADE = 'trade'

    ORDER_LIMIT = 'limit'
    ORDER_MARKET = 'market'
    ORDER_LIMIT_STOP = 'limit_stop'
    ORDER_MARKET_STOP = 'market_stop'
    
    def __init__(self):
        self.logger = logging.getLogger('dummy_kucoin')
        self.logger.info("Initialized dummy KuCoin client")
    
    def get_timestamp(self, **params):
        """Get server timestamp."""
        return int(time.time() * 1000)
    
    def get_ticker(self, symbol):
        """Get ticker information for a symbol."""
        self.logger.info(f"Dummy get_ticker for {symbol}")
        
        # Default prices for common symbols
        prices = {
            'BTC-USDT': '53000.00',
            'ETH-USDT': '3500.00',
            'SOL-USDT': '120.00',
            'KCS-BTC': '0.00037',
        }
        
        return {
            "sequence": "1550467636704",
            "price": prices.get(symbol, '1000.00'),  # Default price
            "size": "0.17",
            "bestAsk": "0.03715004",
            "bestAskSize": "1.788",
            "bestBid": "0.03710768",
            "bestBidSize": "3.803",
            "time": int(time.time() * 1000)
        }
    
    def get_24hr_stats(self, symbol):
        """Get 24hr stats for a symbol."""
        self.logger.info(f"Dummy get_24hr_stats for {symbol}")
        
        # Base values with random variations for different symbols
        import random
        import hashlib
        
        # Use symbol to generate consistent pseudo-random values
        hash_val = int(hashlib.md5(symbol.encode()).hexdigest(), 16) % 100
        change_rate = (hash_val - 50) / 1000  # Between -0.05 and 0.05
        
        return {
            "symbol": symbol,
            "changeRate": str(change_rate),
            "changePrice": str(float(change_rate) * 1000),
            "high": "55000.00",
            "last": "53000.00",
            "low": "51000.00",
            "vol": "2370.8926",
            "volValue": "121820705.7127"
        }
    
    def get_kline_data(self, symbol, kline_type, start, end):
        """Get kline data for a symbol."""
        self.logger.info(f"Dummy get_kline_data for {symbol} ({kline_type})")
        
        # Generate dummy data for the requested time period
        import random
        
        # Convert timestamps to days
        start_day = start // 86400
        end_day = end // 86400
        days = end_day - start_day
        
        klines = []
        
        # Set base price based on symbol
        if 'BTC' in symbol:
            base_price = 50000.0
        elif 'ETH' in symbol:
            base_price = 3000.0
        else:
            base_price = 100.0
        
        for i in range(days):
            day_timestamp = (start_day + i) * 86400
            
            # Create some random price movement
            change = random.uniform(-base_price * 0.02, base_price * 0.02)
            price = base_price + change
            base_price = price  # For the next day
            
            # Format: [timestamp, open, close, high, low, volume, turnover]
            kline = [
                str(day_timestamp),  # timestamp
                str(price - random.uniform(0, price * 0.01)),  # open
                str(price),  # close
                str(price + random.uniform(0, price * 0.015)),  # high
                str(price - random.uniform(0, price * 0.015)),  # low
                str(random.uniform(500, 2000)),  # volume
                str(random.uniform(10000000, 50000000))  # turnover
            ]
            klines.append(kline)
        
        return klines
    
    def get_accounts(self):
        """Get account information."""
        self.logger.info("Dummy get_accounts")
        
        return [
            {
                "id": "5bd6e9286d99522a52e458de",
                "currency": "BTC",
                "type": "main",
                "balance": "0.10000000",
                "available": "0.10000000",
                "holds": "0.00000000"
            },
            {
                "id": "5bd6e9216d99522a52e458d6",
                "currency": "USDT",
                "type": "main",
                "balance": "10000.00000000",
                "available": "10000.00000000",
                "holds": "0.00000000"
            }
        ]
    
    def create_market_order(self, symbol, side, **kwargs):
        """Create a market order."""
        self.logger.info(f"Dummy create_market_order: {side} {symbol}")
        
        order_id = f"dummy-order-{int(time.time())}"
        
        # Log different parameters based on side
        if side == self.SIDE_BUY:
            self.logger.info(f"Buy order funds: {kwargs.get('funds')}")
        else:
            self.logger.info(f"Sell order size: {kwargs.get('size')}")
        
        return {
            "orderId": order_id,
            "symbol": symbol,
            "type": "market",
            "side": side,
            "size": kwargs.get("size", ""),
            "funds": kwargs.get("funds", ""),
            "dealSize": "0",
            "dealFunds": "0",
            "fee": "0",
            "feeCurrency": "USDT",
            "createdAt": int(time.time() * 1000)
        }
    
    def create_limit_order(self, symbol, side, price, size):
        """Create a limit order."""
        self.logger.info(f"Dummy create_limit_order: {side} {symbol} @ {price}")
        
        order_id = f"dummy-order-{int(time.time())}"
        
        return {
            "orderId": order_id,
            "symbol": symbol,
            "type": "limit",
            "side": side,
            "price": price,
            "size": size,
            "dealSize": "0",
            "dealFunds": "0",
            "fee": "0",
            "feeCurrency": "USDT",
            "createdAt": int(time.time() * 1000)
        }