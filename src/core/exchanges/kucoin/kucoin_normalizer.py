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
        #TODO Implement
        pass
        
    def normalize_trading_fees(self, raw_response: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        #TODO Implement
        pass
        
    def normalize_order(self, symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        #TODO Implement
        pass