from typing import Dict, Any, List
from ..abstract.response_normalizer import ResponseNormalizer

class KucoinNormalizer(ResponseNormalizer):
    """Normalizer for KuCoin API responses."""
    
    def normalize_exchange_info(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        symbols = []
        for symbol_info in raw_response.get('data', []):
            if symbol_info.get('enableTrading'):
                # Convert KuCoin format (BTC-USDT) to standard format (BTC/USDT)
                base = symbol_info['baseCurrency']
                quote = symbol_info['quoteCurrency']
                symbol = f"{base}/{quote}"
                
                symbols.append({
                    'symbol': symbol,
                    'status': 'TRADING' if symbol_info['enableTrading'] else 'HALT',
                    'base_asset': base,
                    'quote_asset': quote,
                    'min_price': float(symbol_info.get('priceIncrement', 0)),
                    'min_qty': float(symbol_info.get('baseMinSize', 0)),
                    'price_precision': len(str(symbol_info.get('priceIncrement', '1')).split('.')[-1]),
                    'qty_precision': len(str(symbol_info.get('baseIncrement', '1')).split('.')[-1])
                })
                
        return {
            'exchange': 'KUCOIN',
            'symbols': symbols,
            'rate_limits': [
                {
                    'rateLimitType': 'REQUEST_WEIGHT',
                    'interval': 'MINUTE',
                    'intervalNum': 1,
                    'limit': 60
                },
                {
                    'rateLimitType': 'ORDERS',
                    'interval': 'SECOND',
                    'intervalNum': 1,
                    'limit': 10
                }
            ],
            'server_time': raw_response.get('time')
        }
        
    def normalize_ticker(self, symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        data = raw_response.get('data', {})
        return {
            'symbol': symbol,  # Keep original symbol format
            'last_price': float(data.get('price', 0)),
            'bid': float(data.get('bestBid', 0)),
            'ask': float(data.get('bestAsk', 0)),
            'volume': float(data.get('size', 0)),
            'high': float(data.get('high', 0)),
            'low': float(data.get('low', 0)),
            'timestamp': data.get('time', 0),
        }
        
    def normalize_order_book(self, symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        data = raw_response.get('data', {})
        return {
            'symbol': symbol,  # Keep original symbol format
            'bids': [[float(price), float(size)] for price, size in data.get('bids', [])],
            'asks': [[float(price), float(size)] for price, size in data.get('asks', [])],
            'timestamp': data.get('time', 0)
        }
        
    def normalize_balance(self, raw_response: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Normalize balance response from KuCoin API.
        
        Args:
            raw_response: Raw API response
            
        Returns:
            Dict with currency as key and balance details as value
        """
        result = {}
        data = raw_response.get('data', [])
        
        # Handle both list and single account responses
        if isinstance(data, dict):
            data = [data]
            
        for account in data:
            currency = account['currency']
            result[currency] = {
                'free': float(account['available']),
                'locked': float(account['holds']),
                'total': float(account['balance'])
            }
        
        return result
        
    def normalize_trading_fees(self, raw_response: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Normalize trading fees response from KuCoin API.

        Args:
            raw_response: Raw API response containing trading fees data

        Returns:
            Dict containing normalized trading fees data
        """
        result = {}
        data = raw_response.get('data', {})
        
        # Handle single symbol response
        if isinstance(data, dict):
            symbol = data.get('symbol', '').replace('-', '/')
            if symbol:
                result[symbol] = {
                    'maker': float(data.get('makerFeeRate', 0.001)),
                    'taker': float(data.get('takerFeeRate', 0.001))
                }
        # Handle multiple symbols response
        elif isinstance(data, list):
            for fee_info in data:
                symbol = fee_info.get('symbol', '').replace('-', '/')
                if symbol:
                    result[symbol] = {
                        'maker': float(fee_info.get('makerFeeRate', 0.001)),
                        'taker': float(fee_info.get('takerFeeRate', 0.001))
                    }
        
        return result
        
    def normalize_order(self, symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize order responses from different KuCoin API endpoints.
        Handles responses from place_order, cancel_order, and get_order operations.
        
        Args:
            symbol: Trading pair symbol
            raw_response: Raw API response
            
        Returns:
            Normalized order information
        """
        data = raw_response.get('data', {})
        
        # Handle place_order response
        if 'orderId' in data:
            order_id = data['orderId']
            return {
                "id": order_id,
                "status": "SUBMITTED"
            }
        
        # Handle cancel_order response
        if 'cancelledOrderIds' in data:
            order_id = data['cancelledOrderIds'][0] if data['cancelledOrderIds'] else None
            return {
                "id": order_id,
                "status": "CANCELED"
            }
        
        # Handle get_order response (most detailed)
        order = {
            "id": data.get('id'),
            "symbol": data.get('symbol', symbol.replace('/', '-')),
            "type": data.get('type', None),
            "side": data.get('side', None),
            "price": float(data.get('price', 0)),
            "amount": float(data.get('size', 0)),
            "filled": float(data.get('dealSize', 0)),
            "remaining": float(data.get('remainSize', 0)),
            "status": data.get('status', None),
            "fee": float(data.get('fee', 0)),
            "fee_currency": data.get('feeCurrency', None),
            "created_at": data.get('createdAt', None)
        }
        
        # Calculate filled percentage
        if order['amount'] > 0:
            order['filled_percent'] = (order['filled'] / order['amount']) * 100
        else:
            order['filled_percent'] = 0
            
        return order
    
    def normalize_account_id(self, raw_response: Dict[str, Any]) -> str:
        """
        Extract account ID from KuCoin API response.
        
        Args:
            raw_response: Raw API response
            
        Returns:
            Account ID string
        """
        data = raw_response.get('data', [])
        if not data:
            raise ValueError("No account data found in response")
            
        # Find the first trading account
        for account in data:
            if account.get('type') == 'trade':
                return account['id']
                
        # If no trading account found, return the first account ID
        return data[0]['id']