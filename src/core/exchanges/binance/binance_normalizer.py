from typing import Dict, Any, List, Optional
from ..abstract.response_normalizer import ResponseNormalizer

class BinanceNormalizer(ResponseNormalizer):
    """Normalizer for Binance API responses."""
    
    def normalize_exchange_info(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize exchange info from Binance API response.
        
        Args:
            raw_response: Raw API response from Binance
            
        Returns:
            Normalized exchange info
        """
        # Ensure we're working with a dictionary
        if not isinstance(raw_response, dict):
            self.logger.error(f"Invalid exchange_info format: {type(raw_response)}")
            raw_response = {}  # Use empty dict if response is invalid
            
        symbols = []
        for symbol_info in raw_response.get('symbols', []):
            # Only include TRADING symbols
            if symbol_info.get('status') == 'TRADING':
                # Convert Binance format (BTCUSDT) to standard format (BTC/USDT)
                base = symbol_info.get('baseAsset', '')
                quote = symbol_info.get('quoteAsset', '')
                
                if base and quote:
                    symbol = f"{base}/{quote}"
                    
                    # Extract min price and min qty from filters if available
                    min_price = 0
                    min_qty = 0
                    
                    filters = symbol_info.get('filters', [])
                    for f in filters:
                        if f.get('filterType') == 'PRICE_FILTER':
                            min_price = float(f.get('minPrice', 0))
                        elif f.get('filterType') == 'LOT_SIZE':
                            min_qty = float(f.get('minQty', 0))
                    
                    # Extract precision from symbol info
                    price_precision = symbol_info.get('quotePrecision', 0)
                    qty_precision = symbol_info.get('baseAssetPrecision', 0)
                    
                    symbols.append({
                        'symbol': symbol,
                        'status': 'TRADING',
                        'base_asset': base,
                        'quote_asset': quote,
                        'min_price': min_price,
                        'min_qty': min_qty,
                        'price_precision': price_precision,
                        'qty_precision': qty_precision
                    })
        
        return {
            'exchange': 'BINANCE',
            'symbols': symbols,
            'server_time': raw_response.get('serverTime', 0)
        }
        
    def normalize_ticker(self, symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize ticker data from Binance API response.
        
        Args:
            symbol: Trading pair symbol
            raw_response: Raw API response from Binance
            
        Returns:
            Normalized ticker data in standard format
        """
        return {
            'symbol': symbol,
            'last_price': float(raw_response.get('lastPrice', 0)),
            'bid': float(raw_response.get('bidPrice', 0)),
            'ask': float(raw_response.get('askPrice', 0)),
            'volume': float(raw_response.get('volume', 0)),
            'high': float(raw_response.get('highPrice', 0)),
            'low': float(raw_response.get('lowPrice', 0)),
            'timestamp': raw_response.get('closeTime', 0),
            'change_24h': float(raw_response.get('priceChange', 0)),
            'change_percent_24h': float(raw_response.get('priceChangePercent', 0))
        }
        

    def normalize_order_book(self, symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize order book data from Binance API response.
        
        Args:
            symbol: Trading pair symbol
            raw_response: Raw API response from Binance
            
        Returns:
            Normalized order book data
        """
        # Check if we have a valid response
        if not raw_response or not isinstance(raw_response, dict):
            return {
                'symbol': symbol,
                'bids': [],
                'asks': [],
                'timestamp': 0
            }
            
        # Convert string values to floats
        bids = []
        for bid in raw_response.get('bids', []):
            if len(bid) >= 2:
                bids.append([float(bid[0]), float(bid[1])])
                
        asks = []
        for ask in raw_response.get('asks', []):
            if len(ask) >= 2:
                asks.append([float(ask[0]), float(ask[1])])
        
        return {
            'symbol': symbol,
            'bids': bids,
            'asks': asks,
            'timestamp': raw_response.get('lastUpdateId', 0)  # Binance uses lastUpdateId
        }
        
    def normalize_balance(self, raw_response: Dict[str, Any]) -> Dict[str, float]:
        """
        Normalize balance data from Binance API response.
        
        Args:
            raw_response: Raw API response from Binance
            
        Returns:
            Normalized balance data
        """
        balances = {}
        
        for balance in raw_response.get('balances', []):
            asset = balance.get('asset')
            free = float(balance.get('free', 0))
            locked = float(balance.get('locked', 0))
            
            if asset and (free > 0 or locked > 0):
                balances[asset] = {
                    'free': free,
                    'locked': locked,
                    'total': free + locked
                }
                
        return balances
        
    def normalize_trading_fees(self, raw_response: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Normalize trading fees from Binance API response.
        
        Args:
            raw_response: Raw API response from Binance
            
        Returns:
            Normalized trading fees data
        """
        fees = {}
        
        # Handle response as list of fee objects
        if isinstance(raw_response, list):
            for symbol_fee in raw_response:
                symbol = symbol_fee.get('symbol', '')
                if not symbol:
                    continue
                    
                # Convert Binance format (BTCUSDT) to standard format (BTC/USDT)
                # Try to identify base and quote from common patterns
                if len(symbol) >= 6:  # Most pairs are at least 6 chars
                    for quote in ['USDT', 'BUSD', 'USDC', 'BTC', 'ETH', 'BNB']:
                        if symbol.endswith(quote):
                            base = symbol[:-len(quote)]
                            standard_symbol = f"{base}/{quote}"
                            
                            fees[standard_symbol] = {
                                'maker': float(symbol_fee.get('makerCommission', 0.001)),
                                'taker': float(symbol_fee.get('takerCommission', 0.001))
                            }
                            break
        # Handle response as object with data array
        elif isinstance(raw_response, dict):
            fee_data = raw_response.get('data', [])
            if isinstance(fee_data, list):
                for symbol_fee in fee_data:
                    symbol = symbol_fee.get('symbol', '')
                    if not symbol:
                        continue
                        
                    # Convert Binance format (BTCUSDT) to standard format (BTC/USDT)
                    # Try to identify base and quote from common patterns
                    if len(symbol) >= 6:  # Most pairs are at least 6 chars
                        for quote in ['USDT', 'BUSD', 'USDC', 'BTC', 'ETH', 'BNB']:
                            if symbol.endswith(quote):
                                base = symbol[:-len(quote)]
                                standard_symbol = f"{base}/{quote}"
                                
                                fees[standard_symbol] = {
                                    'maker': float(symbol_fee.get('makerCommission', 0.001)),
                                    'taker': float(symbol_fee.get('takerCommission', 0.001))
                                }
                                break
        
        # If no fees were found, return default fees for common pairs
        if not fees:
            default_fee = {'maker': 0.001, 'taker': 0.001}
            fees = {
                'BTC/USDT': default_fee,
                'ETH/USDT': default_fee
            }
            
        return fees
        
    def normalize_order(self, symbol: str, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize order data from Binance API response.
        
        Args:
            symbol: Trading pair symbol
            raw_response: Raw API response from Binance
            
        Returns:
            Normalized order data
        """
        order_id = raw_response.get('orderId')
        if not order_id:
            # For error responses or incomplete data
            return {
                'id': None,
                'symbol': symbol,
                'status': 'FAILED',
                'error': raw_response.get('msg', 'Unknown error')
            }
            
        return {
            'id': str(order_id),
            'symbol': symbol,
            'price': float(raw_response.get('price', 0)),
            'quantity': float(raw_response.get('origQty', 0)),
            'executed_qty': float(raw_response.get('executedQty', 0)),
            'side': raw_response.get('side', '').lower(),
            'type': raw_response.get('type', '').lower(),
            'status': raw_response.get('status', 'UNKNOWN'),
            'time': raw_response.get('time', 0),
            'filled_percent': (float(raw_response.get('executedQty', 0)) / 
                             float(raw_response.get('origQty', 1))) * 100
        }

