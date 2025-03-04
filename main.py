"""
AI Portfolio Manager

This is the main module that integrates all components of the AI portfolio manager.
It handles the execution flow, scheduling, and user interaction.
"""

# Copyright (c) 2025 Alexander Isaev
# All Rights Reserved. See LICENSE for details.

import os
import sys
import time
import logging
import argparse
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import modules
from modules.transcript_fetcher import TranscriptFetcher
from modules.price_fetcher import PriceFetcher
from modules.analysis_engine import AnalysisEngine
from modules.order_manager import OrderManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ai_portfolio_manager.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ai_portfolio_manager')

class AIPortfolioManager:
    """Main class that coordinates all portfolio management activities."""
    
    def __init__(self, base_path: str = None, test_mode: bool = False):
        """
        Initialize the AI Portfolio Manager.
        
        Args:
            base_path: Base directory for the project (default: current directory)
            test_mode: Use dummy implementations instead of real APIs
        """
        # Set test mode
        self.test_mode = test_mode
        logger.info(f"Running in {'TEST' if test_mode else 'REAL'} mode")

        # Set base path
        if base_path is None:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
        else:
            self.base_path = base_path
            
        # Define paths
        self.config_dir = os.path.join(self.base_path, "config")
        self.data_dir = os.path.join(self.base_path, "data")
        
        # Config file paths
        self.settings_path = os.path.join(self.config_dir, "settings.yaml")
        self.assets_path = os.path.join(self.config_dir, "assets.yaml")
        self.narratives_path = os.path.join(self.config_dir, "narratives.yaml")
        
        # Data directories
        self.transcripts_dir = os.path.join(self.data_dir, "transcripts")
        self.prices_dir = os.path.join(self.data_dir, "prices")
        self.analysis_dir = os.path.join(self.data_dir, "analysis")
        self.orders_dir = os.path.join(self.data_dir, "orders")
        
        # Create directories if they don't exist
        for directory in [self.config_dir, self.transcripts_dir, self.prices_dir, 
                          self.analysis_dir, self.orders_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Load settings
        self.settings = self._load_yaml(self.settings_path)
        
        # Initialize modules
        self.transcript_fetcher = TranscriptFetcher(
            config_path=self.settings_path,
            storage_path=self.transcripts_dir
        )
        
        print(f"Config path: {self.settings_path}")
        print(f"Config directory exists: {os.path.exists(os.path.dirname(self.settings_path))}")
        
        self.price_fetcher = PriceFetcher(
            config_path=self.settings_path,
            assets_path=self.assets_path,
            storage_path=self.prices_dir,
            test_mode=test_mode
        )
        
        self.analysis_engine = AnalysisEngine(
            config_path=self.settings_path,
            assets_path=self.assets_path,
            narratives_path=self.narratives_path,
            transcripts_path=self.transcripts_dir,
            prices_path=self.prices_dir,
            output_path=self.analysis_dir
        )
        
        self.order_manager = OrderManager(
            config_path=self.settings_path,
            assets_path=self.assets_path,
            output_path=self.orders_dir,
            test_mode=test_mode  # Pass the test_mode parameter
        )
    
    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return {}
    
    def fetch_data(self):
        """Fetch all required data from sources."""
        logger.info("Starting data collection")
        
        # Fetch YouTube transcripts
        try:
            logger.info("Fetching YouTube transcripts")
            num_transcripts = self.transcript_fetcher.fetch_recent_transcripts()
            logger.info(f"Fetched {num_transcripts} transcripts")
        except Exception as e:
            logger.error(f"Error fetching transcripts: {e}")
        
        # Fetch crypto prices
        try:
            logger.info("Fetching current crypto prices")
            current_prices = self.price_fetcher.fetch_crypto_prices()
            logger.info(f"Fetched current prices for {len(current_prices)} cryptocurrencies")
            
            logger.info("Fetching historical crypto prices")
            historical_prices = self.price_fetcher.fetch_crypto_historical(days=30)
            logger.info(f"Fetched historical prices for {len(historical_prices)} cryptocurrencies")
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
        
        logger.info("Data collection completed")
    
    def run_analysis(self, symbol: str = None):
        """
        Run analysis on assets.
        
        Args:
            symbol: Specific asset to analyze, or None for all crypto
        """
        logger.info("Starting analysis")
        
        try:
            if symbol:
                # Analyze specific asset
                logger.info(f"Analyzing {symbol}")
                analysis = self.analysis_engine.analyze_asset(symbol)
                logger.info(f"Analysis for {symbol} completed with status: {analysis.get('status')}")
                return analysis
            else:
                # Analyze all crypto assets
                logger.info("Analyzing all crypto assets")
                results = self.analysis_engine.analyze_all_crypto()
                logger.info(f"Analysis completed for {len(results)} assets")
                return results
        except Exception as e:
            logger.error(f"Error running analysis: {e}")
            return None
    
    def generate_orders(self, analysis_results: Dict[str, Any] = None):
        """
        Generate orders based on analysis results.
        
        Args:
            analysis_results: Analysis results from run_analysis, or None to use latest
        """
        logger.info("Generating trading orders")
        
        orders = []
        
        try:
            # If no analysis provided, get latest for each crypto asset
            if not analysis_results:
                analysis_results = {}
                assets = self._load_yaml(self.assets_path)
                
                for asset in assets.get('crypto', []):
                    symbol = asset.get('symbol')
                    if symbol:
                        latest = self.analysis_engine.get_latest_recommendation(symbol)
                        if latest:
                            analysis_results[symbol] = latest
            
            # Process each analysis to generate orders
            for symbol, analysis in analysis_results.items():
                # Extract trading signal
                signal = self.analysis_engine.extract_trade_signals(analysis)
                
                # Create order from signal
                order = self.order_manager.create_order_from_signal(signal)
                if order:
                    orders.append(order)
                    logger.info(f"Generated {order['side']} order for {symbol}")
            
            logger.info(f"Generated {len(orders)} orders")
            return orders
        except Exception as e:
            logger.error(f"Error generating orders: {e}")
            return []
    
    def execute_orders(self, orders: List[Dict[str, Any]], confirm: bool = None):
        """
        Execute trading orders.
        
        Args:
            orders: List of orders to execute
            confirm: Whether to require confirmation (overrides config setting)
        """
        logger.info(f"Executing {len(orders)} orders")
        
        results = []
        
        for order in orders:
            try:
                logger.info(f"Submitting order: {order['side']} {order['amount']} {order['symbol']}")
                result = self.order_manager.submit_order(order, confirm=confirm)
                results.append(result)
                
                if result['status'] == 'success':
                    logger.info(f"Order executed successfully: {result.get('order_id')}")
                elif result['status'] == 'pending_confirmation':
                    logger.info(f"Order pending confirmation")
                else:
                    logger.warning(f"Order execution failed: {result.get('reason')}")
            except Exception as e:
                logger.error(f"Error executing order: {e}")
        
        logger.info(f"Order execution completed: {len([r for r in results if r.get('status') == 'success'])}/{len(orders)} successful")
        return results
    
    def run_full_cycle(self, symbol: str = None, execute: bool = False, confirm: bool = None):
        """
        Run a full cycle of the portfolio manager.
        
        Args:
            symbol: Specific asset to analyze, or None for all crypto
            execute: Whether to execute generated orders
            confirm: Whether to require confirmation for orders
        """
        logger.info("Starting full portfolio management cycle")
        
        # Step 1: Fetch data
        self.fetch_data()
        
        # Step 2: Run analysis
        analysis_results = self.run_analysis(symbol)
        
        # Step 3: Generate orders
        orders = self.generate_orders(analysis_results)
        
        # Step 4: Execute orders (if enabled)
        if execute and orders:
            results = self.execute_orders(orders, confirm=confirm)
            return {
                "analysis": analysis_results,
                "orders": orders,
                "execution_results": results
            }
        else:
            return {
                "analysis": analysis_results,
                "orders": orders
            }
    
    def run_scheduler(self, interval_hours: int = None):
        """
        Run the portfolio manager on a schedule.
        
        Args:
            interval_hours: Hours between cycles, or None to use config
        """
        # Get interval from config if not provided
        if interval_hours is None:
            interval_seconds = self.settings.get('system', {}).get('data_refresh_interval', 3600)
            interval_hours = interval_seconds / 3600
        
        interval_seconds = interval_hours * 3600
        
        logger.info(f"Starting scheduler with {interval_hours} hour interval")
        
        try:
            while True:
                logger.info(f"Running scheduled cycle at {datetime.now().isoformat()}")
                
                try:
                    self.run_full_cycle(execute=False)
                except Exception as e:
                    logger.error(f"Error in scheduled cycle: {e}")
                
                logger.info(f"Next cycle scheduled for {datetime.now() + timedelta(seconds=interval_seconds)}")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
    
    def print_portfolio_summary(self):
        """Print a summary of the current portfolio status."""
        logger.info("Generating portfolio summary")
        
        try:
            # Get latest prices
            prices = self.price_fetcher.get_latest_prices()
            
            # Get latest analyses
            analyses = {}
            assets = self._load_yaml(self.assets_path)
            
            for asset in assets.get('crypto', []):
                symbol = asset.get('symbol')
                if symbol:
                    latest = self.analysis_engine.get_latest_recommendation(symbol)
                    if latest:
                        analyses[symbol] = latest
            
            # Get recent orders
            orders = self.order_manager.get_order_history(days_back=7)
            
            # Print summary
            print("\n" + "="*80)
            print(" AI PORTFOLIO MANAGER - SUMMARY ".center(80, "="))
            print("="*80)
            
            print("\nASSET PRICES:")
            print("-" * 60)
            for symbol, price_data in prices.items():
                print(f"{symbol}: ${price_data.get('price', 'N/A')} ({price_data.get('change_24h_percent', 'N/A')}%)")
            
            print("\nLATEST RECOMMENDATIONS:")
            print("-" * 60)
            for symbol, analysis in analyses.items():
                signal = self.analysis_engine.extract_trade_signals(analysis)
                print(f"{symbol}: {signal.get('action')} ({signal.get('sentiment')}, {signal.get('confidence')})")
            
            print("\nRECENT ORDERS:")
            print("-" * 60)
            for order in orders[:5]:  # Show 5 most recent
                print(f"{order.get('timestamp', 'N/A')}: {order.get('side', 'N/A').upper()} {order.get('amount', 'N/A')} {order.get('symbol', 'N/A')} @ {order.get('price', 'market')}")
            
            print("\n" + "="*80 + "\n")
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            print(f"Error generating summary: {e}")

    def buy_asset(self, symbol: str, amount: float, price: float = None, confirm: bool = None):
        """
        Place a buy order for a specific asset.
        
        Args:
            symbol: Asset symbol (e.g., BTC)
            amount: Amount to buy in USD
            price: Limit price (None for market orders)
            confirm: Whether to require confirmation (overrides config setting)
            
        Returns:
            Order result dictionary
        """
        logger.info(f"Creating buy order for {symbol}, amount: ${amount}")
        
        # Validate symbol
        asset_info = self._get_asset_info(symbol)
        if not asset_info:
            logger.error(f"Asset {symbol} not found in configuration")
            return {
                "status": "error",
                "reason": f"Asset {symbol} not found in configuration"
            }
        
        # Get exchange information (default to 'kucoin' for crypto if not specified)
        exchange = asset_info.get('exchange', 'kucoin' if asset_info.get('type') == 'crypto' else '')
        
        # Create order object
        order = {
            "symbol": symbol,
            "type": "market" if price is None else "limit",
            "side": "buy",
            "amount": amount,
            "exchange": exchange,  # Add exchange information
            "timestamp": datetime.now().isoformat()
        }
        
        # Add price for limit orders
        if price is not None:
            order["price"] = price
            logger.info(f"Limit price: ${price}")
        else:
            logger.info("Market order")
        
        # Log exchange information
        logger.info(f"Using exchange: {exchange}")
        
        # Submit the order
        result = self.order_manager.submit_order(order, confirm=confirm)
        
        if result.get('status') == 'success':
            logger.info(f"Buy order placed successfully: {result.get('order_id')}")
        elif result.get('status') == 'pending_confirmation':
            logger.info(f"Buy order pending confirmation")
        else:
            logger.error(f"Buy order failed: {result.get('reason')}")
        
        return result

    def check_account_balance(self):
        """
        Check and display the current account balance for all exchanges.
        
        Returns:
            Dictionary with balance information or None if the request fails
        """
        logger.info("Checking account balance")
        
        try:
            # Create a PriceFetcher instance if we don't have one
            if not hasattr(self, 'price_fetcher'):
                from modules.price_fetcher import PriceFetcher
                price_fetcher = PriceFetcher(
                    config_path=self.settings_path,
                    assets_path=self.assets_path,
                    test_mode=self.test_mode
                )
            else:
                price_fetcher = self.price_fetcher
            
            # Get the balance from KuCoin
            balance_info = price_fetcher.get_account_balance()
            
            if not balance_info:
                logger.error("Failed to retrieve account balance")
                print("Failed to retrieve account balance. Make sure your API credentials are correct.")
                return None
            
            # Print the balance information in a user-friendly format
            print("\n" + "="*80)
            print(" ACCOUNT BALANCE ".center(80, "="))
            print("="*80 + "\n")
            
            for currency, accounts in balance_info.get('balances', {}).items():
                print(f"{currency}:")
                for account_type, details in accounts.items():
                    print(f"  {account_type.capitalize()}: {details['balance']} (Available: {details['available']}, On Hold: {details['holds']})")
                print()
            
            print("="*80 + "\n")
            
            return balance_info
        
        except Exception as e:
            logger.error(f"Error checking account balance: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            print(f"Error checking account balance: {e}")
            return None

    def sell_asset(self, symbol: str, amount: float, price: float = None, confirm: bool = None):
        """
        Place a sell order for a specific asset.
        
        Args:
            symbol: Asset symbol (e.g., BTC)
            amount: Amount to sell in USD
            price: Limit price (None for market orders)
            confirm: Whether to require confirmation (overrides config setting)
            
        Returns:
            Order result dictionary
        """
        logger.info(f"Creating sell order for {symbol}, amount: ${amount}")
        
        # Validate symbol
        asset_info = self._get_asset_info(symbol)
        if not asset_info:
            logger.error(f"Asset {symbol} not found in configuration")
            return {
                "status": "error",
                "reason": f"Asset {symbol} not found in configuration"
            }
        
        # Get exchange information (default to 'kucoin' for crypto if not specified)
        exchange = asset_info.get('exchange', 'kucoin' if asset_info.get('type') == 'crypto' else '')
        
        # Create order object
        order = {
            "symbol": symbol,
            "type": "market" if price is None else "limit",
            "side": "sell",
            "amount": amount,
            "exchange": exchange,  # Add exchange information
            "timestamp": datetime.now().isoformat()
        }
        
        # Add price for limit orders
        if price is not None:
            order["price"] = price
            logger.info(f"Limit price: ${price}")
        else:
            logger.info("Market order")
        
        # Log exchange information
        logger.info(f"Using exchange: {exchange}")
        
        # Submit the order
        result = self.order_manager.submit_order(order, confirm=confirm)
        
        if result.get('status') == 'success':
            logger.info(f"Sell order placed successfully: {result.get('order_id')}")
        elif result.get('status') == 'pending_confirmation':
            logger.info(f"Sell order pending confirmation")
        else:
            logger.error(f"Sell order failed: {result.get('reason')}")
        
        return result

    def cancel_specific_order(self, order_id: str):
        """
        Cancel a specific order by ID.
        
        Args:
            order_id: ID of the order to cancel
        """
        logger.info(f"Cancelling order: {order_id}")
        
        result = self.order_manager.cancel_order(order_id)
        
        if result.get('status') == 'success':
            logger.info(f"Order {order_id} cancelled successfully")
            print(f"Order {order_id} cancelled successfully")
        else:
            logger.error(f"Failed to cancel order {order_id}: {result.get('reason')}")
            print(f"Failed to cancel order {order_id}: {result.get('reason')}")
        
        return result

    def cancel_all_orders(self, symbol: str = None):
        """
        Cancel all orders, optionally filtered by symbol.
        
        Args:
            symbol: Symbol to cancel orders for (e.g., BTC), or None for all
        """
        if symbol:
            logger.info(f"Cancelling all orders for {symbol}")
            print(f"Cancelling all orders for {symbol}...")
        else:
            logger.info("Cancelling all orders")
            print("Cancelling all orders...")
        
        result = self.order_manager.cancel_all_orders(symbol)
        
        if result.get('status') == 'success':
            cancelled_count = len(result.get('cancelled_ids', []))
            logger.info(f"Cancelled {cancelled_count} orders successfully")
            print(f"Cancelled {cancelled_count} orders successfully")
        else:
            logger.error(f"Failed to cancel orders: {result.get('reason')}")
            print(f"Failed to cancel orders: {result.get('reason')}")
        
        return result
    #helper method to retrieve asset info
    def _get_asset_info(self, symbol: str):
        """Get asset information from the assets config."""
        assets = self._load_yaml(self.assets_path)
        
        for asset_category in ['crypto', 'stocks']:
            for asset in assets.get(asset_category, []):
                if asset.get('symbol') == symbol:
                    asset_info = asset.copy()
                    asset_info['type'] = asset_category
                    return asset_info
        return None

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='AI Portfolio Manager')
    
    parser.add_argument('--fetch', action='store_true', help='Fetch data only')
    parser.add_argument('--analyze', action='store_true', help='Run analysis only')
    parser.add_argument('--generate', action='store_true', help='Generate orders only')
    parser.add_argument('--execute', action='store_true', help='Execute generated orders')
    parser.add_argument('--symbol', type=str, help='Specific asset to analyze')
    parser.add_argument('--cycle', action='store_true', help='Run a full cycle')
    parser.add_argument('--schedule', action='store_true', help='Run on a schedule')
    parser.add_argument('--interval', type=float, help='Hours between scheduled runs')
    parser.add_argument('--summary', action='store_true', help='Print portfolio summary')
    parser.add_argument('--confirm', action='store_true', help='Require confirmation for orders')
    parser.add_argument('--auto', action='store_true', help='Execute orders without confirmation')
    parser.add_argument('--buy', action='store_true', help='Place a buy order')
    parser.add_argument('--sell', action='store_true', help='Place a sell order') 
    parser.add_argument('--amount', type=float, help='Amount to buy in USD')
    parser.add_argument('--price', type=float, help='Limit price (omit for market orders)')
    parser.add_argument('--test', action='store_true', help='Run in test mode with dummy implementations')
    parser.add_argument('--cancel', type=str, help='Cancel a specific order by ID')
    parser.add_argument('--cancel-all', action='store_true', help='Cancel all orders')
    parser.add_argument('--balance', action='store_true', help='Check account balance')
    
    args = parser.parse_args()
    
    # Create the manager with test mode
    manager = AIPortfolioManager(test_mode=args.test)
    
    # Determine confirmation setting
    confirm = None
    if args.confirm:
        confirm = True
    elif args.auto:
        confirm = False
    
    # Execute requested action
    if args.cancel:
        manager.cancel_specific_order(args.cancel)
    elif args.cancel_all:
        manager.cancel_all_orders(args.symbol)  # Will use symbol if specified
    elif args.fetch:
        manager.fetch_data()
    elif args.analyze:
        manager.run_analysis(args.symbol)
    elif args.generate:
        manager.generate_orders()
    elif args.cycle:
        manager.run_full_cycle(args.symbol, args.execute, confirm)
    elif args.schedule:
        manager.run_scheduler(args.interval)
    elif args.sell:
        if not args.symbol:
            print("Error: Symbol must be specified with --symbol")
        elif not args.amount:
            print("Error: Amount must be specified with --amount")
        else:
            manager.sell_asset(args.symbol, args.amount, args.price, args.confirm)
    elif args.buy:
        if not args.symbol:
            print("Error: Symbol must be specified with --symbol")
        elif not args.amount:
            print("Error: Amount must be specified with --amount")
        else:
            manager.buy_asset(args.symbol, args.amount, args.price, args.confirm)
    elif args.summary or not any([args.fetch, args.analyze, args.generate, 
                                args.cycle, args.schedule, args.execute, args.buy, args.sell]):
        # Default action is to print summary
        manager.print_portfolio_summary()

if __name__ == "__main__":
    main()