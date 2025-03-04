# api_client_manager

API Client Manager Module

This module provides a centralized manager for all external API clients.

**Module Path:** `api_client_manager`

## Table of Contents

### Classes

- [APIClientManager](#apiclientmanager)
- [APIRateLimiter](#apiratelimiter)

### Functions

- [api_request](#api_request)

## Classes

### APIClientManager

Manages connections to external APIs.

#### Methods

##### `__init__(secrets_manager=None, config_path=None)`

Initialize the APIClientManager.

Args:
    secrets_manager: SecretsManager instance for API credentials
    config_path: Path to configuration file with API settings

**Type Hints:**

- **config_path**: `str`

##### `_load_config()`

Load API configuration from file.

**Type Hints:**

- **returns**: `Dict[str, Any]`

##### `_create_session()`

Create a session with retry logic.

**Type Hints:**

- **returns**: `requests.Session`

##### `get_kucoin_client(test_mode=False)`

Get KuCoin API client.

Args:
    test_mode: Whether to use sandbox mode
    
Returns:
    KuCoin client instance

**Type Hints:**

- **test_mode**: `bool`

##### `_get_dummy_kucoin_client(test_mode=False)`

Get dummy KuCoin client for testing or fallback.

Args:
    test_mode: Whether using sandbox mode (not used in dummy)
    
Returns:
    Dummy KuCoin client

**Type Hints:**

- **test_mode**: `bool`

##### `get_youtube_client()`

Get YouTube API client.

Returns:
    YouTube API client

##### `get_deepseek_client(is_analysis=True)`

Get DeepSeek API client.

Args:
    is_analysis: Whether for analysis (Reasoner) or execution (Chat)
    
Returns:
    DeepSeek OpenAI-compatible client

**Type Hints:**

- **is_analysis**: `bool`

##### `close_all_clients()`

Close all API client connections.

### APIRateLimiter

Handles rate limiting for API calls.

#### Methods

##### `__init__(calls_per_minute=60)`

Initialize the APIRateLimiter.

Args:
    calls_per_minute: Maximum calls allowed per minute

**Type Hints:**

- **calls_per_minute**: `int`

##### `wait_if_needed(endpoint)`

Wait if needed to comply with rate limits.

Args:
    endpoint: API endpoint identifier

**Type Hints:**

- **endpoint**: `str`

## Functions

### api_request

```python
api_request(url, method='GET', params=None, data=None, headers=None, auth=None, timeout=30, rate_limiter=None, endpoint_id=None)
```

Make an API request with error handling and rate limiting.

Args:
    url: Request URL
    method: HTTP method
    params: URL parameters
    data: Request data
    headers: Request headers
    auth: Authentication
    timeout: Request timeout
    rate_limiter: Optional APIRateLimiter instance
    endpoint_id: Endpoint identifier for rate limiting
    
Returns:
    Response data
    
Raises:
    APIConnectionError: If connection fails
    APIRateLimitError: If rate limit is exceeded
    APIError: For other API errors

