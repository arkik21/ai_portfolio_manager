"""
API Client Manager Module

This module provides a centralized manager for all external API clients.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
import yaml
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Import custom utility modules
from modules.utils.logging import get_logger
from modules.utils.exceptions import APIConnectionError, APIRateLimitError, APIError

logger = get_logger('api_client_manager')

class APIClientManager:
    """Manages connections to external APIs."""
    
    def __init__(self, secrets_manager=None, config_path: str = None):
        """
        Initialize the APIClientManager.
        
        Args:
            secrets_manager: SecretsManager instance for API credentials
            config_path: Path to configuration file with API settings
        """
        self.secrets_manager = secrets_manager
        self.config_path = config_path
        self.config = self._load_config() if config_path else {}
        
        # Initialize clients
        self.clients = {}
        self.session = self._create_session()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load API configuration from file."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file) or {}
        except Exception as e:
            logger.error(f"Failed to load API config: {e}")
            return {}
    
    def _create_session(self) -> requests.Session:
        """Create a session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retries = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        # Add retry adapter to session
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get_kucoin_client(self, test_mode: bool = False):
        """
        Get KuCoin API client.
        
        Args:
            test_mode: Whether to use sandbox mode
            
        Returns:
            KuCoin client instance
        """
        client_key = f"kucoin_{test_mode}"
        
        # Return existing client if already initialized
        if client_key in self.clients:
            return self.clients[client_key]
        
        # Get credentials from secrets manager
        credentials = {}
        if self.secrets_manager:
            credentials = self.secrets_manager.get_api_keys('kucoin')
        
        # Get settings from config
        settings = self.config.get('apis', {}).get('kucoin', {})
        
        # Override sandbox mode from parameter
        settings['sandbox_mode'] = test_mode
        
        try:
            # Import KuCoin client
            try:
                from kucoin.client import Client
                
                # Extract credentials
                api_key = credentials.get('api_key', '')
                api_secret = credentials.get('api_secret', '')
                api_passphrase = credentials.get('api_passphrase', '')
                
                # Create client
                client = Client(
                    api_key, 
                    api_secret, 
                    api_passphrase, 
                    settings.get('sandbox_mode', True)
                )
                
                # Test connection
                client.get_timestamp()
                
                # Store client
                self.clients[client_key] = client
                logger.info(f"KuCoin client initialized (sandbox: {test_mode})")
                
                return client
                
            except ImportError:
                logger.error("KuCoin client not available. Install with: pip install python-kucoin")
                return self._get_dummy_kucoin_client(test_mode)
                
        except Exception as e:
            logger.error(f"Failed to initialize KuCoin client: {e}")
            return self._get_dummy_kucoin_client(test_mode)
    
    def _get_dummy_kucoin_client(self, test_mode: bool = False):
        """
        Get dummy KuCoin client for testing or fallback.
        
        Args:
            test_mode: Whether using sandbox mode (not used in dummy)
            
        Returns:
            Dummy KuCoin client
        """
        from modules.price_fetcher import DummyKuCoinClient
        dummy_client = DummyKuCoinClient()
        
        # Store in clients
        client_key = f"kucoin_{test_mode}"
        self.clients[client_key] = dummy_client
        logger.info("Using dummy KuCoin client")
        
        return dummy_client
    
    def get_youtube_client(self):
        """
        Get YouTube API client.
        
        Returns:
            YouTube API client
        """
        client_key = "youtube"
        
        # Return existing client if already initialized
        if client_key in self.clients:
            return self.clients[client_key]
        
        # Get credentials from secrets manager
        credentials = {}
        if self.secrets_manager:
            credentials = self.secrets_manager.get_api_keys('youtube_api')
        
        try:
            # Try to import required packages
            try:
                from googleapiclient.discovery import build
                
                # Get API key
                api_key = credentials.get('api_key', '')
                
                if not api_key:
                    logger.error("YouTube API key not found")
                    return None
                
                # Build client
                client = build('youtube', 'v3', developerKey=api_key)
                
                # Store client
                self.clients[client_key] = client
                logger.info("YouTube client initialized")
                
                return client
                
            except ImportError:
                logger.error("Google API client not available. Install with: pip install google-api-python-client")
                return None
                
        except Exception as e:
            logger.error(f"Failed to initialize YouTube client: {e}")
            return None
    
    def get_deepseek_client(self, is_analysis: bool = True):
        """
        Get DeepSeek API client.
        
        Args:
            is_analysis: Whether for analysis (Reasoner) or execution (Chat)
            
        Returns:
            DeepSeek OpenAI-compatible client
        """
        client_key = f"deepseek_{'analysis' if is_analysis else 'execution'}"
        
        # Return existing client if already initialized
        if client_key in self.clients:
            return self.clients[client_key]
        
        # Get credentials from secrets manager
        credentials = {}
        if self.secrets_manager:
            credentials = self.secrets_manager.get_api_keys('deepseek')
        
        try:
            # Try to import required packages
            try:
                from openai import OpenAI
                
                # Get API key
                api_key = credentials.get('api_key', '')
                
                if not api_key:
                    logger.error("DeepSeek API key not found")
                    return None
                
                # Create client
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
                
                # Store client
                self.clients[client_key] = client
                logger.info(f"DeepSeek client initialized for {'analysis' if is_analysis else 'execution'}")
                
                return client
                
            except ImportError:
                logger.error("OpenAI client not available. Install with: pip install openai")
                return None
                
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek client: {e}")
            return None
    
    def close_all_clients(self):
        """Close all API client connections."""
        for key, client in self.clients.items():
            try:
                if hasattr(client, 'close'):
                    client.close()
                logger.info(f"Closed client: {key}")
            except Exception as e:
                logger.error(f"Error closing client {key}: {e}")
        
        # Clear clients
        self.clients = {}
        
        # Close session
        self.session.close()
    
    def __del__(self):
        """Ensure all clients are closed on deletion."""
        self.close_all_clients()


