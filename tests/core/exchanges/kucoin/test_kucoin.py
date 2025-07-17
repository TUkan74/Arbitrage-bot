"""
Tests for the KuCoin exchange implementation.
"""

import pytest
import aiohttp
from unittest.mock import patch, MagicMock, AsyncMock
import time
import hmac
import hashlib
import base64
from datetime import datetime
import json

from core.exchanges.kucoin.kucoin import KucoinExchange
from core.enums import HttpMethod

@pytest.fixture
async def exchange():
    """Create a KuCoin exchange instance."""
    exchange = KucoinExchange(
        api_key="test_key",
        api_secret="test_secret",
        api_passphrase="test_passphrase"
    )
    async with exchange:
        yield exchange

def test_initialization():
    """Test exchange initialization."""
    exchange = KucoinExchange(
        api_key="test_key",
        api_secret="test_secret",
        api_passphrase="test_passphrase"
    )
    assert exchange.api_key == "test_key"
    assert exchange.api_secret == "test_secret"
    assert exchange.api_passphrase != "test_passphrase"  # Should be signed
    assert exchange.base_url == "https://api.kucoin.com"

def test_sign_passphrase():
    """Test API passphrase signing."""
    exchange = KucoinExchange(
        api_key="test_key",
        api_secret="test_secret",
        api_passphrase="test_passphrase"
    )
    signed = exchange._sign_passphrase("test_passphrase")
    assert isinstance(signed, str)
    assert len(signed) > 0

@pytest.mark.asyncio
async def test_create_signature(exchange):
    """Test signature creation."""
    signature = await exchange._create_signature(
        method=HttpMethod.GET,
        endpoint="/api/v1/accounts",
        query_string="currency=BTC",
        timestamp="1625097600000"
    )
    assert isinstance(signature, str)
    assert len(signature) > 0

@pytest.mark.asyncio
async def test_get_signed_headers(exchange):
    """Test getting signed headers."""
    headers = await exchange._get_signed_headers(
        method=HttpMethod.GET,
        endpoint="/api/v1/accounts",
        params={"currency": "BTC"}
    )
    assert "KC-API-KEY" in headers
    assert "KC-API-SIGN" in headers
    assert "KC-API-TIMESTAMP" in headers
    assert "KC-API-PASSPHRASE" in headers
    assert headers["KC-API-KEY-VERSION"] == "2"

def test_format_symbol(exchange):
    """Test symbol formatting."""
    assert exchange._format_symbol("BTC/USDT") == "BTC-USDT"

@pytest.mark.asyncio
async def test_make_request_no_session(exchange):
    """Test making request without initialized session."""
    exchange.session = None
    with pytest.raises(RuntimeError, match="Session not initialized"):
        await exchange._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v1/accounts"
        )

@pytest.mark.asyncio
async def test_get_exchange_info(exchange):
    """Test getting exchange information."""
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "code": "200000",
            "data": [
                {
                    "symbol": "BTC-USDT",
                    "name": "BTC-USDT",
                    "baseCurrency": "BTC",
                    "quoteCurrency": "USDT",
                    "baseMinSize": "0.00001",
                    "quoteMinSize": "0.01",
                    "baseMaxSize": "10000",
                    "quoteMaxSize": "100000",
                    "baseIncrement": "0.00000001",
                    "quoteIncrement": "0.01",
                    "priceIncrement": "0.01",
                    "feeCurrency": "USDT",
                    "enableTrading": True,
                }
            ]
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        info = await exchange.get_exchange_info()
        assert info["exchange"] == "KUCOIN"
        assert len(info["symbols"]) == 1
        assert info["symbols"][0]["symbol"] == "BTC/USDT"
        assert info["symbols"][0]["status"] == "TRADING"

@pytest.mark.asyncio
async def test_get_ticker(exchange):
    """Test getting ticker information."""
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "code": "200000",
            "data": {
                "sequence": "1550467636704",
                "bestAsk": "0.03715004",
                "size": "0.17",
                "price": "0.03715005",
                "bestBid": "0.03715003",
                "time": 1550467636704
            }
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        ticker = await exchange.get_ticker("BTC/USDT")
        assert ticker["symbol"] == "BTC/USDT"
        assert "last_price" in ticker
        assert "bid" in ticker
        assert "ask" in ticker

@pytest.mark.asyncio
async def test_get_order_book(exchange):
    """Test getting order book."""
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "code": "200000",
            "data": {
                "sequence": "3262786978",
                "time": 1550476872008,
                "bids": [["0.03715", "0.17"], ["0.03714", "0.25"]],
                "asks": [["0.03716", "0.35"], ["0.03717", "0.15"]]
            }
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        order_book = await exchange.get_order_book("BTC/USDT", limit=20)
        assert order_book["symbol"] == "BTC/USDT"
        assert len(order_book["bids"]) == 2
        assert len(order_book["asks"]) == 2

