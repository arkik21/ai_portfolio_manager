"""
Order Manager Module

This module manages trading orders based on analysis recommendations.
It handles order creation, validation, and submission to exchanges.
"""

import os
import json
import logging
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('order_manager')

class OrderManager:
    """Manages trading orders based on analysis recommendations."""
    
    def __init__(self, config_path: str, assets_path: str, output_path: str = None):
        """
        Initialize the OrderManager.
        
        Args:
            config_path: Path to settings.yaml
            assets_path: Path to assets.yaml
            output_path: Path to store order data (default: ./orders)
        """
        self.config_path = config_path
        self.assets_path = assets_path
        
        # Set default output path if not provided
        if output_path is None:
            self.output_path = os.path.join(os.path.dirname(config_path), "..", "data", "orders")
        else:
            self.output_path = output_path
            
        # Load configurations
        self.config = self._load_yaml(config_path)
        self.assets = self._load_yaml(assets_path)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_path, exist_ok=True)
        
        # Initialize API credentials
        self.kucoin_api_key = self.config.get('apis', {}).get('kucoin', {}).get('api_key', '')
        self.kucoin_api_secret = self.config.get('apis', {}).get('kucoin', {}).get('api_secret', '')
        self.kucoin_api_passphrase = self.config.get('apis', {}).get('kucoin', {}).get('api_passphrase', '')
        self.kucoin_sandbox = self.config.get('apis', {}).get('kucoin', {}).get('sandbox_mode', True)
        
        # Load system settings
        self.trade_confirmation = self.config.get('system', {}).get('trade_confirmation', True)
        self.max_allocation = self.config.get('system', {}).get('max_allocation_per_asset', 0.20)
    
    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(file_path, 'r') as file:
                config = yaml.safe_load(file) or {}
                
            # Also try to load secrets file if it exists
            secrets_path = os.path.join(os.path.dirname(file_path), "secrets.yaml")
            if os.path.exists(secrets_path):
                try:
                    with open(secrets_path, 'r') as secret_file:
                        secrets = yaml.safe_load(secret_file) or {}
                        
                    # Merge secrets into config (deep merge)
                    self._merge_dicts(config, secrets)
                except Exception as e:
                    logger.error(f"Failed to load secrets from {secrets_path}: {e}")
                    
            return config
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return {}
            
    def _merge_dicts(self, dict1, dict2):
        """
        Recursively merge dict2 into dict1
        """
        for key in dict2:
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                self._merge_dicts(dict1[key], dict2[key])
            else:
                dict1[key] = dict2[key]
    
    def _get_asset_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get asset information from the configuration.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Asset information dictionary or None if not found
        """
        for asset_category in ['crypto', 'stocks']:
            for asset in self.assets.get(asset_category, []):
                if asset.get('symbol') == symbol:
                    asset_info = asset.copy()
                    asset_info['type'] = asset_category
                    return asset_info
        return None
    
    def _validate_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an order before submission.
        
        Args:
            order: Order data to validate
            
        Returns:
            Dictionary with validation result and errors if any
        """
        errors = []
        
        # Check required fields
        required_fields = ['symbol', 'type', 'side', 'amount']
        for field in required_fields:
            if field not in order:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return {
                "valid": False,
                "errors": errors
            }
        
        # Validate asset exists
        asset_info = self._get_asset_info(order['symbol'])
        if not asset_info:
            errors.append(f"Asset not found: {order['symbol']}")
            return {
                "valid": False,
                "errors": errors
            }
        
        # Validate order type
        valid_types = ['market', 'limit']
        if order['type'] not in valid_types:
            errors.append(f"Invalid order type: {order['type']}. Must be one of {valid_types}")
        
        # Validate order side
        valid_sides = ['buy', 'sell']
        if order['side'] not in valid_sides:
            errors.append(f"Invalid order side: {order['side']}. Must be one of {valid_sides}")
        
        # Validate amount
        try:
            amount = float(order['amount'])
            if amount <= 0:
                errors.append(f"Invalid amount: {amount}. Must be greater than 0")
        except ValueError:
            errors.append(f"Invalid amount: {order['amount']}. Must be a number")
        
        # For limit orders, validate price
        if order['type'] == 'limit' and 'price' not in order:
            errors.append("Price is required for limit orders")
        elif order['type'] == 'limit':
            try:
                price = float(order['price'])
                if price <= 0:
                    errors.append(f"Invalid price: {price}. Must be greater than 0")
            except ValueError:
                errors.append(f"Invalid price: {order['price']}. Must be a number")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _place_kucoin_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit an order to KuCoin.
        
        Args:
            order: Validated order data
            
        Returns:
            Dictionary with order result
        """
        # NOTE: This is a dummy implementation
        # In a real implementation, we would use the KuCoin API client
        
        logger.info(f"Placing KuCoin order: {order['side']} {order['amount']} {order['symbol']}")
        
        # Simulate API latency
        time.sleep(1)
        
        # Generate order ID
        order_id = f"dummy-order-{int(time.time())}"
        
        # For demonstration, simulate successful order
        return {
            "order_id": order_id,
            "symbol": order['symbol'],
            "type": order['type'],
            "side": order['side'],
            "price": order.get('price', 'market'),
            "amount": order['amount'],
            "status": "success",
            "exchange": "kucoin",
            "timestamp": datetime.now().isoformat()
        }
    
    def create_order_from_signal(self, signal: Dict[str, Any], 
                               allocation: float = None) -> Optional[Dict[str, Any]]:
        """
        Create an order from a trade signal.
        
        Args:
            signal: Trade signal from analysis engine
            allocation: Percentage of portfolio to allocate (0.0 to 1.0)
            
        Returns:
            Order data or None if no action required
        """
        symbol = signal.get('symbol')
        action = signal.get('action')
        
        if not symbol or action == "NONE" or action == "HOLD":
            logger.info(f"No order needed for {symbol} (action: {action})")
            return None
        
        # Get asset info
        asset_info = self._get_asset_info(symbol)
        if not asset_info:
            logger.error(f"Asset not found: {symbol}")
            return None
        
        # Determine order side
        side = "buy" if action == "BUY" else "sell"
        
        # Set default allocation if not provided
        if allocation is None:
            # Higher confidence = higher allocation
            confidence = signal.get('confidence', 'LOW')
            if confidence == "HIGH":
                allocation = self.max_allocation
            elif confidence == "MEDIUM":
                allocation = self.max_allocation * 0.6
            else:  # LOW
                allocation = self.max_allocation * 0.3
        
        # For simplicity, assume we have a fixed amount of USD for each order
        # In a real implementation, this would come from portfolio calculations
        base_amount = 1000.0  # Dummy value in USD
        amount = base_amount * allocation
        
        # Create order
        order = {
            "symbol": symbol,
            "type": "market",  # Use market order for simplicity
            "side": side,
            "amount": amount,
            "reason": f"Signal {action} with {signal.get('confidence', 'LOW')} confidence",
            "analysis_id": signal.get('analysis_id'),
            "timestamp": datetime.now().isoformat()
        }
        
        return order
    
    def submit_order(self, order: Dict[str, Any], 
                   confirm: bool = None) -> Dict[str, Any]:
        """
        Submit an order to the appropriate exchange.
        
        Args:
            order: Order data to submit
            confirm: Whether to require confirmation (overrides config setting)
            
        Returns:
            Dictionary with submission result
        """
        # Validate order
        validation = self._validate_order(order)
        if not validation['valid']:
            return {
                "status": "error",
                "reason": "Validation failed",
                "errors": validation['errors']
            }
        
        # Determine if confirmation is required
        require_confirmation = self.trade_confirmation
        if confirm is not None:
            require_confirmation = confirm
        
        if require_confirmation:
            logger.info("Order requires confirmation before submission")
            return {
                "status": "pending_confirmation",
                "order": order,
                "message": "Order is valid but requires confirmation"
            }
        
        # Determine exchange and submit order
        asset_info = self._get_asset_info(order['symbol'])
        exchange = asset_info.get('exchange', '').lower()
        
        result = None
        if exchange == 'kucoin':
            result = self._place_kucoin_order(order)
        else:
            return {
                "status": "error",
                "reason": f"Unsupported exchange: {exchange}"
            }
        
        # Save order result
        self._save_order(result)
        
        return result
    
    def _save_order(self, order: Dict[str, Any]) -> bool:
        """
        Save order data to storage.
        
        Args:
            order: Order data to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            order_id = order.get('order_id', str(int(time.time())))
            file_path = os.path.join(self.output_path, f"order_{order_id}_{date_str}.json")
            
            with open(file_path, 'w') as file:
                json.dump(order, file, indent=2)
            
            logger.info(f"Saved order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving order: {e}")
            return False
    
    def get_order_history(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Get order history from storage.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of order data
        """
        orders = []
        cutoff_date = datetime.now().timestamp() - (days_back * 86400)
        
        for filename in os.listdir(self.output_path):
            if filename.startswith("order_") and filename.endswith('.json'):
                try:
                    with open(os.path.join(self.output_path, filename), 'r') as file:
                        order = json.load(file)
                        
                        # Parse timestamp and filter by age
                        try:
                            timestamp = datetime.fromisoformat(order['timestamp'].replace('Z', '+00:00'))
                            if timestamp.timestamp() >= cutoff_date:
                                orders.append(order)
                        except (KeyError, ValueError):
                            # If we can't parse the timestamp, include it anyway
                            orders.append(order)
                            
                except Exception as e:
                    logger.error(f"Error loading order {filename}: {e}")
        
        # Sort by timestamp, newest first
        orders.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return orders

# Example usage
if __name__ == "__main__":
    # This is for testing the module directly
    order_manager = OrderManager(
        config_path="../config/settings.yaml",
        assets_path="../config/assets.yaml"
    )
    
    # Create a sample trade signal
    signal = {
        "symbol": "BTC",
        "action": "BUY",
        "sentiment": "BULLISH",
        "confidence": "HIGH",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "analysis_id": "sample_analysis"
    }
    
    # Create an order from the signal
    order = order_manager.create_order_from_signal(signal)
    if order:
        print(f"Created order: {order}")
        
        # Submit the order
        result = order_manager.submit_order(order, confirm=False)
        print(f"Order submission result: {result}")