class APIRateLimiter:
    """Handles rate limiting for API calls."""
    
    def __init__(self, calls_per_minute: int = 60):
        """
        Initialize the APIRateLimiter.
        
        Args:
            calls_per_minute: Maximum calls allowed per minute
        """
        self.calls_per_minute = calls_per_minute
        self.interval = 60.0 / calls_per_minute  # Seconds per call
        self.last_call_time = {}  # endpoint -> timestamp
    
    def wait_if_needed(self, endpoint: str):
        """
        Wait if needed to comply with rate limits.
        
        Args:
            endpoint: API endpoint identifier
        """
        now = time.time()
        
        if endpoint in self.last_call_time:
            elapsed = now - self.last_call_time[endpoint]
            if elapsed < self.interval:
                wait_time = self.interval - elapsed
                logger.debug(f"Rate limiting {endpoint}: waiting {wait_time:.2f}s")
                time.sleep(wait_time)
        
        # Update last call time
        self.last_call_time[endpoint] = time.time()


def api_request(url, method="GET", params=None, data=None, headers=None, auth=None, 
              timeout=30, rate_limiter=None, endpoint_id=None):
    """
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
    """
    # Apply rate limiting
    if rate_limiter and endpoint_id:
        rate_limiter.wait_if_needed(endpoint_id)
    
    # Create session with retry logic
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "DELETE"]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    
    try:
        # Make request
        response = session.request(
            method=method,
            url=url,
            params=params,
            json=data,
            headers=headers,
            auth=auth,
            timeout=timeout
        )
        
        # Check for rate limit
        if response.status_code == 429:
            logger.warning(f"Rate limit exceeded for {url}")
            retry_after = int(response.headers.get('Retry-After', 60))
            raise APIRateLimitError(f"Rate limit exceeded. Retry after {retry_after}s.")
        
        # Check for other errors
        response.raise_for_status()
        
        # Return JSON data if available
        try:
            return response.json()
        except ValueError:
            # Return text if not JSON
            return response.text
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        
        if "429" in str(e):
            raise APIRateLimitError(f"Rate limit exceeded: {e}")
        elif "timeout" in str(e).lower():
            raise APIConnectionError(f"Connection timeout: {e}")
        else:
            raise APIConnectionError(f"Connection error: {e}")
    finally:
        session.close()