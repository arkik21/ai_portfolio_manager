# price_fetcher

Price Fetcher Module

This module fetches current and historical price data for cryptocurrencies
from the KuCoin API. Future versions will include IBKR for stocks.

**Module Path:** `price_fetcher`

## Table of Contents

### Classes

- [PriceFetcher](#pricefetcher)
- [DummyKuCoinClient](#dummykucoinclient)

## Classes

### PriceFetcher

Handler for KuCoin API interactions.

#### Methods

##### `__init__(config_path, assets_path, storage_path=None, test_mode=False)`

Initialize the KuCoin API client.

Args:
    config_path: Path to configuration file containing API credentials
    assets_path: Path to assets configuration file
    storage_path: Path to store price data (optional)
    test_mode: Force using dummy implementation regardless of API availability

**Type Hints:**

- **config_path**: `str`
- **assets_path**: `str`
- **storage_path**: `str`
- **test_mode**: `bool`

##### `_load_config(file_path)`

Load YAML configuration file with improved error handling.

**Type Hints:**

- **file_path**: `str`
- **returns**: `Dict[str, Any]`

##### `get_current_price(symbol)`

Get current price for a trading pair on KuCoin.

Args:
    symbol: Trading pair symbol (e.g., BTC-USDT)
    
Returns:
    Dictionary with price data or None if request fails

**Type Hints:**

- **symbol**: `str`
- **returns**: `Optional[Dict[str, Any]]`

##### `_calculate_change_percent(stats)`

Calculate 24h price change percentage from stats.

**Type Hints:**

- **stats**: `Dict[str, Any]`
- **returns**: `float`

##### `get_historical_prices(symbol, days=30, interval='1day')`

Get historical price data for a symbol from KuCoin.

Args:
    symbol: Trading pair symbol (e.g., BTC-USDT)
    days: Number of days of historical data to fetch
    interval: Kline interval (e.g., 1min, 1hour, 1day)
    
Returns:
    List of historical price data points or None if request fails

**Type Hints:**

- **symbol**: `str`
- **days**: `int`
- **interval**: `str`
- **returns**: `Optional[List[Dict[str, Any]]]`

##### `fetch_crypto_prices()`

Fetch current prices for all configured cryptocurrencies.

**Type Hints:**

- **returns**: `Dict[str, Any]`

##### `_save_price_data(symbol, price_data)`

Save price data to a file.

**Type Hints:**

- **symbol**: `str`
- **price_data**: `Dict[str, Any]`
- **returns**: `bool`

##### `fetch_crypto_historical(days=30)`

Fetch historical prices for all configured cryptocurrencies.

**Type Hints:**

- **days**: `int`
- **returns**: `Dict[str, Any]`

##### `_save_historical_data(symbol, data)`

Save historical data to a file.

**Type Hints:**

- **symbol**: `str`
- **data**: `List[Dict[str, Any]]`
- **returns**: `bool`

##### `get_latest_prices()`

Get the latest available prices for all configured cryptocurrencies.

**Type Hints:**

- **returns**: `Dict[str, Dict[str, Any]]`

##### `place_market_order(symbol, side, amount)`

Place a market order on KuCoin.

Args:
    symbol: Trading pair symbol (e.g., BTC-USDT)
    side: Order side (buy or sell)
    amount: Order amount
    
Returns:
    Dictionary with order result or None if request fails

**Type Hints:**

- **symbol**: `str`
- **side**: `str`
- **amount**: `float`
- **returns**: `Optional[Dict[str, Any]]`

##### `place_limit_order(symbol, side, amount, price)`

Place a limit order on KuCoin.

Args:
    symbol: Trading pair symbol (e.g., BTC-USDT)
    side: Order side (buy or sell)
    amount: Order amount (in base currency, e.g., BTC)
    price: Limit price
    
Returns:
    Dictionary with order result or None if request fails

**Type Hints:**

- **symbol**: `str`
- **side**: `str`
- **amount**: `float`
- **price**: `float`
- **returns**: `Optional[Dict[str, Any]]`

##### `get_account_balance()`

Get account balance from KuCoin.

Returns:
    Dictionary with balance information or None if request fails

**Type Hints:**

- **returns**: `Optional[Dict[str, Any]]`

### DummyKuCoinClient

A dummy implementation of the KuCoin client for development and testing.

#### Methods

##### `__init__()`

##### `get_timestamp()`

Get server timestamp.

##### `get_ticker(symbol)`

Get ticker information for a symbol.

##### `get_24hr_stats(symbol)`

Get 24hr stats for a symbol.

##### `get_kline_data(symbol, kline_type, start, end)`

Get kline data for a symbol.

##### `get_accounts()`

Get account information.

##### `create_market_order(symbol, side)`

Create a market order.

##### `create_limit_order(symbol, side, price, size)`

Create a limit order.

