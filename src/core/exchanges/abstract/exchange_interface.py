from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import aiohttp


class ExchangeInterface(ABC):
    """
    Abstract base class defining the interface for all exchange connectors.
    All custom connectors (Binance, KuCoin) and the CCXT wrapper must implement 
    these methods to provide a consistent API.
    """
    
    @abstractmethod
    async def __aenter__(self):
        """Async context manager entry"""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass
    
    @abstractmethod
    async def initialize(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, **kwargs):
        """
        Initialize the exchange connector with credentials
        
        Args:
            api_key: API key for the exchange
            api_secret: API secret for the exchange
            **kwargs: Additional parameters specific to exchanges (like passphrase for KuCoin)
        """
        pass
    
    #
    # Market Data Methods
    #
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current ticker data for a trading pair
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            
        Returns:
            Dict containing ticker data including:
                - last_price: Last traded price
                - bid: Highest buy order price
                - ask: Lowest sell order price
                - volume: 24h trading volume
                - timestamp: Ticker timestamp
        """
        pass
    
    @abstractmethod
    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get order book data for a trading pair
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            limit: Number of orders to retrieve on each side
            
        Returns:
            Dict containing:
                - bids: List of [price, amount] pairs for buy orders
                - asks: List of [price, amount] pairs for sell orders
                - timestamp: Order book timestamp
        """
        pass
    
    @abstractmethod
    async def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information and trading rules
        
        Returns:
            Dict containing exchange information including:
                - supported symbols
                - trading limits
                - rate limits
                - fees
        """
        pass
    
    #
    # Trading Methods
    #
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, float]:
        """
        Get account balances
        
        Returns:
            Dict mapping asset symbols to available balances
        """
        pass
    
    @abstractmethod
    async def get_trading_fees(self, symbol: Optional[str] = None) -> Dict[str, float]:
        """
        Get trading fees for a symbol or all symbols
        
        Args:
            symbol: Trading pair symbol or None for all
            
        Returns:
            Dict mapping symbols to their fee rates (maker and taker)
        """
        pass
    
    @abstractmethod
    async def place_order(self, symbol: str, order_type: str, side: str, 
                   amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        """
        Place a new order on the exchange
        
        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            order_type: Type of order ('limit', 'market')
            side: Order side ('buy', 'sell')
            amount: Quantity to trade
            price: Price for limit orders (None for market orders)
            
        Returns:
            Dict containing order details including:
                - id: Order ID
                - status: Order status
                - filled: Amount filled
                - remaining: Amount remaining
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Cancel an existing order
        
        Args:
            order_id: ID of the order to cancel
            symbol: Trading pair symbol for the order
            
        Returns:
            Dict containing cancellation confirmation
        """
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Get the status of an order
        
        Args:
            order_id: ID of the order to check
            symbol: Trading pair symbol for the order
            
        Returns:
            Dict containing order details
        """
        pass
    
    #
    # Advanced Methods
    #
    
    @abstractmethod
    async def transfer(self, currency: str, amount: float, from_account: str, 
                to_account: str) -> Dict[str, Any]:
        """
        Transfer funds between accounts within the same exchange
        
        Args:
            currency: Currency to transfer
            amount: Amount to transfer
            from_account: Source account ('spot', 'margin', etc.)
            to_account: Destination account ('spot', 'margin', etc.)
            
        Returns:
            Dict containing transfer confirmation
        """
        pass
    
    @abstractmethod
    async def withdraw(self, currency: str, amount: float, address: str, **params) -> Dict[str, Any]:
        """
        Withdraw funds from the exchange
        
        Args:
            currency: Currency to withdraw
            amount: Amount to withdraw
            address: Destination address
            **params: Additional parameters (tag, memo, etc.)
            
        Returns:
            Dict containing withdrawal details including transaction ID
        """
        pass

