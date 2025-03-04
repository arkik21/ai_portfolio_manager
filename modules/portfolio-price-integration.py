"""
Portfolio and Price Fetcher Integration

This script demonstrates how to integrate the existing PriceFetcher
with the new Portfolio Manager.
"""

import os
import sys
from datetime import datetime

# Add the parent directory to sys.path to import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import the Portfolio and PriceFetcher classes
from modules.portfolio_manager import Portfolio
from modules.price_fetcher import PriceFetcher

def run_integration_test():
    """Run a test integration between Portfolio and PriceFetcher."""
    print("=== Portfolio and PriceFetcher Integration Test ===")
    
    # Paths for configuration and data
    config_path = os.path.join(parent_dir, "config", "settings.yaml")
    assets_path = os.path.join(parent_dir, "config", "assets.yaml")
    portfolio_path = os.path.join(parent_dir, "data", "portfolio")
    prices_path = os.path.join(parent_dir, "data", "prices")
    
    # Create directories if they don't exist
    os.makedirs(portfolio_path, exist_ok=True)
    os.makedirs(prices_path, exist_ok=True)
    
    print(f"Using config: {config_path}")
    print(f"Using assets: {assets_path}")
    
    # Initialize the PriceFetcher in test mode
    price_fetcher = PriceFetcher(
        config_path=config_path,
        assets_path=assets_path,
        storage_path=prices_path,
        test_mode=True  # Use dummy client for testing
    )
    
    # Initialize the Portfolio Manager
    portfolio = Portfolio(
        config_path=config_path,
        storage_path=portfolio_path
    )
    
    # Connect the price fetcher to the portfolio
    portfolio.price_fetcher = price_fetcher
    
    # Fetch current prices and update portfolio
    print("\nFetching current prices...")
    prices = price_fetcher.fetch_crypto_prices()
    
    print(f"Fetched prices for {len(prices)} assets:")
    for symbol, price_data in prices.items():
        print(f"  {symbol}: ${price_data['price']:.2f} ({price_data['change_24h_percent']:.2f}%)")
    
    # Update portfolio with current prices
    print("\nUpdating portfolio with current prices...")
    portfolio.update_prices()
    
    # Print initial portfolio state
    print("\n=== Initial Portfolio State ===")
    summary = portfolio.get_portfolio_summary()
    print(f"Total Value: ${summary['total_value']:.2f}")
    print(f"Cash: ${summary['cash']:.2f} ({summary['cash_allocation']*100:.1f}%)")
    
    # Test recording a trade using fetched price data
    print("\n=== Recording Test Trades ===")
    
    # Choose an asset to buy (e.g., BTC)
    symbol_to_buy = "BTC"
    if symbol_to_buy in prices:
        current_price = prices[symbol_to_buy]['price']
        buy_amount = 20.0  # Buy $20 worth
        quantity = buy_amount / current_price
        
        success = portfolio.record_trade(
            symbol=symbol_to_buy,
            action="buy",
            quantity=quantity,
            price=current_price,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        print(f"{symbol_to_buy} Trade Recorded: {success}")
        print(f"Bought {quantity:.8f} {symbol_to_buy} at ${current_price:.2f}")
        
        # Update portfolio with current prices
        portfolio.update_prices()
        
        # Print updated portfolio state
        print("\n=== Updated Portfolio State ===")
        summary = portfolio.get_portfolio_summary()
        print(f"Total Value: ${summary['total_value']:.2f}")
        print(f"Cash: ${summary['cash']:.2f} ({summary['cash_allocation']*100:.1f}%)")
        
        print("\nAsset Allocations:")
        for asset in summary['assets']:
            print(f"{asset['symbol']}: ${asset['current_value']:.2f} ({asset['allocation']*100:.1f}%)")
    else:
        print(f"Could not find price data for {symbol_to_buy}")

if __name__ == "__main__":
    run_integration_test()