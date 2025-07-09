"""
Tests for the CCXT exchange connector.
"""

import pytest
import ccxt
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from core.exchanges.ccxt.ccxt_connector import CcxtExchange
from core.enums import HttpMethod

@pytest.fixture
def mock_ccxt():
    """Create a mock CCXT exchange."""
    mock_exchange = MagicMock()
    mock_exchange.urls = {'api': 'https://api.mock-exchange.com'}
    
    # Mock basic market data
    mock_exchange.markets = {
        'BTC/USDT': {
            'id': 'BTCUSDT',
            'symbol': 'BTC/USDT',
            'base': 'BTC',
            'quote': 'USDT',
            'active': True,
            'precision': {'price': 2, 'amount': 6},
            'limits': {
                'amount': {'min': 0.0001, 'max': 1000},
                'price': {'min': 0.01}
            },
            'maker': 0.001,
            'taker': 0.001
        },
        'ETH/USDT': {
            'id': 'ETHUSDT',
            'symbol': 'ETH/USDT',
            'base': 'ETH',
            'quote': 'USDT',
            'active': True,
            'precision': {'price': 2, 'amount': 6},
            'limits': {
                'amount': {'min': 0.001, 'max': 5000},
                'price': {'min': 0.01}
            },
            'maker': 0.001,
            'taker': 0.001
        }
    }
    
    # Mock load_markets
    mock_exchange.load_markets = MagicMock(return_value=mock_exchange.markets)
    
    # Mock fetch_ticker
    mock_exchange.fetch_ticker = MagicMock(return_value={
        'symbol': 'BTC/USDT',
        'timestamp': int(datetime.now().timestamp() * 1000),
        'datetime': datetime.now().isoformat(),
        'high': 50000.0,
        'low': 49000.0,
        'bid': 49500.0,
        'ask': 49600.0,
        'last': 49550.0,
        'close': 49550.0,
        'baseVolume': 1000.0,
        'quoteVolume': 49550000.0,
        'info': {}
    })
    
    # Mock fetch_order_book
    mock_exchange.fetch_order_book = MagicMock(return_value={
        'symbol': 'BTC/USDT',
        'timestamp': int(datetime.now().timestamp() * 1000),
        'datetime': datetime.now().isoformat(),
        'bids': [[49500.0, 1.0], [49450.0, 2.0]],
        'asks': [[49600.0, 1.0], [49650.0, 2.0]],
        'info': {}
    })
    
    # Mock fetch_balance
    mock_exchange.fetch_balance = MagicMock(return_value={
        'total': {
            'BTC': 1.1,
            'USDT': 55000.0
        },
        'free': {
            'BTC': 1.0,
            'USDT': 50000.0
        },
        'used': {
            'BTC': 0.1,
            'USDT': 5000.0
        },
        'info': {}
    })
    
    # Mock trading fees methods
    mock_exchange.fetch_trading_fees = MagicMock(return_value={
        'maker': 0.001,
        'taker': 0.001
    })
    
    mock_exchange.fetch_trading_fee = MagicMock(return_value={
        'maker': 0.001,
        'taker': 0.001
    })
    
    # Mock order methods
    mock_exchange.create_limit_order = MagicMock(return_value={
        'id': '12345',
        'symbol': 'BTC/USDT',
        'type': 'limit',
        'side': 'buy',
        'price': 49500.0,
        'amount': 1.0,
        'filled': 0.0,
        'status': 'NEW',
        'timestamp': int(datetime.now().timestamp() * 1000),
        'info': {}
    })
    
    mock_exchange.create_market_order = MagicMock(return_value={
        'id': '12346',
        'symbol': 'BTC/USDT',
        'type': 'market',
        'side': 'sell',
        'amount': 1.0,
        'filled': 1.0,
        'status': 'FILLED',
        'timestamp': int(datetime.now().timestamp() * 1000),
        'info': {}
    })
    
    mock_exchange.cancel_order = MagicMock(return_value={
        'id': '12345',
        'symbol': 'BTC/USDT',
        'type': 'limit',
        'side': 'buy',
        'price': 49500.0,
        'amount': 1.0,
        'filled': 0.0,
        'status': 'CANCELED',
        'timestamp': int(datetime.now().timestamp() * 1000),
        'info': {}
    })
    
    mock_exchange.fetch_order = MagicMock(return_value={
        'id': '12345',
        'symbol': 'BTC/USDT',
        'type': 'limit',
        'side': 'buy',
        'price': 49500.0,
        'amount': 1.0,
        'filled': 0.5,
        'status': 'PARTIALLY_FILLED',
        'timestamp': int(datetime.now().timestamp() * 1000),
        'info': {}
    })
    
    return mock_exchange

