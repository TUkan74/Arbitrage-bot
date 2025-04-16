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

from ..abstract import BaseExchange
from ...enums import HttpMethod
from .kucoin_normalizer import KucoinNormalizer

class Kucoin(BaseExchange):
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, **kwargs):
        super().__init__(exchange_name="KUCOIN")
        self.normalizer = KucoinNormalizer()
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = kwargs.get('passphrase')
    
    @property
    def base_url(self) -> str:
        return "https://api.kucoin.com"
    
    def _format_symbol(self, symbol: str) -> str:
        if '/' in symbol:
            return symbol.replace('/','-')
        else:
            self.logger.error("Incorrect format of symbol pair")
            raise Exception("Incorrect format of symbol pair")
    
    def get_exchange_info(self) -> Dict[str, Any]:
        
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v1/symbols"
        )
        self.logger.debug(f"Raw KuCoin exchange info response: {response}")
        
        return self.normalizer.normalize_exchange_info(response)

    def get_ticker(self,symbol : str) -> Dict[str,Any]:

        kucoin_symbol = self._format_symbol(symbol)
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v1/market/orderbook/level1",
            params={"symbol": kucoin_symbol}
        )
        self.logger.debug(f"Raw Kucoin ticker response: {response}")
        
        data = response.get("data", {})
        
        return self.normalizer.normalize_ticker(symbol, data)

    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        kucoin_symbol = self._format_symbol(symbol)
        response = self._make_request(
            method=HttpMethod.GET,
            endpoint=f"/api/v1/market/orderbook/level2_{limit}",
            params={"symbol": kucoin_symbol}
        )
        self.logger.debug(f"Raw Kucoin order book response")

        return self.normalizer.normalize_order_book(symbol,response)

    def get_balance(self) -> Dict[str, float]:
        #TODO Implement
        pass

    def get_trading_fees(self, symbol: str | None = None) -> Dict[str, float]:
        #TODO Implement
        pass

    def transfer(self, currency: str, amount: float, from_account: str, to_account: str) -> Dict[str, Any]:
        #TODO Implement
        pass

    def place_order(self, symbol: str, order_type: str, side: str, amount: float, price: float | None = None) -> Dict[str, Any]:
        #TODO Implement
        pass

    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        #TODO Implement
        pass

    def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        #TODO Implement
        pass

    

