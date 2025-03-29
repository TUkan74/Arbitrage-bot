import time
from abc import abstractmethod
from typing import Dict, List, Optional, Any, Union
from .exchange_interface import ExchangeInterface
import requests
from datetime import datetime
import hmac
import hashlib
import json
from urllib.parse import urlencode
from utils.logging.logger import Logger
from dotenv import load_dotenv
import os

class BaseExchange(ExchangeInterface):
    """Base class for all exchanges."""
    
    def __init__(self, exchange_name: str, **kwargs):
        """
        Initialize the base exchange with common functionality
        
        Args:
            exchange_name: Name of the exchange (e.g., 'BINANCE', 'KUCOIN')
            **kwargs: Additional parameters specific to exchanges
        """
        # Load environment variables
        load_dotenv()
        
        # Get API credentials from environment variables
        self.api_key = os.getenv(f'{exchange_name.upper()}_API_KEY')
        self.api_secret = os.getenv(f'{exchange_name.upper()}_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            self.logger.warning(f"No API credentials found for {exchange_name}")
        
        self.rate_limit = kwargs.get('rate_limit', 1.0)  # Default 1 request per second
        self.last_request_time = 0
        self.logger = Logger("exchange")
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """
        Get the base URL for the exchange API
        
        Returns:
            str: The base URL for the exchange
        """
        pass
    
    def _handle_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.rate_limit:
            self.logger.debug(f"Rate limiting: waiting {self.rate_limit - time_since_last_request:.2f} seconds")
            time.sleep(self.rate_limit - time_since_last_request)
        self.last_request_time = time.time()
    
    def _handle_error(self, response: requests.Response) -> None:
        """
        Handle common API errors
        
        Args:
            response: The API response to check for errors
            
        Raises:
            Exception: If the response contains an error
        """
        if response.status_code != 200:
            error_msg = f"API Error: {response.status_code} - {response.text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
            
        try:
            data = response.json()
            if 'error' in data:
                error_msg = f"Exchange Error: {data['error']}"
                self.logger.error(error_msg)
                raise Exception(error_msg)
        except json.JSONDecodeError:
            pass  # Not JSON response, ignore
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     headers: Optional[Dict] = None, signed: bool = False) -> Dict[str, Any]:
        """
        Make an HTTP request to the exchange API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            headers: Request headers
            signed: Whether to sign the request
            
        Returns:
            Dict containing the API response
        """
        self._handle_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        if params:
            query_string = urlencode(params)
            url = f"{url}?{query_string}"
            
        if signed and self.api_key and self.api_secret:
            headers = self._get_signed_headers(method, endpoint, params)
            
        try:
            self.logger.debug(f"Making {method} request to {endpoint}")
            response = requests.request(method, url, headers=headers)
            self._handle_error(response)
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise
    
    def _get_signed_headers(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, str]:
        """
        Generate signed headers for authenticated requests
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Dict containing signed headers
        """
        timestamp = str(int(time.time() * 1000))
        query_string = urlencode(params) if params else ""
        
        # Create signature string (exchange-specific implementations will override this)
        signature = self._create_signature(method, endpoint, query_string, timestamp)
        
        return {
            'X-API-KEY': self.api_key,
            'X-TIMESTAMP': timestamp,
            'X-SIGNATURE': signature
        }
    
    @abstractmethod
    def _create_signature(self, method: str, endpoint: str, query_string: str, timestamp: str) -> str:
        """
        Create signature for authenticated requests (to be implemented by specific exchanges)
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            query_string: Query parameters as string
            timestamp: Current timestamp
            
        Returns:
            String containing the signature
        """
        pass
    
    # Market Data Methods
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_exchange_info(self) -> Dict[str, Any]:
        pass
    
    # Trading Methods
    @abstractmethod
    def get_balance(self) -> Dict[str, float]:
        pass
    
    @abstractmethod
    def get_trading_fees(self, symbol: Optional[str] = None) -> Dict[str, float]:
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, order_type: str, side: str, 
                   amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        pass
    
    # Advanced Methods
    @abstractmethod
    def transfer(self, currency: str, amount: float, from_account: str, 
                to_account: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def withdraw(self, currency: str, amount: float, address: str, **params) -> Dict[str, Any]:
        pass


