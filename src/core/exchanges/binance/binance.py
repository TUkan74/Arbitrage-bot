from typing import Any, Dict, Optional
import hmac
import hashlib
import requests
from urllib.parse import urlencode
import base64
import time

from .binance_normalizer import BinanceNormalizer
from ..abstract.base_exchange import BaseExchange
from ...enums import HttpMethod



class BinanceExchange(BaseExchange):
    def __init__(self,**kwargs):
        super().__init__(
            exchange_name="BINANCE"
        )
        self.normalizer = BinanceNormalizer()
        
    @property
    def base_url(self) -> str:
        return "https://api1.binance.com"

    @property
    def public_data_url(self) -> str:
        """Base URL for public market data endpoints"""
        return "https://data-api.binance.vision"

    def _create_signature(self, method: HttpMethod, endpoint: str, query_string: str, timestamp: str) -> str:
        """
        Create signature for Binance API requests using either HMAC-SHA256 or Ed25519
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            query_string: Query parameters as string
            timestamp: Current timestamp
            
        Returns:
            String containing the signature
        """
        # For Binance, we need to add timestamp to the query string
        msg = query_string
        if msg:
            msg += f"&timestamp={timestamp}"
        else:
            msg = f"timestamp={timestamp}"
            
        # Check if we're using Ed25519 key
        if hasattr(self, 'private_key') and self.private_key:
            # Sign with Ed25519
            signature = base64.b64encode(
                self.private_key.sign(msg.encode('ASCII'))
            ).decode('utf-8')
        else:
            # Fallback to HMAC-SHA256
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                msg.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
        
        return signature

    def _get_signed_headers(self, method: HttpMethod, endpoint: str, params: Optional[Dict] = None) -> Dict[str, str]:
        """
        Get headers for signed requests
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Dict containing request headers
        """
        # Only include the API key in headers
        headers = {
            'X-MBX-APIKEY': self.api_key
        }
        
        return headers

    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information and trading rules
        
        Returns:
            Dict containing exchange information
        """
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v3/exchangeInfo")
        
        return self.normalizer.normalize_exchange_info(response)
    
    def _format_symbol(self, symbol: str) -> str:
        """
        Convert a standard symbol format (e.g., BTC/USDT) to Binance format (e.g., BTCUSDT)
        
        Args:
            symbol: Symbol in standard format with slash separator
            
        Returns:
            Symbol in Binance format without separator
        """
        # Handle both formats
        if '/' in symbol:
            return symbol.replace('/', '')
        return symbol
        
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current ticker data for a trading pair
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT" or "BTCUSDT")
            
        Returns:
            Dict containing normalized ticker data
        """
        binance_symbol = self._format_symbol(symbol)
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v3/ticker/24hr",
            params={"symbol": binance_symbol}
        )
        self.logger.debug(f"Raw Binance ticker response: {response}")
        
        return self.normalizer.normalize_ticker(symbol,response)
        

    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get order book data for a trading pair
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT" or "BTCUSDT")
            limit: Number of orders to retrieve on each side
            
        Returns:
            Dict containing normalized order book data
        """
        binance_symbol = self._format_symbol(symbol)
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v3/depth",
            params={"symbol": binance_symbol, "limit": limit}
        )
        self.logger.debug(f"Raw order book response: {response}")
        
        return self.normalizer.normalize_order_book(symbol,response)

    def get_balance(self) -> Dict[str, float]:
        """
        Get account balances
        
        Returns:
            Dict mapping asset symbols to available balances
        """
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v3/account",
            signed=True
        )
        self.logger.debug(f"Balance response: {response}")
        
        return self.normalizer.normalize_balance(response)
    
    def get_trading_fees(self, symbol: Optional[str] = None) -> Dict[str, float]:
        """
        Get trading fees for a symbol or all symbols
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT" or "BTCUSDT") or None for all
            
        Returns:
            Dict mapping symbols to their fee rates (maker and taker)
        """
        params = {}
        if symbol:
            binance_symbol = self._format_symbol(symbol)
            params["symbol"] = binance_symbol
            
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v3/tradeFee",
            params=params,
            signed=True
        )
        self.logger.debug(f"Trading fees response: {response}")
        
        return self.normalizer.normalize_trading_fees(response)
        
    # Required by interface but not implemented in Phase 2
    def transfer(self, currency: str, amount: float, from_account: str, 
                to_account: str) -> Dict[str, Any]:
        """Not implemented in Phase 2"""
        self.logger.warning("Method not implemented in Phase 2")
        return {"success": False, "message": "Method not implemented in Phase 2"}
    
    def withdraw(self, currency: str, amount: float, address: str, **params) -> Dict[str, Any]:
        """Not implemented in Phase 2"""
        self.logger.warning("Method not implemented in Phase 2")
        return {"success": False, "message": "Method not implemented in Phase 2"}
    
    def place_order(self, symbol: str, order_type: str, side: str, 
                   amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        """
        Place a new order on the exchange
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT" or "BTCUSDT")
            order_type: Type of order ('LIMIT', 'MARKET')
            side: Order side ('BUY', 'SELL')
            amount: Quantity to trade
            price: Price for limit orders (None for market orders)
            
        Returns:
            Dict containing order details
        """
        binance_symbol = self._format_symbol(symbol)
        params = {
            "symbol": binance_symbol, 
            "type": order_type, 
            "side": side, 
            "quantity": amount
        }
        
        if price and order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = "GTC"  # Good Till Cancelled
            
        response = self._make_request(
            method=HttpMethod.POST,
            endpoint="/api/v3/order",
            params=params,
            signed=True
        )
        self.logger.debug(f"Order response: {response}")
        
        return self.normalizer.normalize_order(response)
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Cancel an existing order
        
        Args:
            order_id: ID of the order to cancel
            symbol: Trading pair symbol (e.g., "BTC/USDT" or "BTCUSDT")
            
        Returns:
            Dict containing cancellation confirmation
        """
        binance_symbol = self._format_symbol(symbol)
        response = self._make_request(
            method=HttpMethod.DELETE,
            endpoint="/api/v3/order",
            params={"orderId": order_id, "symbol": binance_symbol},
            signed=True
        )
        self.logger.debug(f"Cancel order response: {response}")
        
        return self.normalizer.normalize_order(response)
    
    def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Get the status of an order
        
        Args:
            order_id: ID of the order to check
            symbol: Trading pair symbol (e.g., "BTC/USDT" or "BTCUSDT")
            
        Returns:
            Dict containing order details
        """
        binance_symbol = self._format_symbol(symbol)
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v3/order",
            params={"orderId": order_id, "symbol": binance_symbol},
            signed=True
        )
        self.logger.debug(f"Get order response: {response}")
        
        return self.normalizer.normalize_order(symbol,response)

    def _make_request(self, method: HttpMethod, endpoint: str, params: Optional[Dict] = None, 
                     headers: Optional[Dict] = None, signed: bool = False) -> Dict[str, Any]:
        """
        Override base _make_request to use different base URLs for public/private endpoints
        """
        self._handle_rate_limit()
        
        # Use public data URL for public market data endpoints
        if not signed and (endpoint.startswith("/api/v3/ticker") or 
                          endpoint.startswith("/api/v3/depth") or
                          endpoint.startswith("/api/v3/exchangeInfo") or
                          endpoint == "api/v3/exchangeInfo"):
            base = self.public_data_url
        else:
            base = self.base_url
            
        # Ensure endpoint starts with a slash
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
            
        url = f"{base}{endpoint}"
        
        # Add timestamp and signature for signed requests
        if signed and self.api_key:
            timestamp = str(int(time.time() * 1000))
            if params is None:
                params = {}
            params['timestamp'] = timestamp
            
            # Get signed headers
            headers = self._get_signed_headers(method, endpoint, params)
            
            # Add signature to params for Ed25519
            if hasattr(self, 'private_key') and self.private_key:
                query_string = urlencode(params)
                signature = self._create_signature(method, endpoint, query_string, timestamp)
                params['signature'] = signature
            
            url = f"{url}?{urlencode(params)}"
        elif params:
            url = f"{url}?{urlencode(params)}"
            
        try:
            self.logger.debug(f"Making {method.value} request to {url}")
            response = requests.request(method.value, url, headers=headers)
            self._handle_error(response)
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise



