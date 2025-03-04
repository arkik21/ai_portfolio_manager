"""
Portfolio with Real Price Fetching

This script demonstrates the Portfolio Manager using real price data
from the KuCoin API.
"""

import os
import sys
import time
from datetime import datetime

# Add the parent directory to sys.path to import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import the Portfolio and PriceFetcher classes
from modules.portfolio_manager import Portfolio
from modules.price_fetcher import PriceFetcher

def run_with_real_prices():
    """Run the portfolio manager with real price data."""
    print("\n====== Portfolio Manager with Real Price Data ======\n")
    
    # Paths for configuration and data
    config_path = os.path.join(parent_dir, "config", "settings.yaml")
    assets_path = os.path.join(parent_dir, "config", "assets.yaml")
    portfolio_path = os.path.join(parent_dir, "data", "portfolio")
    prices_path = os.path.join(parent_dir, "data", "prices")
    
    # Create directories if they don't exist
    os.makedirs(portfolio_path, exist_ok=True)
    os.makedirs(prices_path, exist_ok=True)
    
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Using config: {config_path}")
    print(f"Using assets: {assets_path}")
    
    # Initialize the PriceFetcher with real API (test_mode=False)
    print("\nInitializing PriceFetcher with real API...")
    price_fetcher = PriceFetcher(
        config_path=config_path,
        assets_path=assets_path,
        storage_path=prices_path,
        test_mode=False  # Use real API
    )
    
    # Initialize the Portfolio Manager
    print("\nInitializing Portfolio Manager...")
    portfolio = Portfolio(
        config_path=config_path,
        storage_path=portfolio_path
    )
    
    # Connect the price fetcher to the portfolio
    portfolio.price_fetcher = price_fetcher
    
    # Get current portfolio state
    print("\n[1] Current Portfolio State:")
    summary = portfolio.get_portfolio_summary()
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Value: ${summary['total_value']:.2f}")
    print(f"Cash: ${summary['cash']:.2f} ({summary['cash_allocation']*100:.1f}%)")
    
    print("\nAsset Allocations:")
    for asset in summary['assets']:
        print(f"{asset['symbol']}: ${asset['current_value']:.2f} ({asset['allocation']*100:.1f}%)")
    
    # Fetch current prices
    print("\n[2] Fetching Current Market Prices:")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    prices = price_fetcher.fetch_crypto_prices()
    
    if prices:
        print(f"Successfully fetched prices for {len(prices)} assets:")
        for symbol, price_data in prices.items():
            print(f"  {symbol}: ${price_data['price']:.2f} ({price_data['change_24h_percent']:.2f}%)")
        
        # Update portfolio with fresh prices
        print("\n[3] Updating Portfolio with Fresh Market Prices:")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        portfolio.update_prices()
        
        # Show updated portfolio
        print("\n[4] Updated Portfolio After Price Update:")
        summary = portfolio.get_portfolio_summary()
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Value: ${summary['total_value']:.2f}")
        print(f"Cash: ${summary['cash']:.2f} ({summary['cash_allocation']*100:.1f}%)")
        
        print("\nAsset Allocations:")
        for asset in summary['assets']:
            print(f"{asset['symbol']}: ${asset['current_value']:.2f} ({asset['allocation']*100:.1f}%)")
        
        # Option to record a new trade
        print("\n[5] Record New Trade? (Enter 'y' to continue)")
        choice = input("Record a new trade? (y/n): ")
        
        if choice.lower() == 'y':
            # Get available symbols
            available_symbols = list(prices.keys())
            
            # Display available assets
            print("\nAvailable Assets:")
            for i, symbol in enumerate(available_symbols):
                price = prices[symbol]['price']
                print(f"{i+1}. {symbol} (Current price: ${price:.2f})")
            
            # Get user input for the trade
            try:
                symbol_idx = int(input(f"Select asset (1-{len(available_symbols)}): ")) - 1
                if 0 <= symbol_idx < len(available_symbols):
                    symbol = available_symbols[symbol_idx]
                    
                    action = input("Action (buy/sell): ").lower()
                    if action not in ['buy', 'sell']:
                        print("Invalid action. Must be 'buy' or 'sell'.")
                        return
                    
                    amount = float(input("USD amount: "))
                    if amount <= 0:
                        print("Amount must be greater than 0.")
                        return
                    
                    # Calculate quantity based on current price
                    current_price = prices[symbol]['price']
                    quantity = amount / current_price
                    
                    # Record the trade
                    print(f"\nRecording trade: {action.upper()} {quantity:.8f} {symbol} at ${current_price:.2f}")
                    success = portfolio.record_trade(
                        symbol=symbol,
                        action=action,
                        quantity=quantity,
                        price=current_price,
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                    
                    if success:
                        print("Trade recorded successfully!")
                    else:
                        print("Failed to record trade.")
                    
                    # Show final portfolio
                    print("\n[6] Final Portfolio State:")
                    portfolio.update_prices()
                    summary = portfolio.get_portfolio_summary()
                    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"Total Value: ${summary['total_value']:.2f}")
                    print(f"Cash: ${summary['cash']:.2f} ({summary['cash_allocation']*100:.1f}%)")
                    
                    print("\nAsset Allocations:")
                    for asset in summary['assets']:
                        print(f"{asset['symbol']}: ${asset['current_value']:.2f} ({asset['allocation']*100:.1f}%)")
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Invalid input. Please enter numeric values where required.")
            except Exception as e:
                print(f"Error processing trade: {e}")
    else:
        print("Failed to fetch current prices. Check your API credentials and connection.")

if __name__ == "__main__":
    run_with_real_prices()