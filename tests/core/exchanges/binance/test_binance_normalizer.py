"""
Tests for the BinanceNormalizer class.
"""

import pytest
from core.exchanges.binance.binance_normalizer import BinanceNormalizer

@pytest.fixture
def normalizer():
    """Create a BinanceNormalizer instance for testing."""
    return BinanceNormalizer()

def test_normalize_exchange_info_valid(normalizer):
    """Test normalizing valid exchange info response."""
    raw_response = {
        'timezone': 'UTC',
        'serverTime': 1625097600000,
        'symbols': [
            {
                'symbol': 'BTCUSDT',
                'status': 'TRADING',
                'baseAsset': 'BTC',
                'quoteAsset': 'USDT',
                'quotePrecision': 8,
                'baseAssetPrecision': 8,
                'filters': [
                    {
                        'filterType': 'PRICE_FILTER',
                        'minPrice': '0.01000000'
                    },
                    {
                        'filterType': 'LOT_SIZE',
                        'minQty': '0.00100000'
                    }
                ]
            },
            {
                'symbol': 'ETHUSDT',
                'status': 'BREAK',  # Should be filtered out
                'baseAsset': 'ETH',
                'quoteAsset': 'USDT'
            }
        ]
    }
    
    result = normalizer.normalize_exchange_info(raw_response)
    
    assert result['exchange'] == 'BINANCE'
    assert result['server_time'] == 1625097600000
    assert len(result['symbols']) == 1  # Only TRADING symbols
    
    symbol = result['symbols'][0]
    assert symbol['symbol'] == 'BTC/USDT'
    assert symbol['status'] == 'TRADING'
    assert symbol['base_asset'] == 'BTC'
    assert symbol['quote_asset'] == 'USDT'
    assert symbol['min_price'] == 0.01
    assert symbol['min_qty'] == 0.001
    assert symbol['price_precision'] == 8
    assert symbol['qty_precision'] == 8


def test_normalize_ticker_valid(normalizer):
    """Test normalizing valid ticker response."""
    raw_response = {
        'symbol': 'BTCUSDT',
        'lastPrice': '50000.00',
        'bidPrice': '49990.00',
        'askPrice': '50010.00',
        'volume': '1000.00',
        'highPrice': '51000.00',
        'lowPrice': '49000.00',
        'closeTime': 1625097600000,
        'priceChange': '-1000.00',
        'priceChangePercent': '-2.00'
    }
    
    result = normalizer.normalize_ticker('BTC/USDT', raw_response)
    
    assert result['symbol'] == 'BTC/USDT'
    assert result['last_price'] == 50000.00
    assert result['bid'] == 49990.00
    assert result['ask'] == 50010.00
    assert result['volume'] == 1000.00
    assert result['high'] == 51000.00
    assert result['low'] == 49000.00
    assert result['timestamp'] == 1625097600000
    assert result['change_24h'] == -1000.00
    assert result['change_percent_24h'] == -2.00

def test_normalize_ticker_missing_fields(normalizer):
    """Test normalizing ticker response with missing fields."""
    raw_response = {}
    result = normalizer.normalize_ticker('BTC/USDT', raw_response)
    
    assert result['symbol'] == 'BTC/USDT'
    assert result['last_price'] == 0
    assert result['bid'] == 0
    assert result['ask'] == 0
    assert result['volume'] == 0
    assert result['high'] == 0
    assert result['low'] == 0
    assert result['timestamp'] == 0
    assert result['change_24h'] == 0
    assert result['change_percent_24h'] == 0

def test_normalize_order_book_valid(normalizer):
    """Test normalizing valid order book response."""
    raw_response = {
        'lastUpdateId': 1234567890,
        'bids': [
            ['50000.00', '1.00'],
            ['49990.00', '2.00']
        ],
        'asks': [
            ['50010.00', '1.00'],
            ['50020.00', '2.00']
        ]
    }
    
    result = normalizer.normalize_order_book('BTC/USDT', raw_response)
    
    assert result['symbol'] == 'BTC/USDT'
    assert result['timestamp'] == 1234567890
    assert len(result['bids']) == 2
    assert len(result['asks']) == 2
    assert result['bids'][0] == [50000.00, 1.00]
    assert result['asks'][0] == [50010.00, 1.00]

