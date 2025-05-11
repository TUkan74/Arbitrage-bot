from typing import Dict, Any, List
import time
from ..abstract.response_normalizer import ResponseNormalizer

class CcxtNormalizer(ResponseNormalizer):
    """
    Normalizer for CCXT API responses to convert them to our standard format.
    """
    
    def normalize_exchange_info(self, exchange_id: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize exchange info from CCXT
        
        Args:
            exchange_id: Exchange ID
            raw_response: Raw CCXT markets data
            
        Returns:
            Normalized exchange info in standard format
        """
        symbols = []
        
        for symbol, market in raw_response.items():
            if market.get('active', False):
                base = market.get('base', '')
                quote = market.get('quote', '')
                
                # Some exchanges use different symbol formats
                standard_symbol = f"{base}/{quote}"
                
                # Extract precision and limits
                price_precision = market.get('precision', {}).get('price', 0)
                if isinstance(price_precision, int):
                    price_precision_value = price_precision
                else:
                    # Handle string or float representations
                    price_precision_value = len(str(price_precision).split('.')[-1]) if '.' in str(price_precision) else 0
                
                # Extract amount precision
                amount_precision = market.get('precision', {}).get('amount', 0)
                if isinstance(amount_precision, int):
                    amount_precision_value = amount_precision
                else:
                    amount_precision_value = len(str(amount_precision).split('.')[-1]) if '.' in str(amount_precision) else 0
                
                # Extract limits
                min_price = market.get('limits', {}).get('price', {}).get('min', 0)
                min_amount = market.get('limits', {}).get('amount', {}).get('min', 0)
                
                symbols.append({
                    'symbol': standard_symbol,
                    'status': 'TRADING' if market.get('active', False) else 'HALT',
                    'base_asset': base,
                    'quote_asset': quote,
                    'min_price': float(min_price) if min_price else 0,
                    'min_qty': float(min_amount) if min_amount else 0,
                    'price_precision': price_precision_value,
                    'qty_precision': amount_precision_value
                })
        
        # Extract rate limits if available
        rate_limits = []
        if hasattr(raw_response, 'rateLimit'):
            rate_limits.append({
                'rateLimitType': 'REQUEST_WEIGHT',
                'interval': 'MINUTE',
                'intervalNum': 1,
                'limit': 60000 / raw_response.rateLimit  # Convert milliseconds to requests per minute
            })
        
        return {
            'exchange': exchange_id.upper(),
            'symbols': symbols,
            'rate_limits': rate_limits,
            'server_time': int(time.time() * 1000)
        }
    
    def normalize_ticker(self, symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize ticker data from CCXT
        
        Args:
            symbol: Symbol in standard format
            raw_response: Raw CCXT ticker data
            
        Returns:
            Normalized ticker data in standard format
        """
        return {
            'symbol': symbol,
            'last_price': float(raw_response.get('last', 0)),
            'bid': float(raw_response.get('bid', 0)),
            'ask': float(raw_response.get('ask', 0)),
            'volume': float(raw_response.get('baseVolume', 0)),
            'high': float(raw_response.get('high', 0)),
            'low': float(raw_response.get('low', 0)),
            'timestamp': raw_response.get('timestamp', 0)
        }
    
    def normalize_order_book(self, symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize order book data from CCXT
        
        Args:
            symbol: Symbol in standard format
            raw_response: Raw CCXT order book data
            
        Returns:
            Normalized order book data in standard format
        """
        # CCXT already returns bids and asks as arrays of [price, amount]
        return {
            'symbol': symbol,
            'bids': raw_response.get('bids', []),
            'asks': raw_response.get('asks', []),
            'timestamp': raw_response.get('timestamp', 0)
        }
    
    def normalize_balance(self, raw_response: Dict[str, Any]) -> Dict[str, float]:
        """
        Normalize balance data from CCXT
        
        Args:
            raw_response: Raw CCXT balance data
            
        Returns:
            Normalized balance data mapping currencies to amounts
        """
        result = {}
        
        # CCXT returns balances in 'free', 'used', and 'total' fields per currency
        for currency, balance in raw_response.get('total', {}).items():
            if balance > 0:
                result[currency] = {
                    'free': float(raw_response.get('free', {}).get(currency, 0)),
                    'locked': float(raw_response.get('used', {}).get(currency, 0)),
                    'total': float(balance)
                }
        
        return result
    
    def normalize_trading_fees(self, raw_response: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Normalize trading fees from CCXT
        
        Args:
            raw_response: Raw CCXT trading fees data
            
        Returns:
            Normalized trading fees mapping symbols to maker/taker rates
        """
        result = {}
        
        # Handle both formats:
        # 1. {symbol: {maker: X, taker: Y}}
        # 2. {maker: X, taker: Y} (global fees)
        
        if 'maker' in raw_response and 'taker' in raw_response:
            # Global fees, apply to all symbols
            maker = float(raw_response.get('maker', 0.001))
            taker = float(raw_response.get('taker', 0.001))
            
            # Add default fees for common pairs
            result['BTC/USDT'] = {'maker': maker, 'taker': taker}
            result['ETH/USDT'] = {'maker': maker, 'taker': taker}
        else:
            # Per-symbol fees
            for symbol, fees in raw_response.items():
                if isinstance(fees, dict) and 'maker' in fees and 'taker' in fees:
                    result[symbol] = {
                        'maker': float(fees.get('maker', 0.001)),
                        'taker': float(fees.get('taker', 0.001))
                    }
        
        return result
    
    def normalize_order(self, symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize order data from CCXT
        
        Args:
            symbol: Symbol in standard format
            raw_response: Raw CCXT order data
            
        Returns:
            Normalized order data in standard format
        """
        # Handle both full order objects and simplified responses
        order_id = raw_response.get('id')
        
        if not order_id:
            # Some exchanges just return a string order ID or a simplified response
            if isinstance(raw_response, str):
                return {
                    'id': raw_response,
                    'symbol': symbol,
                    'status': 'SUBMITTED'
                }
            elif 'orderId' in raw_response:
                return {
                    'id': raw_response['orderId'],
                    'symbol': symbol,
                    'status': 'SUBMITTED'
                }
        
        # Full order object
        return {
            'id': str(order_id),
            'symbol': symbol,
            'price': float(raw_response.get('price', 0)),
            'quantity': float(raw_response.get('amount', 0)),
            'executed_qty': float(raw_response.get('filled', 0)),
            'side': raw_response.get('side', '').lower(),
            'type': raw_response.get('type', '').lower(),
            'status': self._map_order_status(raw_response.get('status', '')),
            'time': raw_response.get('timestamp', 0),
            'filled_percent': (float(raw_response.get('filled', 0)) / 
                             float(raw_response.get('amount', 1))) * 100 if raw_response.get('amount') else 0
        }
    
    def _map_order_status(self, ccxt_status: str) -> str:
        """
        Map CCXT order status to our standard status
        
        Args:
            ccxt_status: CCXT status string
            
        Returns:
            Standardized status string
        """
        status_map = {
            'open': 'NEW',
            'closed': 'FILLED',
            'canceled': 'CANCELED',
            'expired': 'EXPIRED',
            'rejected': 'REJECTED',
            'failed': 'REJECTED'
        }
        
        return status_map.get(ccxt_status.lower(), ccxt_status.upper()) 