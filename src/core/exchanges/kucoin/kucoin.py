from typing import Any, Dict, Optional
from ..abstract.base_exchange import BaseExchange
from ...enums import HttpMethod
import hmac
import hashlib
import requests
from urllib.parse import urlencode
import base64
import time
import logging
import json

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
        
    def _create_signature(self, method: HttpMethod, endpoint: str, query_string: str, timestamp: str) -> str:
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
        
    def _get_signed_headers(self, method: HttpMethod, endpoint: str, params: Optional[Dict] = None) -> Dict[str, str]:
        timestamp = str(int(time.time() * 1000))
        
        # Create query string for GET/DELETE requests
        query_string = ""
        if method in [HttpMethod.GET, HttpMethod.DELETE] and params:
            query_string = urlencode(params)
            
        # Create signature
        signature = self._create_signature(method, endpoint, query_string, timestamp)
        
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
        
    def _make_request(self, method: HttpMethod, endpoint: str, params: Optional[Dict] = None, 
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
        self._handle_rate_limit()
        
        # Prepare URL
        url = f"{self.base_url}{endpoint}"
        
        # Prepare headers
        if signed and self.api_key and self.api_secret:
            headers = self._get_signed_headers(method, endpoint, params)
            
        # Handle GET/DELETE requests
        if method in [HttpMethod.GET, HttpMethod.DELETE]:
            if params:
                url = f"{url}?{urlencode(params)}"
            response = requests.request(method.value, url, headers=headers)
            
        # Handle POST requests
        else:
            data = json.dumps(params) if params else None
            response = requests.request(method.value, url, headers=headers, data=data)
            
        self._handle_error(response)
        return response.json()
        
    def get_exchange_info(self) -> Dict[str, Any]:
        
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v1/symbols"
        )
        return self.normalizer.normalize_exchange_info(response)

    def get_ticker(self,symbol : str) -> Dict[str,Any]:

        kucoin_symbol = self._format_symbol(symbol)
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v1/market/orderbook/level1",
            params={"symbol": kucoin_symbol}
        )
        return self.normalizer.normalize_ticker(symbol, response)
        
        

    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        kucoin_symbol = self._format_symbol(symbol)
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint=f"/api/v1/market/orderbook/level2_{limit}",
            params={"symbol": kucoin_symbol}
        )
        return self.normalizer.normalize_order_book(symbol, response)
        
    def get_balance(self, account_id: Optional[str] = None,currency: Optional[str] = None) -> Dict[str, float]:
        if account_id:
            response = self._make_request(
                method=HttpMethod.GET,
                endpoint=f"/api/v1/accounts/{account_id}",
                params={"currency": currency if currency else None}
                )
        else:
            response = self._make_request(
                method=HttpMethod.GET,
                endpoint="/api/v1/accounts",
                params={"currency": currency if currency else None}
                )
        return self.normalizer.normalize_balance(response)

    def get_account_id(self) -> str:
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v1/accounts"
            )
        return self.normalizer.normalize_account_id(response)
    
    def get_trading_fees(self, symbol: Optional[str] = None) -> Dict[str, float]:
        """
        Get trading fees for a symbol or multiple symbols
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT") or None
            
        Returns:
            Dict containing fee rates for maker and taker for the requested symbol(s)
        """
        # Check if we have valid API credentials before attempting the call
        if not self.api_key or not self.api_secret or not self.api_passphrase:
            self.logger.warning("Cannot fetch trading fees: missing API credentials")
            # Return default fees to allow operation to continue
            default_fee = {"maker": 0.001, "taker": 0.001}
            return {symbol: default_fee} if symbol else {"BTC/USDT": default_fee, "ETH/USDT": default_fee}
            
        if symbol:
            kucoin_symbol = self._format_symbol(symbol)
            params = {"symbols": kucoin_symbol}
            
            response = self._make_request(
                method=HttpMethod.GET,
                endpoint="/api/v1/trade-fees",
                params=params,
                signed=True
            )
            
            result = {}
            for fee_info in response.get("data", []):
                std_symbol = fee_info["symbol"].replace("-", "/")
                result[std_symbol] = {
                    "maker": float(fee_info["makerFeeRate"]),
                    "taker": float(fee_info["takerFeeRate"])
                }
                
            return result
        
        else:
            # Get all trading fees
            exchange_info = self.get_exchange_info()
            all_symbols = []
            
            for symbol_info in exchange_info.get("symbols", []):
                if symbol_info.get("status") == "TRADING":  
                    all_symbols.append(symbol_info["symbol"].replace("/", "-"))
            
            if not all_symbols:
                return {}  
            
            result = {}
            
            # Process fewer symbols at a time to avoid API rate limits and errors
            symbol_batches = [all_symbols[i:i+5] for i in range(0, len(all_symbols), 5)]
            
            for batch in symbol_batches:
                params = {"symbols": ",".join(batch)}
                
                try:
                    response = self._make_request(
                        method=HttpMethod.GET,
                        endpoint="/api/v1/trade-fees",
                        params=params,
                        signed=True
                    )
                    
                    for fee_info in response.get("data", []):
                        std_symbol = fee_info["symbol"].replace("-", "/")
                        result[std_symbol] = {
                            "maker": float(fee_info["makerFeeRate"]),
                            "taker": float(fee_info["takerFeeRate"])
                        }
                    
                    self._handle_rate_limit()
                    # Add a small delay between batches to avoid rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"Error fetching fees for batch: {e}")
            
            return result

    def transfer(self, currency: str, amount: float, from_account: str, to_account: str) -> Dict[str, Any]:
        #TODO Implement Not right now, to be implemented in phase 3
        pass

    def place_order(self, symbol: str, order_type: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
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
            
        response = self._make_request(
            method=HttpMethod.POST,
            endpoint="/api/v1/hf/orders",
            params=params,
            signed=True
        )
        
        return self.normalizer.normalize_order(symbol, response)

    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        response = self._make_request(
            method=HttpMethod.DELETE,
            endpoint=f"/api/v1/hf/orders/{order_id}",
            signed=True
        )
        return self.normalizer.normalize_order(symbol, response)
        
    def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint=f"/api/v1/hf/orders/{order_id}",
            signed=True
        )
        return self.normalizer.normalize_order(symbol, response)

    def withdraw(self, currency: str, amount: float, address: str, **params) -> Dict[str, Any]:
        self.logger.warning("Method withdraw() not implemented in Phase 2")
        return {"success": False, "message": "Method not implemented in Phase 2"}

    

