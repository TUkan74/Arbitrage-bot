from typing import Any, Dict, Optional
from ..abstract.base_exchange import BaseExchange
from ...enums import HttpMethod
import hmac
import hashlib
import aiohttp
from urllib.parse import urlencode
import base64
import time
import logging
import json
import asyncio

from ..abstract import BaseExchange
from ...enums import HttpMethod
from .kucoin_normalizer import KucoinNormalizer

class KucoinExchange(BaseExchange):
    """KuCoin exchange implementation."""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, 
                 api_passphrase: Optional[str] = None, **kwargs):
                 
        super().__init__(exchange_name="KUCOIN")
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.normalizer = KucoinNormalizer()
        
        # Sign the passphrase if credentials are provided
        if api_passphrase and api_secret:
            self.api_passphrase = self._sign_passphrase(api_passphrase)
    
    @property
    def base_url(self) -> str:
        return "https://api.kucoin.com"
        
    def _sign_passphrase(self, passphrase: str) -> str:
        """
        Sign the API passphrase using HMAC-SHA256.
        
        Args:
            passphrase: The API passphrase to sign
            
        Returns:
            Base64 encoded signature
        """
        return base64.b64encode(
            hmac.new(
                self.api_secret.encode('utf-8'),
                passphrase.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()
        
    async def _create_signature(self, method: HttpMethod, endpoint: str, query_string: str, timestamp: str) -> str:
        """
        Create signature for KuCoin API requests.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            query_string: Query parameters as string
            timestamp: Current timestamp
            
        Returns:
            Base64 encoded signature
        """
        # For GET/DELETE requests, include query params in the signature
        if method in [HttpMethod.GET, HttpMethod.DELETE] and query_string:
            endpoint = f"{endpoint}?{query_string}"
            
        # Create the string to sign
        str_to_sign = f"{timestamp}{method.value}{endpoint}"
        
        # Sign with HMAC-SHA256
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            str_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode()
        
    async def _get_signed_headers(self, method: HttpMethod, endpoint: str, params: Optional[Dict] = None) -> Dict[str, str]:
        timestamp = str(int(time.time() * 1000))
        
        # Create query string for GET/DELETE requests
        query_string = ""
        if method in [HttpMethod.GET, HttpMethod.DELETE] and params:
            query_string = urlencode(params)
            
        # Create signature
        signature = await self._create_signature(method, endpoint, query_string, timestamp)
        
        return {
            "KC-API-KEY": self.api_key,
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": timestamp,
            "KC-API-PASSPHRASE": self.api_passphrase,
            "KC-API-KEY-VERSION": "2",
            "Content-Type": "application/json"
        }
    
    def _format_symbol(self, symbol: str) -> str:
        return symbol.replace('/', '-')
        
    async def _make_request(self, method: HttpMethod, endpoint: str, params: Optional[Dict] = None, 
                     headers: Optional[Dict] = None, signed: bool = False) -> Dict[str, Any]:
        """
        Make a request to the KuCoin API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            headers: Request headers
            signed: Whether to sign the request
            
        Returns:
            Dict containing the API response
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' or call initialize()")
            
        async with self.request_semaphore:  # Rate limiting
            await self._handle_rate_limit()
            
            # Prepare URL
            url = f"{self.base_url}{endpoint}"
            
            # Prepare headers
            if signed and self.api_key and self.api_secret:
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
        
    async def get_exchange_info(self) -> Dict[str, Any]:
        
        response = await self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v1/symbols"
        )
        return self.normalizer.normalize_exchange_info(response)

    async def get_ticker(self,symbol : str) -> Dict[str,Any]:

        kucoin_symbol = self._format_symbol(symbol)
        response = await self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v1/market/orderbook/level1",
            params={"symbol": kucoin_symbol}
        )
        return self.normalizer.normalize_ticker(symbol, response)
        
    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        kucoin_symbol = self._format_symbol(symbol)
        response = await self._make_request(
            method=HttpMethod.GET,
            endpoint=f"/api/v1/market/orderbook/level2_{limit}",
            params={"symbol": kucoin_symbol}
        )
        return self.normalizer.normalize_order_book(symbol, response)
        
    async def get_balance(self, account_id: Optional[str] = None,currency: Optional[str] = None) -> Dict[str, float]:
        if account_id:
            response = await self._make_request(
                method=HttpMethod.GET,
                endpoint=f"/api/v1/accounts/{account_id}",
                params={"currency": currency if currency else None}
                )
        else:
            response = await self._make_request(
                method=HttpMethod.GET,
                endpoint="/api/v1/accounts",
                params={"currency": currency if currency else None}
                )
        return self.normalizer.normalize_balance(response)

    async def get_account_id(self) -> str:
        response = await self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v1/accounts"
            )
        return self.normalizer.normalize_account_id(response)
    
    async def get_trading_fees(self, symbol: Optional[str] = None) -> Dict[str, float]:
        """
        Get trading fees for a symbol or all symbols.
        
        Args:
            symbol: Optional trading pair symbol
            
        Returns:
            Dict containing trading fees
        """
        # Check if we have valid API credentials before attempting the call
        if not self.api_key or not self.api_secret or not self.api_passphrase:
            self.logger.warning("Cannot fetch trading fees: missing API credentials")
            # Return default fees to allow operation to continue
            default_fee = {"maker": 0.001, "taker": 0.001}
            return {symbol: default_fee} if symbol else {"BTC/USDT": default_fee, "ETH/USDT": default_fee}
            
        try:
            if symbol:
                kucoin_symbol = self._format_symbol(symbol)
                response = await self._make_request(
                    method=HttpMethod.GET,
                    endpoint="/api/v1/trade-fees",
                    params={"symbols": kucoin_symbol},
                    signed=True
                )
            else:
                response = await self._make_request(
                    method=HttpMethod.GET,
                    endpoint="/api/v1/trade-fees",
                    signed=True
                )
                
            if isinstance(response, str):
                response = json.loads(response)
                
            if "data" in response:
                data = response["data"]
                # Handle single object response
                if isinstance(data, dict):
                    data = [data]
                # Handle list response
                if isinstance(data, list):
                    result = {}
                    for fee_info in data:
                        if isinstance(fee_info, dict):
                            symbol = fee_info.get("symbol", "").replace("-", "/")
                            if symbol:
                                result[symbol] = {
                                    "maker": float(fee_info.get("makerFeeRate", 0.001)),
                                    "taker": float(fee_info.get("takerFeeRate", 0.001))
                                }
                    return result
                    
            self.logger.error(f"Unexpected response format: {response}")
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting trading fees: {str(e)}")
            return {}

    async def transfer(self, currency: str, amount: float, from_account: str, to_account: str) -> Dict[str, Any]:
        #TODO Implement Not right now, to be implemented in phase 3
        pass

    async def place_order(self, symbol: str, order_type: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        kucoin_symbol = self._format_symbol(symbol)
        
        # Base parameters for all order types
        params = {
            "clientOid": str(int(time.time() * 1000)),  # Generate unique client order ID
            "symbol": kucoin_symbol,
            "type": order_type.lower(),
            "side": side.lower()
        }
        
        # Handle limit orders
        if order_type.lower() == "limit":
            if not price:
                raise ValueError("Price is required for limit orders")
                
            params.update({
                "price": str(price),
                "size": str(amount),
                "timeInForce": "GTC"  # Good Till Cancelled
            })
            
        # Handle market orders
        else:
            # For market orders, we can specify either size or funds
            # Here we use size by default, but you could add a parameter to choose
            params["size"] = str(amount)
            
        response = await self._make_request(
            method=HttpMethod.POST,
            endpoint="/api/v1/hf/orders",
            params=params,
            signed=True
        )
        
        return self.normalizer.normalize_order(symbol, response)

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        response = await self._make_request(
            method=HttpMethod.DELETE,
            endpoint=f"/api/v1/hf/orders/{order_id}",
            signed=True
        )
        return self.normalizer.normalize_order(symbol, response)
        
    async def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        response = await self._make_request(
            method=HttpMethod.GET,
            endpoint=f"/api/v1/hf/orders/{order_id}",
            signed=True
        )
        return self.normalizer.normalize_order(symbol, response)

    async def withdraw(self, currency: str, amount: float, address: str, **params) -> Dict[str, Any]:
        self.logger.warning("Method withdraw() not implemented in Phase 2")
        return {"success": False, "message": "Method not implemented in Phase 2"}

    

