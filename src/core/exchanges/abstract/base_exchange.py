import time
from abc import abstractmethod
from typing import Dict, List, Optional, Any, Union
from .exchange_interface import ExchangeInterface
import aiohttp
import asyncio
from datetime import datetime
import hmac
import hashlib
import json
from urllib.parse import urlencode
from utils.logger import Logger
from dotenv import load_dotenv
import os
from ...enums import HttpMethod

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
        
        # Set up logging
        self.logger = Logger("exchange")
        self.logger.clear_log()
        self.logger.info("Cleared log file")

        self.exchange_name = exchange_name
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_semaphore = asyncio.Semaphore(10)  # Rate limiting
        
        # Initialize but don't set credentials yet
        self.api_key = None
        self.api_secret = None
        self.rate_limit = kwargs.get('rate_limit', 1.0)  # Default 1 request per second
        self.last_request_time = 0
        
    async def __aenter__(self):
        """Async context manager entry"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        # Initialize API credentials if not already set
        if not self.api_key or not self.api_secret:
            self.api_key = os.getenv(f'{self.exchange_name.upper()}_API_KEY')
            self.api_secret = os.getenv(f'{self.exchange_name.upper()}_API_SECRET')
            
            if not self.api_key or not self.api_secret:
                self.logger.warning(f"No API credentials found for {self.exchange_name}")
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def initialize(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, **kwargs):
        """Initialize with API credentials"""
        # Get API credentials from environment variables if not provided
        self.api_key = api_key or os.getenv(f'{self.exchange_name.upper()}_API_KEY')
        self.api_secret = api_secret or os.getenv(f'{self.exchange_name.upper()}_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            self.logger.warning(f"No API credentials found for {self.exchange_name}")
            
        # Initialize session if not already done
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """
        Get the base URL for the exchange API
        
        Returns:
            str: The base URL for the exchange
        """
        pass
    
    async def _handle_rate_limit(self):
        """Ensure we don't exceed rate limits using asyncio sleep"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.rate_limit:
            await asyncio.sleep(self.rate_limit - time_since_last_request)
        self.last_request_time = time.time()
    
    async def _handle_error(self, response: aiohttp.ClientResponse) -> None:
        """
        Handle common API errors
        
        Args:
            response: The API response to check for errors
            
        Raises:
            Exception: If the response contains an error
        """
        if response.status != 200:
            error_text = await response.text()
            error_msg = f"API Error: {response.status} - {error_text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
            
        try:
            if response.content_type == 'application/json':
                data = await response.json()
                if isinstance(data, dict) and ('error' in data or 'code' in data):
                    error_msg = data.get('error') or data.get('msg') or str(data)
                    self.logger.error(f"Exchange Error: {error_msg}")
                    raise Exception(f"Exchange Error: {error_msg}")
        except ValueError:
            pass  # Not JSON response, ignore
    
    async def _make_request(self, method: HttpMethod, endpoint: str, params: Optional[Dict] = None, 
                    headers: Optional[Dict] = None, signed: bool = False) -> Dict[str, Any]:
        """
        Make an HTTP request to the exchange API using aiohttp.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters or request body
            headers: Request headers
            signed: Whether to sign the request
            
        Returns:
            Dict containing the API response
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' or call initialize()")
            
        async with self.request_semaphore:  # Rate limiting
            await self._handle_rate_limit()
            
            url = f"{self.base_url}{endpoint}"
            
            if signed:
                headers = await self._get_signed_headers(method, endpoint, params)
                
            try:
                async with self.session.request(
                    method.value, 
                    url,
                    params=params if method in [HttpMethod.GET, HttpMethod.DELETE] else None,
                    json=params if method not in [HttpMethod.GET, HttpMethod.DELETE] else None,
                    headers=headers
                ) as response:
                    await self._handle_error(response)
                    return await response.json()
            except aiohttp.ClientError as e:
                self.logger.error(f"Request failed: {str(e)}")
                raise
    
    @abstractmethod
    async def _get_signed_headers(self, method: HttpMethod, endpoint: str, params: Optional[Dict] = None) -> Dict[str, str]:
        """
        Generate signed headers for authenticated requests
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Dict containing signed headers
        """
        pass

    @abstractmethod
    def _format_symbol(self, symbol: str) -> str:
        """
        Convert a standard symbol format (e.g., BTC/USDT) to Exchange specific format
        
        Args:
            symbol: Symbol in standard format with slash separator
            
        Returns:
            Symbol in Exchange specific format 
        """
        pass
    
    @abstractmethod
    async def _create_signature(self, method: HttpMethod, endpoint: str, query_string: str, timestamp: str) -> str:
        """
        Create a signature for authenticated requests
        
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
        """
        Get current ticker data for a trading pair
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            
        Returns:
            Dict containing ticker data
        """
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