@pytest.fixture
def exchange(mock_ccxt):
    """Create a CCXT exchange instance with mocked CCXT."""
    with patch('ccxt.binance', return_value=mock_ccxt):
        exchange = CcxtExchange('binance')
        exchange.api_key = 'test_key'
        exchange.api_secret = 'test_secret'
        return exchange

def test_initialization(exchange):
    """Test exchange initialization."""
    assert exchange.exchange_id == 'binance'
    assert exchange.api_key == 'test_key'
    assert exchange.api_secret == 'test_secret'
    assert exchange.base_url == 'https://api.mock-exchange.com'

def test_format_symbol(exchange):
    """Test symbol formatting."""
    assert exchange._format_symbol('BTC/USDT') == 'BTC/USDT'

def test_create_signature(exchange):
    """Test signature creation (not used in CCXT)."""
    signature = exchange._create_signature(
        method=HttpMethod.GET,
        endpoint='/api/v3/order',
        query_string='symbol=BTCUSDT',
        timestamp='1625097600000'
    )
    assert signature == ''

def test_get_signed_headers(exchange):
    """Test getting signed headers (not used in CCXT)."""
    headers = exchange._get_signed_headers(
        method=HttpMethod.GET,
        endpoint='/api/v3/order'
    )
    assert headers == {}

