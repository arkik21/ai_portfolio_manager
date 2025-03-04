"""
Portfolio Manager Module

This module tracks the portfolio composition, calculates allocations,
and provides data for decision making.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('portfolio_manager')

class Portfolio:
    """Manages portfolio composition, allocations, and tracking."""
    
    def __init__(self, config_path: str, storage_path: str):
        """
        Initialize the Portfolio Manager.
        
        Args:
            config_path: Path to the configuration file
            storage_path: Path to store portfolio data
        """
        self.config_path = config_path
        self.storage_path = storage_path
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load configuration
        self.config = self._load_yaml(config_path)
        
        # Portfolio constraints
        self.max_allocation = self.config.get('portfolio', {}).get('max_allocation_per_asset', 0.15)
        self.min_allocation = self.config.get('portfolio', {}).get('min_allocation_per_asset', 0.01)
        self.risk_tolerance = self.config.get('portfolio', {}).get('risk_tolerance', 'moderate')
        
        # Initial capital
        self.initial_capital = self.config.get('portfolio', {}).get('initial_capital', 10000.0)
        
        # Load portfolio data or initialize with defaults
        self.holdings = self._load_portfolio() or self._initialize_portfolio()
        
        # Load price fetcher (should be initialized elsewhere)
        self.price_fetcher = None
    
    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file) or {}
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return {}
    
    def _load_portfolio(self) -> Optional[Dict[str, Any]]:
        """Load portfolio data from storage."""
        portfolio_path = os.path.join(self.storage_path, "portfolio.json")
        if os.path.exists(portfolio_path):
            try:
                with open(portfolio_path, 'r') as file:
                    return json.load(file)
            except Exception as e:
                logger.error(f"Failed to load portfolio data: {e}")
        return None
    
    def _initialize_portfolio(self) -> Dict[str, Any]:
        """Initialize a new portfolio with default values."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        return {
            "created_at": current_date,
            "updated_at": current_date,
            "initial_capital": self.initial_capital,
            "cash": self.initial_capital,
            "total_value": self.initial_capital,
            "holdings": {},
            "history": [{
                "date": current_date,
                "total_value": self.initial_capital,
                "cash": self.initial_capital,
                "holdings": {}
            }]
        }
    
    def save_portfolio(self) -> bool:
        """Save portfolio data to storage."""
        try:
            portfolio_path = os.path.join(self.storage_path, "portfolio.json")
            with open(portfolio_path, 'w') as file:
                json.dump(self.holdings, file, indent=2)
            logger.info("Portfolio data saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save portfolio data: {e}")
            return False
    
    def update_prices(self, price_fetcher=None) -> bool:
        """
        Update current prices and total portfolio value.
        
        Args:
            price_fetcher: Optional PriceFetcher instance
            
        Returns:
            True if successful, False otherwise
        """
        if price_fetcher:
            self.price_fetcher = price_fetcher
            
        if not self.price_fetcher:
            logger.error("No price fetcher available")
            return False
        
        # Get latest prices
        latest_prices = self.price_fetcher.get_latest_prices()
        if not latest_prices:
            logger.error("Failed to fetch latest prices")
            return False
        
        # Update each holding's current value
        total_value = self.holdings.get("cash", 0)
        
        for symbol, holding in self.holdings.get("holdings", {}).items():
            # Get current price
            price_data = latest_prices.get(symbol)
            if not price_data:
                logger.warning(f"No price data for {symbol}")
                continue
            
            current_price = price_data.get("price", 0)
            if current_price:
                # Update holding value
                quantity = holding.get("quantity", 0)
                current_value = quantity * current_price
                
                # Calculate profit/loss
                cost_basis = holding.get("cost_basis", 0)
                profit_loss = current_value - cost_basis
                profit_loss_percent = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0
                
                # Update holding data
                holding["current_price"] = current_price
                holding["current_value"] = current_value
                holding["profit_loss"] = profit_loss
                holding["profit_loss_percent"] = profit_loss_percent
                holding["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Add to total value
                total_value += current_value
        
        # Update total portfolio value
        self.holdings["total_value"] = total_value
        self.holdings["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate allocations
        self.calculate_allocations()
        
        # Save updated portfolio
        self.save_portfolio()
        
        return True
    
    def calculate_allocations(self) -> Dict[str, float]:
        """
        Calculate current allocation percentages for each asset.
        
        Returns:
            Dictionary of symbol -> allocation percentage
        """
        total_value = self.holdings.get("total_value", 0)
        if total_value <= 0:
            logger.warning("Total portfolio value is zero or negative")
            return {}
        
        # Calculate cash allocation
        cash = self.holdings.get("cash", 0)
        cash_allocation = cash / total_value
        
        allocations = {"cash": cash_allocation}
        
        # Calculate allocation for each asset
        for symbol, holding in self.holdings.get("holdings", {}).items():
            current_value = holding.get("current_value", 0)
            allocation = current_value / total_value
            
            # Update holding with allocation percentage
            holding["allocation"] = allocation
            
            # Add to allocations dictionary
            allocations[symbol] = allocation
        
        return allocations
    
    def get_current_allocation(self, symbol: str) -> float:
        """
        Get current allocation percentage for a specific asset.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Allocation percentage (0.0 to 1.0)
        """
        if symbol == "cash":
            cash = self.holdings.get("cash", 0)
            total_value = self.holdings.get("total_value", 0)
            return cash / total_value if total_value > 0 else 0
            
        holding = self.holdings.get("holdings", {}).get(symbol)
        if not holding:
            return 0.0
            
        return holding.get("allocation", 0.0)
    
    def get_available_cash(self) -> float:
        """Get available cash balance."""
        return self.holdings.get("cash", 0)
    
    def get_total_value(self) -> float:
        """Get total portfolio value including cash."""
        return self.holdings.get("total_value", 0)
    
    def record_trade(self, symbol: str, action: str, quantity: float, 
                   price: float, timestamp: Optional[str] = None) -> bool:
        """
        Record a trade and update portfolio holdings.
        
        Args:
            symbol: Asset symbol
            action: Trade action (buy or sell)
            quantity: Quantity traded
            price: Trade price
            timestamp: Trade timestamp (default: current time)
            
        Returns:
            True if successful, False otherwise
        """
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        # Calculate trade value
        trade_value = quantity * price
        
        # Handle buy/sell differently
        if action.lower() == "buy":
            # Check if enough cash is available
            cash = self.holdings.get("cash", 0)
            if trade_value > cash:
                logger.error(f"Insufficient cash for {action} {quantity} {symbol} at ${price}")
                return False
                
            # Update cash balance
            self.holdings["cash"] = cash - trade_value
            
            # Add to or update holdings
            holdings = self.holdings.get("holdings", {})
            if symbol not in holdings:
                holdings[symbol] = {
                    "symbol": symbol,
                    "quantity": quantity,
                    "cost_basis": trade_value,
                    "average_price": price,
                    "current_price": price,
                    "current_value": trade_value,
                    "profit_loss": 0,
                    "profit_loss_percent": 0,
                    "first_purchased": timestamp,
                    "last_updated": timestamp
                }
            else:
                # Update existing holding
                holding = holdings[symbol]
                old_quantity = holding.get("quantity", 0)
                old_cost_basis = holding.get("cost_basis", 0)
                
                # Calculate new totals
                new_quantity = old_quantity + quantity
                new_cost_basis = old_cost_basis + trade_value
                
                # Update holding
                holding["quantity"] = new_quantity
                holding["cost_basis"] = new_cost_basis
                holding["average_price"] = new_cost_basis / new_quantity if new_quantity > 0 else 0
                holding["current_price"] = price
                holding["current_value"] = new_quantity * price
                holding["last_updated"] = timestamp
        
        elif action.lower() == "sell":
            # Check if holding exists and has enough quantity
            holdings = self.holdings.get("holdings", {})
            if symbol not in holdings:
                logger.error(f"Cannot sell {symbol}: not in holdings")
                return False
                
            holding = holdings[symbol]
            available_quantity = holding.get("quantity", 0)
            
            if quantity > available_quantity:
                logger.error(f"Insufficient quantity of {symbol} to sell")
                return False
                
            # Calculate realized profit/loss
            average_price = holding.get("average_price", 0)
            realized_pl = (price - average_price) * quantity
            
            # Update cash balance
            cash = self.holdings.get("cash", 0)
            self.holdings["cash"] = cash + trade_value
            
            # Update holding
            new_quantity = available_quantity - quantity
            
            if new_quantity <= 0:
                # Remove holding if fully sold
                del holdings[symbol]
            else:
                # Update holding with reduced quantity
                holding["quantity"] = new_quantity
                holding["current_value"] = new_quantity * price
                holding["last_updated"] = timestamp
        
        else:
            logger.error(f"Invalid trade action: {action}")
            return False
        
        # Record trade in history
        trade_record = {
            "timestamp": timestamp,
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "price": price,
            "value": trade_value
        }
        
        # Ensure trades list exists
        if "trades" not in self.holdings:
            self.holdings["trades"] = []
            
        self.holdings["trades"].append(trade_record)
        
        # Update portfolio value and allocations
        self.update_prices()
        
        # Record portfolio snapshot
        self._record_portfolio_snapshot()
        
        return True
    
    def _record_portfolio_snapshot(self) -> None:
        """Record current portfolio state in history."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        snapshot = {
            "date": current_date,
            "total_value": self.holdings.get("total_value", 0),
            "cash": self.holdings.get("cash", 0),
            "holdings": {}
        }
        
        # Copy holdings data without all details
        for symbol, holding in self.holdings.get("holdings", {}).items():
            snapshot["holdings"][symbol] = {
                "quantity": holding.get("quantity", 0),
                "current_value": holding.get("current_value", 0),
                "allocation": holding.get("allocation", 0)
            }
        
        # Add to history
        history = self.holdings.get("history", [])
        history.append(snapshot)
        self.holdings["history"] = history
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current portfolio state.
        
        Returns:
            Dictionary with portfolio summary
        """
        # Ensure prices and allocations are up to date
        self.update_prices()
        
        # Calculate overall profit/loss
        initial_capital = self.holdings.get("initial_capital", 0)
        total_value = self.holdings.get("total_value", 0)
        
        total_profit_loss = total_value - initial_capital
        total_profit_loss_percent = (total_profit_loss / initial_capital * 100) if initial_capital > 0 else 0
        
        # Build summary
        summary = {
            "updated_at": self.holdings.get("updated_at", ""),
            "total_value": total_value,
            "initial_capital": initial_capital,
            "cash": self.holdings.get("cash", 0),
            "invested_value": total_value - self.holdings.get("cash", 0),
            "total_profit_loss": total_profit_loss,
            "total_profit_loss_percent": total_profit_loss_percent,
            "asset_count": len(self.holdings.get("holdings", {})),
            "cash_allocation": self.get_current_allocation("cash"),
            "assets": []
        }
        
        # Add data for each asset
        for symbol, holding in self.holdings.get("holdings", {}).items():
            asset_summary = {
                "symbol": symbol,
                "quantity": holding.get("quantity", 0),
                "current_price": holding.get("current_price", 0),
                "current_value": holding.get("current_value", 0),
                "allocation": holding.get("allocation", 0),
                "profit_loss": holding.get("profit_loss", 0),
                "profit_loss_percent": holding.get("profit_loss_percent", 0)
            }
            
            summary["assets"].append(asset_summary)
        
        # Sort assets by allocation (descending)
        summary["assets"].sort(key=lambda x: x["allocation"], reverse=True)
        
        return summary
    
    def get_allocation_recommendations(self) -> Dict[str, Any]:
        """
        Generate recommendations for portfolio rebalancing.
        
        Returns:
            Dictionary with rebalancing recommendations
        """
        # Get current allocations
        allocations = self.calculate_allocations()
        
        # Generate recommendations
        recommendations = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_value": self.holdings.get("total_value", 0),
            "cash": self.holdings.get("cash", 0),
            "actions": []
        }
        
        # Check for overweight assets
        for symbol, allocation in allocations.items():
            if symbol == "cash":
                continue
                
            if allocation > self.max_allocation:
                # Asset is overweight
                excess_allocation = allocation - self.max_allocation
                excess_value = excess_allocation * self.holdings.get("total_value", 0)
                
                recommendations["actions"].append({
                    "symbol": symbol,
                    "action": "REDUCE",
                    "current_allocation": allocation,
                    "target_allocation": self.max_allocation,
                    "value_to_adjust": excess_value
                })
        
        # Check if cash is too high
        cash_allocation = allocations.get("cash", 0)
        max_cash_allocation = self.config.get('portfolio', {}).get('max_cash_allocation', 0.3)
        
        if cash_allocation > max_cash_allocation:
            excess_cash = (cash_allocation - max_cash_allocation) * self.holdings.get("total_value", 0)
            
            recommendations["actions"].append({
                "symbol": "cash",
                "action": "DEPLOY",
                "current_allocation": cash_allocation,
                "target_allocation": max_cash_allocation,
                "value_to_adjust": excess_cash
            })
        
        return recommendations

# Example usage
if __name__ == "__main__":
    portfolio = Portfolio(
        config_path="./config/settings.yaml",
        storage_path="./data/portfolio"
    )
    
    # Print portfolio summary
    summary = portfolio.get_portfolio_summary()
    print(f"Portfolio Value: ${summary['total_value']:.2f}")
    print(f"Cash: ${summary['cash']:.2f} ({summary['cash_allocation']*100:.1f}%)")
    print(f"Profit/Loss: ${summary['total_profit_loss']:.2f} ({summary['total_profit_loss_percent']:.1f}%)")
    
    # Print asset allocations
    print("\nAsset Allocations:")
    for asset in summary['assets']:
        print(f"{asset['symbol']}: ${asset['current_value']:.2f} ({asset['allocation']*100:.1f}%)")