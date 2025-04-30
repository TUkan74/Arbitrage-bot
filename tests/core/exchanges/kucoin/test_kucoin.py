import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src')))

from core.exchanges.kucoin.kucoin import KucoinExchange
from core.enums import HttpMethod

@pytest.fixture
def kucoin():
    """Create a KucoinExchange instance for testing"""
    return KucoinExchange()

def test_base_url(kucoin):
    """Test that the base URL is correct"""
    assert kucoin.base_url == "https://api.kucoin.com"

def test_format_symbol(kucoin):
    """Test symbol format conversion"""
    # Test standard format to KuCoin format
    assert kucoin._format_symbol("BTC/USDT") == "BTC-USDT"
    
    # Test already formatted symbol (though this shouldn't happen in practice)
    assert kucoin._format_symbol("BTC-USDT") == "BTC-USDT"

def test_get_exchange_info(kucoin):
    """Test getting exchange info"""
    mock_response = {
        "data": [
            {
                "symbol": "BTC-USDT",
                "name": "BTC-USDT",
                "baseCurrency": "BTC",
                "quoteCurrency": "USDT",
                "feeCurrency": "USDT",
                "market": "USDS",
                "baseMinSize": "0.00001",
                "quoteMinSize": "0.01",
                "baseMaxSize": "10000",
                "quoteMaxSize": "100000",
                "baseIncrement": "0.00000001",
                "quoteIncrement": "0.01",
                "priceIncrement": "0.1",
                "priceLimitRate": "0.1",
                "enableTrading": True
            }
        ]
    }
    
    with patch.object(kucoin, '_make_request') as mock_request:
        mock_request.return_value = mock_response
        result = kucoin.get_exchange_info()
        
        assert result["exchange"] == "KUCOIN"
        assert len(result["symbols"]) == 1
        
        symbol_info = result["symbols"][0]
        assert symbol_info["symbol"] == "BTC/USDT"
        assert symbol_info["status"] == "TRADING"
        assert symbol_info["base_asset"] == "BTC"
        assert symbol_info["quote_asset"] == "USDT"
        assert symbol_info["min_price"] == 0.1
        assert symbol_info["min_qty"] == 0.00001
        assert symbol_info["price_precision"] == 1  # From "0.1"
        assert symbol_info["qty_precision"] == 8    # From "0.00000001"

def test_get_ticker(kucoin):
    """Test getting ticker data"""
    mock_response = {
        "data": {
            "sequence": "1550467636704",
            "bestAsk": "0.7100",
            "size": "0.17",
            "price": "0.7000",
            "bestBidSize": "0.1",
            "bestBid": "0.6900",
            "bestAskSize": "0.1",
            "time": 1550653727731,
            "high": "0.7500",
            "low": "0.6500"
        }
    }
    
    with patch.object(kucoin, '_make_request') as mock_request:
        mock_request.return_value = mock_response
        result = kucoin.get_ticker("BTC/USDT")
        
        assert result["symbol"] == "BTC/USDT"
        assert result["last_price"] == 0.7000
        assert result["bid"] == 0.6900
        assert result["ask"] == 0.7100
        assert result["volume"] == 0.17
        assert result["high"] == 0.7500
        assert result["low"] == 0.6500
        assert result["timestamp"] == 1550653727731

def test_get_order_book(kucoin):
    """Test getting order book data"""
    mock_response = {
        "data": {
            "sequence": "3262786978",
            "time": 1550653727731,
            "bids": [["6500.12", "0.45054140"], ["6500.11", "0.45054140"]],
            "asks": [["6500.16", "0.57753524"], ["6500.15", "0.57753524"]]
        }
    }
    
    with patch.object(kucoin, '_make_request') as mock_request:
        mock_request.return_value = mock_response
        result = kucoin.get_order_book("BTC/USDT", limit=20)
        
        assert result["symbol"] == "BTC/USDT"
        assert result["bids"] == [[6500.12, 0.45054140], [6500.11, 0.45054140]]
        assert result["asks"] == [[6500.16, 0.57753524], [6500.15, 0.57753524]]
        assert result["timestamp"] == 1550653727731

def test_place_order(kucoin):
    """Test placing an order"""
    mock_response = {
        "data": {
            "orderId": "5bd6e9286d99522a52e458de"
        }
    }
    
    with patch.object(kucoin, '_make_request') as mock_request:
        mock_request.return_value = mock_response
        
        # Test placing a limit order
        with patch('time.time', return_value=1234567.89):
            result = kucoin.place_order(
                symbol="BTC/USDT",
                order_type="limit",
                side="buy",
                amount=1.0,
                price=50000.0
            )
            
            # Check that the request was made with the correct parameters
            called_args = mock_request.call_args
            assert called_args[1]["method"] == HttpMethod.POST
            assert called_args[1]["endpoint"] == "/api/v1/hf/orders"
            assert called_args[1]["signed"] == True
            
            params = called_args[1]["params"]
            assert params["symbol"] == "BTC-USDT"
            assert params["type"] == "limit"
            assert params["side"] == "buy"
            assert params["size"] == "1.0"
            assert params["price"] == "50000.0"
            assert params["timeInForce"] == "GTC"
            assert params["clientOid"] == "1234567890"  # From mocked time.time()

def test_cancel_order(kucoin):
    """Test canceling an order"""
    mock_response = {
        "data": {
            "cancelledOrderIds": ["5bd6e9286d99522a52e458de"]
        }
    }
    
    order_id = "5bd6e9286d99522a52e458de"
    symbol = "BTC/USDT"
    
    with patch.object(kucoin, '_make_request') as mock_request:
        mock_request.return_value = mock_response
        kucoin.cancel_order(order_id, symbol)
        
        # Check that the request was made with the correct parameters
        called_args = mock_request.call_args
        assert called_args[1]["method"] == HttpMethod.DELETE
        assert called_args[1]["endpoint"] == f"/api/v1/hf/orders/{order_id}"
        assert called_args[1]["signed"] == True

def test_get_order(kucoin):
    """Test getting order details"""
    mock_response = {
        "data": {
            "id": "5bd6e9286d99522a52e458de",
            "symbol": "BTC-USDT",
            "opType": "DEAL",
            "type": "limit",
            "side": "buy",
            "price": "10000",
            "size": "1",
            "funds": "10000",
            "dealFunds": "0",
            "dealSize": "0",
            "fee": "0",
            "feeCurrency": "USDT",
            "createdAt": 1550653727731,
            "status": "open"
        }
    }
    
    order_id = "5bd6e9286d99522a52e458de"
    symbol = "BTC/USDT"
    
    with patch.object(kucoin, '_make_request') as mock_request:
        mock_request.return_value = mock_response
        kucoin.get_order(order_id, symbol)
        
        # Check that the request was made with the correct parameters
        called_args = mock_request.call_args
        assert called_args[1]["method"] == HttpMethod.GET
        assert called_args[1]["endpoint"] == f"/api/v1/hf/orders/{order_id}"
        assert called_args[1]["signed"] == True 