def test_make_request_not_implemented(exchange):
    """Test that _make_request raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        exchange._make_request(
            method=HttpMethod.GET,
            endpoint='/api/v3/order'
        )

@pytest.mark.asyncio
async def test_get_exchange_info(exchange):
    """Test getting exchange information."""
    info = exchange.get_exchange_info()
    assert info['exchange'] == 'BINANCE'
    assert len(info['symbols']) == 2
    btc_symbol = next(s for s in info['symbols'] if s['base_asset'] == 'BTC')
    assert btc_symbol['symbol'] == 'BTC/USDT'
    assert btc_symbol['status'] == 'TRADING'

@pytest.mark.asyncio
async def test_get_ticker(exchange):
    """Test getting ticker information."""
    ticker = exchange.get_ticker('BTC/USDT')
    assert ticker['symbol'] == 'BTC/USDT'
    assert ticker['last_price'] == 49550.0
    assert ticker['volume'] == 1000.0

@pytest.mark.asyncio
async def test_get_order_book(exchange):
    """Test getting order book."""
    order_book = exchange.get_order_book('BTC/USDT', limit=10)
    assert order_book['symbol'] == 'BTC/USDT'
    assert len(order_book['bids']) == 2
    assert len(order_book['asks']) == 2
    assert order_book['bids'][0] == [49500.0, 1.0]

@pytest.mark.asyncio
async def test_get_balance(exchange):
    """Test getting account balance."""
    balance = exchange.get_balance()
    assert 'BTC' in balance
    assert 'USDT' in balance
    assert balance['BTC']['free'] == 1.0
    assert balance['BTC']['locked'] == 0.1
    assert balance['BTC']['total'] == 1.1

@pytest.mark.asyncio
async def test_get_trading_fees_all(exchange):
    """Test getting all trading fees."""
    fees = exchange.get_trading_fees()
    assert 'BTC/USDT' in fees
    assert fees['BTC/USDT']['maker'] == 0.001
    assert fees['BTC/USDT']['taker'] == 0.001

@pytest.mark.asyncio
async def test_get_trading_fees_symbol(exchange):
    """Test getting trading fees for a specific symbol."""
    fees = exchange.get_trading_fees('BTC/USDT')
    assert 'BTC/USDT' in fees
    assert fees['BTC/USDT']['maker'] == 0.001
    assert fees['BTC/USDT']['taker'] == 0.001

@pytest.mark.asyncio
async def test_get_trading_fees_not_supported(exchange, mock_ccxt):
    """Test getting trading fees when not supported."""
    # Make fetch_trading_fees raise NotSupported
    mock_ccxt.fetch_trading_fees.side_effect = ccxt.NotSupported()
    mock_ccxt.fetch_trading_fee.side_effect = ccxt.NotSupported()
    
    # Mock market data with proper fee structure
    mock_ccxt.market = MagicMock(return_value={
        'maker': 0.001,
        'taker': 0.001
    })
    
    fees = exchange.get_trading_fees('BTC/USDT')
    assert 'BTC/USDT' in fees
    assert fees['BTC/USDT']['maker'] == 0.001  # Default fee
    assert fees['BTC/USDT']['taker'] == 0.001  # Default fee
    
    # Test getting all fees when not supported
    fees = exchange.get_trading_fees()
    assert 'BTC/USDT' in fees
    assert 'ETH/USDT' in fees
    assert fees['BTC/USDT']['maker'] == 0.001
    assert fees['BTC/USDT']['taker'] == 0.001

@pytest.mark.asyncio
async def test_place_limit_order(exchange):
    """Test placing a limit order."""
    order = exchange.place_order(
        symbol='BTC/USDT',
        order_type='limit',
        side='buy',
        amount=1.0,
        price=49500.0
    )
    assert order['id'] == '12345'
    assert order['status'] == 'NEW'
    assert order['type'] == 'limit'

@pytest.mark.asyncio
async def test_place_market_order(exchange):
    """Test placing a market order."""
    order = exchange.place_order(
        symbol='BTC/USDT',
        order_type='market',
        side='sell',
        amount=1.0
    )
    assert order['id'] == '12346'
    assert order['status'] == 'FILLED'
    assert order['type'] == 'market'

@pytest.mark.asyncio
async def test_place_order_invalid_type(exchange):
    """Test placing an order with invalid type."""
    with pytest.raises(ValueError, match="Unsupported order type"):
        exchange.place_order(
            symbol='BTC/USDT',
            order_type='invalid',
            side='buy',
            amount=1.0
        )

@pytest.mark.asyncio
async def test_cancel_order(exchange):
    """Test canceling an order."""
    order = exchange.cancel_order('12345', 'BTC/USDT')
    assert order['id'] == '12345'
    assert order['status'] == 'CANCELED'

@pytest.mark.asyncio
async def test_get_order(exchange):
    """Test getting order status."""
    order = exchange.get_order('12345', 'BTC/USDT')
    assert order['id'] == '12345'
    assert order['status'] == 'PARTIALLY_FILLED'
    assert order['filled_percent'] > 0

@pytest.mark.asyncio
async def test_error_handling(exchange, mock_ccxt):
    """Test error handling in various methods."""
    # Test get_exchange_info error
    mock_ccxt.load_markets.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        exchange.get_exchange_info()
    
    # Test get_ticker error
    mock_ccxt.fetch_ticker.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        exchange.get_ticker('BTC/USDT')
    
    # Test get_order_book error
    mock_ccxt.fetch_order_book.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        exchange.get_order_book('BTC/USDT')
    
    # Test get_balance error
    mock_ccxt.fetch_balance.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        exchange.get_balance()
    
    # Test place_order error
    mock_ccxt.create_limit_order.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        exchange.place_order('BTC/USDT', 'limit', 'buy', 1.0, 50000.0)
    
    # Test cancel_order error
    mock_ccxt.cancel_order.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        exchange.cancel_order('12345', 'BTC/USDT')
    
    # Test get_order error
    mock_ccxt.fetch_order.side_effect = Exception("API error")
    with pytest.raises(Exception, match="API error"):
        exchange.get_order('12345', 'BTC/USDT') 