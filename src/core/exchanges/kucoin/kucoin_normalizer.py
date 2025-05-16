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
        
    def normalize_balance(self, raw_response: Dict[str, Any]) -> Dict[str, float]:
        data = []
        for account in raw_response:
            """
            "id": "5bd6e9286d99522a52e458de", //accountId
            "currency": "BTC", //Currency
            "type": "main", //Account type, including main and trade
            "balance": "237582.04299", //Total assets of a currency
            "available": "237582.032", //Available assets of a currency
            "holds": "0.01099" //Hold assets of a currency
            """
            data.append({
                "id": account['id'],
                "type": account['type'],
                "currency": account['currency'],
                "balance": float(account['balance']),
                "available": float(account['available']),
                "holds": float(account['holds'])
            })
        return data
        
    def normalize_trading_fees(self, raw_response: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        data = []
        for symbol in raw_response:
            data.append({
                "symbol": symbol['symbol'],
                "maker_fee": float(symbol['makerFeeRate']),
                "taker_fee": float(symbol['takerFeeRate'])
            })
        return data     
        
    def normalize_order(self, symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize order responses from different KuCoin API endpoints.
        Handles responses from place_order, cancel_order, and get_order operations.
        
        The response format varies between these operations:
        - place_order: {"data": {"orderId": "..."}}
        - cancel_order: {"data": {"cancelledOrderIds": ["..."]}}
        - get_order: {"data": {"id": "...", "symbol": "...", ... }}
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
        return {
            "id": data.get('id'),
            "clientOid": data.get('clientOid', None),
            "symbol": data.get('symbol', symbol.replace('/', '-')),
            "opType": data.get('opType', None),
            "type": data.get('type', None),
            "side": data.get('side', None),
            "price": float(data.get('price', 0)),
            "size": float(data.get('size', 0)),
            "funds": float(data.get('funds', 0)),
            "dealSize": float(data.get('dealSize', 0)),
            "dealFunds": float(data.get('dealFunds', 0)),
            "remainSize": float(data.get('remainSize', 0)),
            "remainFunds": float(data.get('remainFunds', 0)),
            "cancelledSize": float(data.get('cancelledSize', 0)),
            "cancelledFunds": float(data.get('cancelledFunds', 0)),
            "fee": float(data.get('fee', 0)),
            "feeCurrency": data.get('feeCurrency', None),
            "stp": data.get('stp', None),
            "timeInForce": data.get('timeInForce', None),
            "postOnly": data.get('postOnly', False),
            "hidden": data.get('hidden', False),
            "iceberg": data.get('iceberg', False),
            "visibleSize": data.get('visibleSize', 0),
            "cancelAfter": data.get('cancelAfter', 0),
            "status": data.get('status', None),
        }
    
    def normalize_account_id(self, raw_response: Dict[str, Any]) -> str:
        return raw_response[0]['id']