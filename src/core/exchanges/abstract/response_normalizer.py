from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ResponseNormalizer(ABC):
    """Abstract base class for exchange response normalization."""
    
    @abstractmethod
    def normalize_exchange_info(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize exchange information response.
        
        Args:
            raw_response: Raw response from exchange API
            
        Returns:
            Dict containing:
                - exchange: str - Exchange name
                - symbols: List[Dict] - List of trading pairs with:
                    - symbol: str - Trading pair in standard format (e.g., "BTC/USDT")
                    - status: str - Trading status ("TRADING" or "BREAK")
                    - base_asset: str - Base currency
                    - quote_asset: str - Quote currency
                    - min_price: float - Minimum price
                    - min_qty: float - Minimum quantity
                    - price_precision: int - Price decimal places
                    - qty_precision: int - Quantity decimal places
                - rate_limits: List[Dict] - List of rate limits
                - server_time: int - Server timestamp (ms)
        """
        pass
    
    @abstractmethod
    def normalize_ticker(self,symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize ticker response.
        
        Args:
            raw_response: Raw response from exchange API
            symbol: Original symbol format
            
        Returns:
            Dict containing:
                - symbol: str - Trading pair in standard format
                - last_price: float - Last traded price
                - bid: float - Best bid price
                - ask: float - Best ask price
                - volume: float - 24h trading volume
                - high: float - 24h high price
                - low: float - 24h low price
                - timestamp: int - Ticker timestamp (ms)
                - change_24h: float - 24h price change
                - change_percent_24h: float - 24h price change percentage
        """
        pass
    
    @abstractmethod
    def normalize_order_book(self,symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize order book response.
        
        Args:
            raw_response: Raw response from exchange API
            symbol: Original symbol format

        Returns:
            Dict containing:
                - symbol: str - Trading pair in standard format
                - bids: List[List[float]] - List of [price, size] pairs for bids
                - asks: List[List[float]] - List of [price, size] pairs for asks
                - timestamp: int - Order book timestamp (ms)
        """
        pass
    
    @abstractmethod
    def normalize_balance(self, raw_response: Dict[str, Any]) -> Dict[str, float]:
        """
        Normalize balance response.
        
        Args:
            raw_response: Raw response from exchange API
            
        Returns:
            Dict mapping asset symbols to available balances
        """
        pass
    
    @abstractmethod
    def normalize_trading_fees(self, raw_response: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Normalize trading fees response.
        
        Args:
            raw_response: Raw response from exchange API
            
        Returns:
            Dict mapping symbols to fee rates:
                - maker: float - Maker fee rate
                - taker: float - Taker fee rate
        """
        pass
    
    @abstractmethod
    def normalize_order(self,symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize order response.
        
        Args:
            raw_response: Raw response from exchange API
            symbol: Original symbol format
            
        Returns:
            Dict containing:
                - id: str - Order ID
                - symbol: str - Trading pair in standard format
                - status: str - Order status
                - filled: float - Filled quantity
                - remaining: float - Remaining quantity
                - price: float - Order price
                - cost: float - Total cost
                - timestamp: int - Order timestamp (ms)
        """
        pass