def test_normalize_order_book_invalid(normalizer):
    """Test normalizing invalid order book response."""
    # Test with None
    result = normalizer.normalize_order_book('BTC/USDT', None)
    assert result['symbol'] == 'BTC/USDT'
    assert result['bids'] == []
    assert result['asks'] == []
    assert result['timestamp'] == 0
    
    # Test with invalid bid/ask format
    raw_response = {
        'bids': [['invalid']],
        'asks': [['invalid']]
    }
    result = normalizer.normalize_order_book('BTC/USDT', raw_response)
    assert result['bids'] == []
    assert result['asks'] == []

def test_normalize_balance_valid(normalizer):
    """Test normalizing valid balance response."""
    raw_response = {
        'balances': [
            {
                'asset': 'BTC',
                'free': '1.00',
                'locked': '0.50'
            },
            {
                'asset': 'USDT',
                'free': '1000.00',
                'locked': '500.00'
            },
            {
                'asset': 'ETH',
                'free': '0',
                'locked': '0'
            }
        ]
    }
    
    result = normalizer.normalize_balance(raw_response)
    
    assert len(result) == 2  # ETH should be filtered out (zero balance)
    assert result['BTC']['free'] == 1.00
    assert result['BTC']['locked'] == 0.50
    assert result['BTC']['total'] == 1.50
    assert result['USDT']['free'] == 1000.00
    assert result['USDT']['locked'] == 500.00
    assert result['USDT']['total'] == 1500.00

def test_normalize_balance_invalid(normalizer):
    """Test normalizing invalid balance response."""
    # Test with empty response
    result = normalizer.normalize_balance({})
    assert result == {}
    
    # Test with invalid balance format
    raw_response = {
        'balances': [
            {'asset': 'BTC'}  # Missing free/locked
        ]
    }
    result = normalizer.normalize_balance(raw_response)
    assert result == {}

def test_normalize_trading_fees_list_response(normalizer):
    """Test normalizing trading fees from list response."""
    raw_response = [
        {
            'symbol': 'BTCUSDT',
            'makerCommission': '0.001',
            'takerCommission': '0.001'
        },
        {
            'symbol': 'ETHUSDT',
            'makerCommission': '0.001',
            'takerCommission': '0.001'
        }
    ]
    
    result = normalizer.normalize_trading_fees(raw_response)
    
    assert 'BTC/USDT' in result
    assert 'ETH/USDT' in result
    assert result['BTC/USDT']['maker'] == 0.001
    assert result['BTC/USDT']['taker'] == 0.001

def test_normalize_trading_fees_object_response(normalizer):
    """Test normalizing trading fees from object response."""
    raw_response = {
        'data': [
            {
                'symbol': 'BTCUSDT',
                'makerCommission': '0.001',
                'takerCommission': '0.001'
            }
        ]
    }
    
    result = normalizer.normalize_trading_fees(raw_response)
    
    assert 'BTC/USDT' in result
    assert result['BTC/USDT']['maker'] == 0.001
    assert result['BTC/USDT']['taker'] == 0.001

def test_normalize_trading_fees_invalid(normalizer):
    """Test normalizing invalid trading fees response."""
    # Test with invalid response
    result = normalizer.normalize_trading_fees(None)
    assert 'BTC/USDT' in result  # Should return default fees
    assert result['BTC/USDT']['maker'] == 0.001
    assert result['BTC/USDT']['taker'] == 0.001

def test_normalize_order_valid(normalizer):
    """Test normalizing valid order response."""
    raw_response = {
        'orderId': '12345',
        'symbol': 'BTCUSDT',
        'price': '50000.00',
        'origQty': '1.00',
        'executedQty': '0.50',
        'side': 'BUY',
        'type': 'LIMIT',
        'status': 'PARTIALLY_FILLED',
        'time': 1625097600000
    }

    result = normalizer.normalize_order(raw_response)

    assert result['id'] == '12345'
    assert result['symbol'] == 'BTC/USDT'
    assert result['price'] == 50000.00
    assert result['amount'] == 1.00
    assert result['filled'] == 0.50
    assert result['remaining'] == 0.50
    assert result['status'] == 'PARTIALLY_FILLED'
    assert result['side'] == 'BUY'
    assert result['type'] == 'LIMIT'
    assert result['created_at'] == 1625097600000

def test_normalize_order_error(normalizer):
    """Test normalizing error order response."""
    raw_response = {
        'msg': 'Invalid order'
    }

    result = normalizer.normalize_order(raw_response)

    assert result == {}  # Should return empty dict for error responses 