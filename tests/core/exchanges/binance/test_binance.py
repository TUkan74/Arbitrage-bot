"""
Tests for the BinanceExchange class.
"""

import pytest
import aiohttp
from unittest.mock import patch, AsyncMock, MagicMock
import time
import hmac
import hashlib
import base64
from urllib.parse import urlencode

from core.exchanges.binance.binance import BinanceExchange
from core.enums import HttpMethod

@pytest.fixture
async def exchange():
    """Create a BinanceExchange instance for testing."""
    async with BinanceExchange() as binance:
        binance.api_key = "test_key"
        binance.api_secret = "test_secret"
        yield binance

@pytest.mark.asyncio
async def test_base_url(exchange):
    """Test base URL property."""
    assert exchange.base_url == "https://api1.binance.com"
    assert exchange.public_data_url == "https://data-api.binance.vision"

@pytest.mark.asyncio
async def test_format_symbol(exchange):
    """Test symbol format conversion."""
    assert exchange._format_symbol("BTC/USDT") == "BTCUSDT"
    assert exchange._format_symbol("BTCUSDT") == "BTCUSDT"

@pytest.mark.asyncio
async def test_create_signature_hmac(exchange):
    """Test HMAC signature creation."""
    method = HttpMethod.GET
    endpoint = "/api/v3/order"
    query_string = "symbol=BTCUSDT&side=BUY&type=LIMIT&quantity=1.0"
    timestamp = "1625097600000"
    
    signature = await exchange._create_signature(method, endpoint, query_string, timestamp)
    
    # Verify signature
    msg = f"{query_string}&timestamp={timestamp}"
    expected_signature = hmac.new(
        exchange.api_secret.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    assert signature == expected_signature

@pytest.mark.asyncio
async def test_create_signature_ed25519(exchange):
    """Test Ed25519 signature creation."""
    # Mock private key
    mock_key = MagicMock()
    mock_key.sign = MagicMock(return_value=b"signature")
    exchange.private_key = mock_key
    
    signature = await exchange._create_signature(
        HttpMethod.GET,
        "/api/v3/order",
        "symbol=BTCUSDT",
        "1625097600000"
    )
    
    assert signature == base64.b64encode(b"signature").decode("utf-8")

@pytest.mark.asyncio
async def test_get_signed_headers(exchange):
    """Test signed headers generation."""
    headers = await exchange._get_signed_headers(
        HttpMethod.GET,
        "/api/v3/order",
        {"symbol": "BTCUSDT"}
    )
    
    assert headers == {"X-MBX-APIKEY": "test_key"}

@pytest.mark.asyncio
async def test_get_exchange_info(exchange):
    """Test getting exchange info."""
    mock_response = {
        "timezone": "UTC",
        "serverTime": 1625097600000,
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "status": "TRADING",
                "baseAsset": "BTC",
                "quoteAsset": "USDT"
            }
        ]
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        result = await exchange.get_exchange_info()
        
        assert result['exchange'] == 'BINANCE'
        assert len(result['symbols']) == 1
        assert result['symbols'][0]['symbol'] == 'BTC/USDT'