@pytest.mark.asyncio
async def test_get_balance(exchange):
    """Test getting account balance."""
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "code": "200000",
            "data": [
                {
                    "id": "5bd6e9286d99522a52e458de",
                    "currency": "BTC",
                    "type": "trade",
                    "balance": "1.00000000",
                    "available": "0.99000000",
                    "holds": "0.01000000"
                }
            ]
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        balance = await exchange.get_balance()
        assert "BTC" in balance
        assert balance["BTC"]["free"] == 0.99
        assert balance["BTC"]["locked"] == 0.01
        assert balance["BTC"]["total"] == 1.0

@pytest.mark.asyncio
async def test_get_balance_with_account_id(exchange):
    """Test getting balance for specific account."""
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "code": "200000",
            "data": {
                "currency": "BTC",
                "balance": "1.00000000",
                "available": "0.99000000",
                "holds": "0.01000000"
            }
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        balance = await exchange.get_balance(account_id="test_account")
        assert "BTC" in balance
        assert balance["BTC"]["free"] == 0.99
        assert balance["BTC"]["locked"] == 0.01
        assert balance["BTC"]["total"] == 1.0

@pytest.mark.asyncio
async def test_get_account_id(exchange):
    """Test getting account ID."""
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "code": "200000",
            "data": [
                {
                    "id": "5bd6e9286d99522a52e458de",
                    "currency": "BTC",
                    "type": "trade",
                    "balance": "1.00000000",
                    "available": "0.99000000",
                    "holds": "0.01000000"
                }
            ]
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        account_id = await exchange.get_account_id()
        assert account_id == "5bd6e9286d99522a52e458de"

@pytest.mark.asyncio
async def test_get_trading_fees(exchange):
    """Test getting trading fees."""
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "code": "200000",
            "data": {
                "makerFeeRate": "0.001",
                "takerFeeRate": "0.001",
                "symbol": "BTC-USDT"
            }
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        fees = await exchange.get_trading_fees("BTC/USDT")
        assert "BTC/USDT" in fees
        assert fees["BTC/USDT"]["maker"] == 0.001
        assert fees["BTC/USDT"]["taker"] == 0.001

@pytest.mark.asyncio
async def test_place_limit_order(exchange):
    """Test placing a limit order."""
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "code": "200000",
            "data": {
                "orderId": "5bd6e9286d99522a52e458de"
            }
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        order = await exchange.place_order(
            symbol="BTC/USDT",
            order_type="limit",
            side="buy",
            amount=1.0,
            price=50000.0
        )
        assert order["id"] == "5bd6e9286d99522a52e458de"
        assert order["status"] == "SUBMITTED"

@pytest.mark.asyncio
async def test_place_market_order(exchange):
    """Test placing a market order."""
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "code": "200000",
            "data": {
                "orderId": "5bd6e9286d99522a52e458de"
            }
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        order = await exchange.place_order(
            symbol="BTC/USDT",
            order_type="market",
            side="buy",
            amount=1.0
        )
        assert order["id"] == "5bd6e9286d99522a52e458de"
        assert order["status"] == "SUBMITTED"



@pytest.mark.asyncio
async def test_get_order(exchange):
    """Test getting order status."""
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "code": "200000",
            "data": {
                "id": "5bd6e9286d99522a52e458de",
                "symbol": "BTC-USDT",
                "type": "limit",
                "side": "buy",
                "price": "50000",
                "size": "1.0",
                "dealSize": "0.5",
                "dealFunds": "25000",
                "status": "PARTIALLY_FILLED",
                "createdAt": 1550476872008
            }
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        order = await exchange.get_order("5bd6e9286d99522a52e458de", "BTC/USDT")
        assert order["id"] == "5bd6e9286d99522a52e458de"
        assert order["status"] == "PARTIALLY_FILLED"
        assert order["filled_percent"] == 50.0

@pytest.mark.asyncio
async def test_error_handling(exchange):
    """Test error handling in API requests."""
    with patch('aiohttp.ClientSession.request') as mock_request:
        # Test 400 error
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value=json.dumps({
            "code": "400100",
            "msg": "Invalid parameter"
        }))
        mock_response.json = AsyncMock(return_value={
            "code": "400100",
            "msg": "Invalid parameter"
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(Exception, match="Invalid parameter"):
            await exchange.get_ticker("BTC/USDT")
        
        # Test network error
        mock_request.side_effect = aiohttp.ClientError("Network error")
        with pytest.raises(aiohttp.ClientError, match="Network error"):
            await exchange.get_ticker("BTC/USDT") 