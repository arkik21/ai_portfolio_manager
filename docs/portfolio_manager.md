# portfolio_manager

Portfolio Manager Module

This module tracks the portfolio composition, calculates allocations,
and provides data for decision making.

**Module Path:** `portfolio_manager`

## Table of Contents

### Classes

- [Portfolio](#portfolio)

## Classes

### Portfolio

Manages portfolio composition, allocations, and tracking.

#### Methods

##### `__init__(config_path, storage_path)`

Initialize the Portfolio Manager.

Args:
    config_path: Path to the configuration file
    storage_path: Path to store portfolio data

**Type Hints:**

- **config_path**: `str`
- **storage_path**: `str`

##### `_load_yaml(file_path)`

Load YAML configuration file.

**Type Hints:**

- **file_path**: `str`
- **returns**: `Dict[str, Any]`

##### `_load_portfolio()`

Load portfolio data from storage.

**Type Hints:**

- **returns**: `Optional[Dict[str, Any]]`

##### `_initialize_portfolio()`

Initialize a new portfolio with default values.

**Type Hints:**

- **returns**: `Dict[str, Any]`

##### `save_portfolio()`

Save portfolio data to storage.

**Type Hints:**

- **returns**: `bool`

##### `update_prices(price_fetcher=None)`

Update current prices and total portfolio value.

Args:
    price_fetcher: Optional PriceFetcher instance
    
Returns:
    True if successful, False otherwise

**Type Hints:**

- **returns**: `bool`

##### `calculate_allocations()`

Calculate current allocation percentages for each asset.

Returns:
    Dictionary of symbol -> allocation percentage

**Type Hints:**

- **returns**: `Dict[str, float]`

##### `get_current_allocation(symbol)`

Get current allocation percentage for a specific asset.

Args:
    symbol: Asset symbol
    
Returns:
    Allocation percentage (0.0 to 1.0)

**Type Hints:**

- **symbol**: `str`
- **returns**: `float`

##### `get_available_cash()`

Get available cash balance.

**Type Hints:**

- **returns**: `float`

##### `get_total_value()`

Get total portfolio value including cash.

**Type Hints:**

- **returns**: `float`

##### `record_trade(symbol, action, quantity, price, timestamp=None)`

Record a trade and update portfolio holdings.

Args:
    symbol: Asset symbol
    action: Trade action (buy or sell)
    quantity: Quantity traded
    price: Trade price
    timestamp: Trade timestamp (default: current time)
    
Returns:
    True if successful, False otherwise

**Type Hints:**

- **symbol**: `str`
- **action**: `str`
- **quantity**: `float`
- **price**: `float`
- **timestamp**: `Optional[str]`
- **returns**: `bool`

##### `_record_portfolio_snapshot()`

Record current portfolio state in history.

**Type Hints:**

- **returns**: `None`

##### `get_portfolio_summary()`

Get a summary of the current portfolio state.

Returns:
    Dictionary with portfolio summary

**Type Hints:**

- **returns**: `Dict[str, Any]`

##### `get_allocation_recommendations()`

Generate recommendations for portfolio rebalancing.

Returns:
    Dictionary with rebalancing recommendations

**Type Hints:**

- **returns**: `Dict[str, Any]`

