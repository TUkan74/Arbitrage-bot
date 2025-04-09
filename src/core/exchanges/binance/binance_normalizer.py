from typing import Dict, Any, List
from ..abstract.response_normalizer import ResponseNormalizer

class BinanceNormalizer(ResponseNormalizer):
    """Normalizer for Binance API responses."""
    
    def normalize_exchange_info(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        # Extract relevant information
        symbols_info = {}
        for symbol_data in raw_response.get('symbols', []):
            symbol = symbol_data.get('symbol', '')
            # Convert Binance format to standard format
            base = symbol_data.get('baseAsset', '')
            quote = symbol_data.get('quoteAsset', '')
            standard_symbol = f"{base}/{quote}"
            
            symbols_info[standard_symbol] = {
                'status': symbol_data.get('status', ''),
                'base_asset': base,
                'quote_asset': quote,
                'min_price': float(symbol_data.get('filters', [{}])[0].get('minPrice', 0)) 
                    if symbol_data.get('filters') else 0,
                'min_qty': float(symbol_data.get('filters', [{}])[1].get('minQty', 0))
                    if len(symbol_data.get('filters', [])) > 1 else 0,
                'base_precision': symbol_data.get('baseAssetPrecision', 8),
                'quote_precision': symbol_data.get('quoteAssetPrecision', 8)
            }
        
        return {
            'name': 'Binance',
            'symbols': symbols_info,
            'rate_limits': raw_response.get('rateLimits', []),
            'server_time': raw_response.get('serverTime', 0)
        }

        
    
    def normalize_ticker(self,symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        # Normalize the response to match our interface
        return {
            "symbol": symbol,  
            "last_price": float(raw_response.get("lastPrice", 0)),
            "bid": float(raw_response.get("bidPrice", 0)),
            "ask": float(raw_response.get("askPrice", 0)),
            "volume": float(raw_response.get("volume", 0)),
            "high": float(raw_response.get("highPrice", 0)),
            "low": float(raw_response.get("lowPrice", 0)),
            "timestamp": raw_response.get("closeTime", 0),
            "change_24h": float(raw_response.get("priceChange", 0)),
            "change_percent_24h": float(raw_response.get("priceChangePercent", 0))
        }
        
        
    
    def normalize_order_book(self,symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "bids": [[float(price), float(qty)] for price, qty in raw_response.get("bids", [])],
            "asks": [[float(price), float(qty)] for price, qty in raw_response.get("asks", [])],
            "timestamp": raw_response.get("lastUpdateId", 0)
        }
        
    def normalize_balance(self, raw_response: Dict[str, Any]) -> Dict[str, float]:
        """
        Normalize balance response.
        
        Args:
            raw_response: Raw response from Binance API
            
        Returns:
            Dict mapping asset symbols to available balances
        """
        balances = {}
        for balance in raw_response.get('balances', []):
            asset = balance.get('asset', '')
            free = float(balance.get('free', 0))
            if free > 0:
                balances[asset] = free
        return balances
        
    def normalize_trading_fees(self, raw_response: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Normalize trading fees response.
        
        Args:
            raw_response: Raw response from Binance API
            
        Returns:
            Dict mapping symbols to fee rates
        """
        fees = {}
        for fee_info in raw_response:
            symbol = fee_info.get('symbol', '')
            # Convert Binance format to standard format
            for quote in ['USDT', 'BTC', 'ETH', 'BNB', 'USD', 'EUR', 'GBP']:
                if symbol.endswith(quote):
                    base = symbol[:-len(quote)]
                    standard_symbol = f"{base}/{quote}"
                    break
            else:
                standard_symbol = symbol
                
            fees[standard_symbol] = {
                'maker': float(fee_info.get('makerCommission', 0)),
                'taker': float(fee_info.get('takerCommission', 0))
            }
        return fees
        
    def normalize_order(self, symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize order response.
        
        Args:
            symbol: Original symbol in standard format
            raw_response: Raw response from Binance API
            
        Returns:
            Dict containing normalized order data
        """
        return {
            'id': str(raw_response.get('orderId', '')),
            'symbol': symbol,  # Keep original symbol format
            'status': raw_response.get('status', ''),
            'filled': float(raw_response.get('executedQty', 0)),
            'remaining': float(raw_response.get('origQty', 0)) - float(raw_response.get('executedQty', 0)),
            'price': float(raw_response.get('price', 0)),
            'cost': float(raw_response.get('cummulativeQuoteQty', 0)),
            'timestamp': raw_response.get('time', 0)
        }

