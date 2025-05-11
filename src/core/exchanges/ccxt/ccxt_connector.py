from typing import Dict, List, Optional, Any
import time
import ccxt
from ..abstract import BaseExchange
from ...enums import HttpMethod
from .ccxt_normalizer import CcxtNormalizer

class CcxtExchange(BaseExchange):
    """
    CCXT-based exchange connector that implements the ExchangeInterface.
    This wrapper allows using any exchange supported by the CCXT library.
    """
    
    def __init__(self, exchange_id: str, **kwargs):
        """
        Initialize a CCXT-based exchange connector.
        
        Args:
            exchange_id: ID of the exchange in CCXT (e.g., 'binance', 'huobi', 'bitget')
            **kwargs: Additional parameters to pass to the CCXT exchange
        """
        super().__init__(exchange_name=exchange_id.upper())
        
        # Store exchange ID
        self.exchange_id = exchange_id.lower()
        
        # Override API credentials from kwargs if provided
        api_key = kwargs.pop('api_key', self.api_key)
        api_secret = kwargs.pop('api_secret', self.api_secret)
        
        # Initialize CCXT exchange
        exchange_class = getattr(ccxt, self.exchange_id)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'timeout': 30000,
            'enableRateLimit': True,
            **kwargs
        })
        
        # Create normalizer
        self.normalizer = CcxtNormalizer()
        
        self.logger.info(f"Initialized CCXT connector for {exchange_id}")
    
    @property
    def base_url(self) -> str:
        """Get the base URL from CCXT"""
        return self.exchange.urls.get('api', '')
    
    def _create_signature(self, method: HttpMethod, endpoint: str, query_string: str, timestamp: str) -> str:
        """
        Not needed for CCXT as it handles signatures internally
        """
        return ""
    
    def _get_signed_headers(self, method: HttpMethod, endpoint: str, params: Optional[Dict] = None) -> Dict[str, str]:
        """
        Not needed for CCXT as it handles authentication internally
        """
        return {}
    
    def _format_symbol(self, symbol: str) -> str:
        """
        Convert symbol to CCXT format if needed
        """
        return symbol
    
    def _make_request(self, method: HttpMethod, endpoint: str, params: Optional[Dict] = None, 
                     headers: Optional[Dict] = None, signed: bool = False) -> Dict[str, Any]:
        """
        Not used directly as we use CCXT methods instead
        """
        raise NotImplementedError("CCXT connector uses CCXT methods directly, not _make_request")
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information including symbols, limits, etc.
        """
        try:
            markets = self.exchange.load_markets(True)  # Force reload
            return self.normalizer.normalize_exchange_info(self.exchange_id, markets)
        except Exception as e:
            self.logger.error(f"Error getting exchange info: {str(e)}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get ticker information for a symbol
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return self.normalizer.normalize_ticker(symbol, ticker)
        except Exception as e:
            self.logger.error(f"Error getting ticker for {symbol}: {str(e)}")
            raise
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get order book for a symbol
        """
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit)
            return self.normalizer.normalize_order_book(symbol, order_book)
        except Exception as e:
            self.logger.error(f"Error getting order book for {symbol}: {str(e)}")
            raise
    
    def get_balance(self) -> Dict[str, float]:
        """
        Get account balance
        """
        try:
            balance = self.exchange.fetch_balance()
            return self.normalizer.normalize_balance(balance)
        except Exception as e:
            self.logger.error(f"Error getting balance: {str(e)}")
            raise
    
    def get_trading_fees(self, symbol: Optional[str] = None) -> Dict[str, float]:
        """
        Get trading fees (if supported by the exchange)
        """
        try:
            if symbol:
                # Some exchanges support fetching fees for a specific symbol
                try:
                    fee = self.exchange.fetch_trading_fee(symbol)
                    return self.normalizer.normalize_trading_fees({symbol: fee})
                except ccxt.NotSupported:
                    # Fallback to default fees from markets
                    market = self.exchange.market(symbol)
                    return self.normalizer.normalize_trading_fees({symbol: {
                        'maker': market.get('maker', 0.001),
                        'taker': market.get('taker', 0.001)
                    }})
            else:
                # Try to fetch all trading fees
                try:
                    fees = self.exchange.fetch_trading_fees()
                    return self.normalizer.normalize_trading_fees(fees)
                except ccxt.NotSupported:
                    # Fallback to default fees from markets
                    markets = self.exchange.markets
                    fees = {}
                    for symbol, market in markets.items():
                        fees[symbol] = {
                            'maker': market.get('maker', 0.001),
                            'taker': market.get('taker', 0.001)
                        }
                    return self.normalizer.normalize_trading_fees(fees)
        except Exception as e:
            self.logger.error(f"Error getting trading fees for {symbol if symbol else 'all symbols'}: {str(e)}")
            # Return default fees to allow operation to continue
            default_fee = {"maker": 0.001, "taker": 0.001}
            return {symbol: default_fee} if symbol else {"BTC/USDT": default_fee, "ETH/USDT": default_fee}
    
    def place_order(self, symbol: str, order_type: str, side: str, 
                   amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        """
        Place an order
        """
        try:
            # Map order types
            if order_type.lower() == 'limit' and price:
                ccxt_order = self.exchange.create_limit_order(symbol, side.lower(), amount, price)
            elif order_type.lower() == 'market':
                ccxt_order = self.exchange.create_market_order(symbol, side.lower(), amount)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
                
            return self.normalizer.normalize_order(symbol, ccxt_order)
        except Exception as e:
            self.logger.error(f"Error placing {order_type} {side} order for {symbol}: {str(e)}")
            raise
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Cancel an order
        """
        try:
            ccxt_order = self.exchange.cancel_order(order_id, symbol)
            return self.normalizer.normalize_order(symbol, ccxt_order)
        except Exception as e:
            self.logger.error(f"Error canceling order {order_id} for {symbol}: {str(e)}")
            raise
    
    def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Get order status
        """
        try:
            ccxt_order = self.exchange.fetch_order(order_id, symbol)
            return self.normalizer.normalize_order(symbol, ccxt_order)
        except Exception as e:
            self.logger.error(f"Error getting order {order_id} for {symbol}: {str(e)}")
            raise
    
    def transfer(self, currency: str, amount: float, from_account: str, to_account: str) -> Dict[str, Any]:
        """
        Transfer funds between accounts (if supported by the exchange)
        """
        self.logger.warning("CCXT transfer not implemented in Phase 2")
        return {"success": False, "message": "Method not implemented in Phase 2"}
    
    def withdraw(self, currency: str, amount: float, address: str, **params) -> Dict[str, Any]:
        """
        Withdraw funds (if supported by the exchange)
        """
        self.logger.warning("CCXT withdraw not implemented in Phase 2")
        return {"success": False, "message": "Method not implemented in Phase 2"} 