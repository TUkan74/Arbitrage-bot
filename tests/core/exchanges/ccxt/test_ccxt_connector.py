import pytest
from unittest.mock import patch, MagicMock
from core.exchanges.ccxt import CcxtExchange
from core.enums import HttpMethod

@pytest.fixture
def ccxt_exchange():
    with patch('ccxt.binance'):
        exchange = CcxtExchange('binance')
        exchange.exchange = MagicMock()
        yield exchange

def test_initialization():
    """Test that the CCXT connector initializes correctly with various parameters"""
    with patch('ccxt.binance') as mock_binance:
        # Test with minimal parameters
        exchange = CcxtExchange('binance')
        mock_binance.assert_called_once()
        
        # Reset mock for the next test
        mock_binance.reset_mock()
        
        # Test with API credentials
        exchange = CcxtExchange('binance', api_key='test_key', api_secret='test_secret')
        mock_binance.assert_called_once_with({
            'apiKey': 'test_key',
            'secret': 'test_secret',
            'timeout': 30000,
            'enableRateLimit': True,
        })
        
        # Reset mock for the next test
        mock_binance.reset_mock()
        
        # Test with additional parameters like KuCoin password
        exchange = CcxtExchange('binance', 
                           api_key='test_key', 
                           api_secret='test_secret',
                           password='test_pass')
        mock_binance.assert_called_once_with({
            'apiKey': 'test_key',
            'secret': 'test_secret',
            'timeout': 30000,
            'enableRateLimit': True,
            'password': 'test_pass'
        })

def test_get_exchange_info(ccxt_exchange):
    """Test getting exchange info with mocked CCXT response"""
    # Mock the CCXT load_markets method
    mock_markets = {
        'BTC/USDT': {
            'active': True,
            'base': 'BTC',
            'quote': 'USDT',
            'precision': {'price': 2, 'amount': 5},
            'limits': {'price': {'min': 0.01}, 'amount': {'min': 0.001}}
        }
    }
    ccxt_exchange.exchange.load_markets.return_value = mock_markets
    
    result = ccxt_exchange.get_exchange_info()
    
    assert result['exchange'] == 'BINANCE'
    assert len(result['symbols']) == 1
    assert result['symbols'][0]['symbol'] == 'BTC/USDT'
    assert result['symbols'][0]['base_asset'] == 'BTC'
    assert result['symbols'][0]['quote_asset'] == 'USDT'
    assert result['symbols'][0]['status'] == 'TRADING'

def test_get_ticker(ccxt_exchange):
    """Test getting ticker data with mocked CCXT response"""
    mock_ticker = {
        'symbol': 'BTC/USDT',
        'last': 50000.0,
        'bid': 49990.0,
        'ask': 50010.0,
        'baseVolume': 100.0,
        'high': 51000.0,
        'low': 49000.0,
        'timestamp': 1234567890000
    }
    ccxt_exchange.exchange.fetch_ticker.return_value = mock_ticker
    
    result = ccxt_exchange.get_ticker('BTC/USDT')
    
    assert result['symbol'] == 'BTC/USDT'
    assert result['last_price'] == 50000.0
    assert result['bid'] == 49990.0
    assert result['ask'] == 50010.0
    assert result['volume'] == 100.0
    assert result['high'] == 51000.0
    assert result['low'] == 49000.0
    assert result['timestamp'] == 1234567890000

def test_get_order_book(ccxt_exchange):
    """Test getting order book with mocked CCXT response"""
    mock_order_book = {
        'bids': [[49990.0, 1.0], [49980.0, 2.0]],
        'asks': [[50010.0, 1.0], [50020.0, 2.0]],
        'timestamp': 1234567890000
    }
    ccxt_exchange.exchange.fetch_order_book.return_value = mock_order_book
    
    result = ccxt_exchange.get_order_book('BTC/USDT')
    
    assert result['symbol'] == 'BTC/USDT'
    assert result['bids'] == [[49990.0, 1.0], [49980.0, 2.0]]
    assert result['asks'] == [[50010.0, 1.0], [50020.0, 2.0]]
    assert result['timestamp'] == 1234567890000

def test_get_balance(ccxt_exchange):
    """Test getting balance with mocked CCXT response"""
    mock_balance = {
        'free': {'BTC': 1.0, 'USDT': 50000.0},
        'used': {'BTC': 0.5, 'USDT': 10000.0},
        'total': {'BTC': 1.5, 'USDT': 60000.0}
    }
    ccxt_exchange.exchange.fetch_balance.return_value = mock_balance
    
    result = ccxt_exchange.get_balance()
    
    assert 'BTC' in result
    assert 'USDT' in result
    assert result['BTC']['free'] == 1.0
    assert result['BTC']['locked'] == 0.5
    assert result['BTC']['total'] == 1.5
    assert result['USDT']['free'] == 50000.0
    assert result['USDT']['locked'] == 10000.0
    assert result['USDT']['total'] == 60000.0

def test_get_trading_fees(ccxt_exchange):
    """Test getting trading fees with mocked CCXT response"""
    # Test global fees
    mock_fees_global = {
        'maker': 0.001,
        'taker': 0.002
    }
    ccxt_exchange.exchange.fetch_trading_fees.return_value = mock_fees_global
    
    result = ccxt_exchange.get_trading_fees()
    
    assert 'BTC/USDT' in result
    assert 'ETH/USDT' in result
    assert result['BTC/USDT']['maker'] == 0.001
    assert result['BTC/USDT']['taker'] == 0.002
    
    # Test per-symbol fees
    mock_fees_symbol = {
        'maker': 0.0005,
        'taker': 0.001
    }
    ccxt_exchange.exchange.fetch_trading_fee.return_value = mock_fees_symbol
    
    result = ccxt_exchange.get_trading_fees('BTC/USDT')
    
    assert 'BTC/USDT' in result
    assert result['BTC/USDT']['maker'] == 0.0005
    assert result['BTC/USDT']['taker'] == 0.001 