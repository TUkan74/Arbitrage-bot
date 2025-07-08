from typing import Any, Dict, Optional
import hmac
import hashlib
import aiohttp
from urllib.parse import urlencode
import base64
import time

from .binance_normalizer import BinanceNormalizer
from ..abstract import BaseExchange
from ...enums import HttpMethod


class BinanceExchange(BaseExchange):
    def __init__(self, **kwargs):
        super().__init__(exchange_name="BINANCE")
        self.normalizer = BinanceNormalizer()

    @property
    def base_url(self) -> str:
        return "https://api1.binance.com"

    @property
    def public_data_url(self) -> str:
        """Base URL for public market data endpoints"""
        return "https://data-api.binance.vision"

    async def _create_signature(self, method: HttpMethod, endpoint: str, query_string: str, timestamp: str) -> str:
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
        if hasattr(self, "private_key") and self.private_key:
            # Sign with Ed25519
            signature = base64.b64encode(self.private_key.sign(msg.encode("ASCII"))).decode("utf-8")
        else:
            # Fallback to HMAC-SHA256
            signature = hmac.new(
                self.api_secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256
            ).hexdigest()

        return signature

    async def _get_signed_headers(self, method: HttpMethod, endpoint: str, params: Optional[Dict] = None) -> Dict[str, str]:
        # Only include the API key in headers
        headers = {"X-MBX-APIKEY": self.api_key}

        return headers

    def _format_symbol(self, symbol: str) -> str:
        # Handle both formats
        if "/" in symbol:
            return symbol.replace("/", "")
        return symbol

    async def get_exchange_info(self) -> Dict[str, Any]:
        response = await self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v3/exchangeInfo")
        
        return self.normalizer.normalize_exchange_info(response)
        
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        binance_symbol = self._format_symbol(symbol)
        response = await self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v3/ticker/24hr",
            params={"symbol": binance_symbol}
        )
        self.logger.debug(f"Raw Binance ticker response: {response}")
        
        return self.normalizer.normalize_ticker(symbol,response)
        

    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        binance_symbol = self._format_symbol(symbol)
        response = await self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v3/depth",
            params={"symbol": binance_symbol, "limit": limit}
        )
        # self.logger.debug(f"Raw Binance order book response: {response}")
        return self.normalizer.normalize_order_book(symbol, response)

    async def get_balance(self) -> Dict[str, float]:
        response = await self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v3/account",
            signed=True
        )
        self.logger.debug(f"Balance response: {response}")
        return self.normalizer.normalize_balance(response)
    
    async def get_trading_fees(self, symbol: Optional[str] = None) -> Dict[str, float]:
        params = {}
        if symbol:
            binance_symbol = self._format_symbol(symbol)
            params["symbol"] = binance_symbol
            
        response = await self._make_request(
            method=HttpMethod.GET,
            endpoint="/sapi/v1/asset/tradeFee",
            params=params,
            signed=True
        )
        self.logger.debug(f"Trading fees response: {response}")
        return self.normalizer.normalize_trading_fees(response)

    # Required by interface but not implemented in Phase 2
    async def transfer(self, currency: str, amount: float, from_account: str, 
                to_account: str) -> Dict[str, Any]:
        """Not implemented in Phase 2"""
        self.logger.warning("Method not implemented in Phase 2")
        return {"success": False, "message": "Method not implemented in Phase 2"}
    
    async def withdraw(self, currency: str, amount: float, address: str, **params) -> Dict[str, Any]:
        """Not implemented in Phase 2"""
        self.logger.warning("Method not implemented in Phase 2")
        return {"success": False, "message": "Method not implemented in Phase 2"}
    
    async def place_order(self, symbol: str, order_type: str, side: str, 
                   amount: float, price: Optional[float] = None) -> Dict[str, Any]:
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
            
        response = await self._make_request(
            method=HttpMethod.POST,
            endpoint="/api/v3/order",
            params=params,
            signed=True
        )
        self.logger.debug(f"Order response: {response}")
        return self.normalizer.normalize_order(response)
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        binance_symbol = self._format_symbol(symbol)
        response = await self._make_request(
            method=HttpMethod.DELETE,
            endpoint="/api/v3/order",
            params={"orderId": order_id, "symbol": binance_symbol},
            signed=True
        )
        self.logger.debug(f"Cancel order response: {response}")
        return self.normalizer.normalize_order(response)
    
    async def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        binance_symbol = self._format_symbol(symbol)
        response = await self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v3/order",
            params={"orderId": order_id, "symbol": binance_symbol},
            signed=True
        )
        self.logger.debug(f"Get order response: {response}")
        return self.normalizer.normalize_order(symbol, response)

    async def _make_request(self, method: HttpMethod, endpoint: str, params: Optional[Dict] = None, 
                     headers: Optional[Dict] = None, signed: bool = False) -> Dict[str, Any]:
        """
        Override base _make_request to use different base URLs for public/private endpoints
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' or call initialize()")
            
        async with self.request_semaphore:  # Rate limiting
            await self._handle_rate_limit()
            
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
            if signed and self.api_key and self.api_secret:
                if params is None:
                    params = {}
                    
                # Add timestamp parameter required by Binance
                params['timestamp'] = str(int(time.time() * 1000))
                
                # Add recvWindow parameter for better reliability (optional)
                params['recvWindow'] = '5000'
                
                # Create the query string without the signature
                query_string = urlencode(params)
                
                # Create signature
                signature = hmac.new(
                    self.api_secret.encode('utf-8'),
                    query_string.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                # Add the signature to the parameters
                params['signature'] = signature
                
                # Set headers with API key
                headers = {
                    'X-MBX-APIKEY': self.api_key
                }
                
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



