# order_manager

Order Manager Module

This module manages trading orders based on analysis recommendations.
It handles order creation, validation, and submission to exchanges.

**Module Path:** `order_manager`

## Table of Contents

### Classes

- [OrderManager](#ordermanager)

## Classes

### OrderManager

Manages trading orders based on analysis recommendations.

#### Methods

##### `__init__(config_path, assets_path, output_path=None, test_mode=False)`

Initialize the OrderManager.

Args:
    config_path: Path to settings.yaml
    assets_path: Path to assets.yaml
    output_path: Path to store order data (default: ./orders)
    test_mode: Whether to use dummy implementations instead of real APIs

**Type Hints:**

- **config_path**: `str`
- **assets_path**: `str`
- **output_path**: `str`
- **test_mode**: `bool`

##### `_load_yaml(file_path)`

Load YAML configuration file.

**Type Hints:**

- **file_path**: `str`
- **returns**: `Dict[str, Any]`

##### `_merge_dicts(dict1, dict2)`

Recursively merge dict2 into dict1

##### `_get_asset_info(symbol)`

Get asset information from the configuration.

Args:
    symbol: Asset symbol
    
Returns:
    Asset information dictionary or None if not found

**Type Hints:**

- **symbol**: `str`
- **returns**: `Optional[Dict[str, Any]]`

##### `_validate_order(order)`

Validate an order before submission.

Args:
    order: Order data to validate
    
Returns:
    Dictionary with validation result and errors if any

**Type Hints:**

- **order**: `Dict[str, Any]`
- **returns**: `Dict[str, Any]`

##### `_place_kucoin_order(order)`

Submit an order to KuCoin.

Args:
    order: Validated order data
    
Returns:
    Dictionary with order result

**Type Hints:**

- **order**: `Dict[str, Any]`
- **returns**: `Dict[str, Any]`

##### `_place_dummy_kucoin_order(order)`

Create a dummy order for testing purposes.

Args:
    order: Order data
    
Returns:
    Dictionary with simulated order result

**Type Hints:**

- **order**: `Dict[str, Any]`
- **returns**: `Dict[str, Any]`

##### `_get_current_price(symbol)`

Get the current price for a symbol.

Args:
    symbol: Asset symbol
    
Returns:
    Price information or None if not available

**Type Hints:**

- **symbol**: `str`
- **returns**: `Dict[str, Any]`

##### `create_order_from_signal(signal, allocation=None)`

Create an order from a trade signal.

Args:
    signal: Trade signal from analysis engine
    allocation: Percentage of portfolio to allocate (0.0 to 1.0)
    
Returns:
    Order data or None if no action required

**Type Hints:**

- **signal**: `Dict[str, Any]`
- **allocation**: `float`
- **returns**: `Optional[Dict[str, Any]]`

##### `submit_order(order, confirm=None)`

Submit an order to the appropriate exchange.

Args:
    order: Order data to submit
    confirm: Whether to require confirmation (overrides config setting)
    
Returns:
    Dictionary with submission result

**Type Hints:**

- **order**: `Dict[str, Any]`
- **confirm**: `bool`
- **returns**: `Dict[str, Any]`

##### `cancel_order(order_id)`

Cancel a specific order.

Args:
    order_id: Order ID to cancel
    
Returns:
    Dictionary with cancellation result

**Type Hints:**

- **order_id**: `str`
- **returns**: `Dict[str, Any]`

##### `cancel_all_orders(symbol=None)`

Cancel all orders, optionally filtered by symbol.

Args:
    symbol: Symbol to cancel orders for (e.g., BTC), or None for all
    
Returns:
    Dictionary with cancellation result

**Type Hints:**

- **symbol**: `str`
- **returns**: `Dict[str, Any]`

##### `_find_order(order_id)`

Find an order by ID in local storage.

**Type Hints:**

- **order_id**: `str`
- **returns**: `Optional[Dict[str, Any]]`

##### `_save_cancellation(cancellation)`

Save cancellation data to storage.

**Type Hints:**

- **cancellation**: `Dict[str, Any]`
- **returns**: `bool`

##### `_save_order(order)`

Save order data to storage.

Args:
    order: Order data to save
    
Returns:
    True if saved successfully, False otherwise

**Type Hints:**

- **order**: `Dict[str, Any]`
- **returns**: `bool`

##### `get_order_history(days_back=30)`

Get order history from storage.

Args:
    days_back: Number of days to look back
    
Returns:
    List of order data

**Type Hints:**

- **days_back**: `int`
- **returns**: `List[Dict[str, Any]]`