@pytest.mark.asyncio
async def test_get_ticker(exchange):
    """Test getting ticker data."""
    mock_response = {
        "symbol": "BTCUSDT",
        "lastPrice": "50000.00",
        "bidPrice": "49990.00",
        "askPrice": "50010.00"
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        result = await exchange.get_ticker("BTC/USDT")
        
        assert result['symbol'] == 'BTC/USDT'
        assert result['last_price'] == 50000.00
        assert result['bid'] == 49990.00
        assert result['ask'] == 50010.00

@pytest.mark.asyncio
async def test_get_order_book(exchange):
    """Test getting order book."""
    mock_response = {
        "lastUpdateId": 1234567890,
        "bids": [["50000.00", "1.00"]],
        "asks": [["50010.00", "1.00"]]
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        result = await exchange.get_order_book("BTC/USDT", 5)
        
        assert result['symbol'] == 'BTC/USDT'
        assert len(result['bids']) == 1
        assert len(result['asks']) == 1
        assert result['bids'][0] == [50000.00, 1.00]

@pytest.mark.asyncio
async def test_get_balance(exchange):
    """Test getting account balance."""
    mock_response = {
        "balances": [
            {
                "asset": "BTC",
                "free": "1.00",
                "locked": "0.50"
            }
        ]
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        result = await exchange.get_balance()
        
        assert 'BTC' in result
        assert result['BTC']['free'] == 1.00
        assert result['BTC']['locked'] == 0.50

@pytest.mark.asyncio
async def test_get_trading_fees(exchange):
    """Test getting trading fees."""
    mock_response = [
        {
            "symbol": "BTCUSDT",
            "makerCommission": "0.001",
            "takerCommission": "0.001"
        }
    ]
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        result = await exchange.get_trading_fees("BTC/USDT")
        
        assert 'BTC/USDT' in result
        assert result['BTC/USDT']['maker'] == 0.001
        assert result['BTC/USDT']['taker'] == 0.001

@pytest.mark.asyncio
async def test_place_order(exchange):
    """Test placing an order."""
    mock_response = {
        "orderId": "12345",
        "symbol": "BTCUSDT",
        "status": "NEW"
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        result = await exchange.place_order(
            symbol="BTC/USDT",
            order_type="LIMIT",
            side="BUY",
            amount=1.0,
            price=50000.0
        )
        
        assert result['id'] == '12345'
        assert result['status'] == 'NEW'

@pytest.mark.asyncio
async def test_cancel_order(exchange):
    """Test canceling an order."""
    mock_response = {
        "orderId": "12345",
        "symbol": "BTCUSDT",
        "status": "CANCELED"
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        result = await exchange.cancel_order("12345", "BTC/USDT")
        
        assert result['id'] == '12345'
        assert result['status'] == 'CANCELED'

@pytest.mark.asyncio
async def test_get_order(exchange):
    """Test getting order details."""
    mock_response = {
        "orderId": "12345",
        "symbol": "BTCUSDT",
        "status": "FILLED"
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        result = await exchange.get_order("12345", "BTC/USDT")
        
        assert result['id'] == '12345'
        assert result['status'] == 'FILLED'

@pytest.mark.asyncio
async def test_transfer_not_implemented(exchange):
    """Test transfer method (not implemented)."""
    result = await exchange.transfer("BTC", 1.0, "spot", "margin")
    assert result['success'] is False
    assert "not implemented" in result['message'].lower()

@pytest.mark.asyncio
async def test_withdraw_not_implemented(exchange):
    """Test withdraw method (not implemented)."""
    result = await exchange.withdraw("BTC", 1.0, "address")
    assert result['success'] is False
    assert "not implemented" in result['message'].lower()

@pytest.mark.asyncio
async def test_make_request_public_data_url(exchange):
    """Test make_request using public data URL."""
    mock_response = {"data": "test"}
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        
        # Test public market data endpoint
        result = await exchange._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v3/ticker/24hr",
            params={"symbol": "BTCUSDT"}
        )
        
        assert result == mock_response
        # Verify public data URL was used
        call_args = mock_request.call_args
        assert exchange.public_data_url in call_args[0][1]  # URL is the second positional argument

@pytest.mark.asyncio
async def test_make_request_error_handling(exchange):
    """Test make_request error handling."""
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 400
        mock_request.return_value.__aenter__.return_value.text = AsyncMock(
            return_value="Invalid request"
        )
        
        with pytest.raises(Exception) as exc_info:
            await exchange._make_request(
                method=HttpMethod.GET,
                endpoint="/api/v3/order",
                params={"symbol": "BTCUSDT"}
            )
        
        assert "API Error: 400" in str(exc_info.value)

@pytest.mark.asyncio
async def test_make_request_without_session(exchange):
    """Test make_request without initialized session."""
    exchange.session = None
    
    with pytest.raises(RuntimeError) as exc_info:
        await exchange._make_request(
            method=HttpMethod.GET,
            endpoint="/api/v3/ticker/24hr"
        )
    
    assert "Session not initialized" in str(exc_info.value)
