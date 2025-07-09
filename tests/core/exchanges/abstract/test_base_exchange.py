"""
Tests for the BaseExchange class.
"""

import pytest
import aiohttp
import asyncio
import os
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
import hmac
import hashlib
import json

from core.exchanges.abstract.base_exchange import BaseExchange
from core.enums import HttpMethod

class MockExchange(BaseExchange):
    """Mock exchange implementation for testing BaseExchange."""
    
    def __init__(self, exchange_name: str = "MOCK", **kwargs):
        super().__init__(exchange_name, **kwargs)
        
    @property
    def base_url(self) -> str:
        return "https://api.mock-exchange.com"
        
    async def _get_signed_headers(self, method: HttpMethod, endpoint: str, params=None) -> dict:
        timestamp = str(int(datetime.now().timestamp() * 1000))
        query_string = ""
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        
        signature = await self._create_signature(method, endpoint, query_string, timestamp)
        
        return {
            "X-MOCK-APIKEY": self.api_key,
            "X-MOCK-SIGNATURE": signature,
            "X-MOCK-TIMESTAMP": timestamp
        }
        
    def _format_symbol(self, symbol: str) -> str:
        return symbol.replace("/", "")
        
    async def _create_signature(self, method: HttpMethod, endpoint: str, query_string: str, timestamp: str) -> str:
        message = f"{method.value}{endpoint}{query_string}{timestamp}"
        signature = hmac.new(
            self.api_secret.encode('utf-8') if self.api_secret else b'',
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
        
    async def get_ticker(self, symbol: str):
        params = {"symbol": self._format_symbol(symbol)}
        return await self._make_request(HttpMethod.GET, "/api/v1/ticker", params)
        
    async def get_order_book(self, symbol: str, limit: int = 20):
        params = {"symbol": self._format_symbol(symbol), "limit": limit}
        return await self._make_request(HttpMethod.GET, "/api/v1/depth", params)
        
    async def get_exchange_info(self):
        return await self._make_request(HttpMethod.GET, "/api/v1/exchangeInfo")
        
    async def get_balance(self):
        return await self._make_request(HttpMethod.GET, "/api/v1/account", signed=True)
        
    async def get_trading_fees(self, symbol=None):
        params = {"symbol": self._format_symbol(symbol)} if symbol else None
        return await self._make_request(HttpMethod.GET, "/api/v1/trading-fees", params, signed=True)
        
    async def place_order(self, symbol: str, order_type: str, side: str, amount: float, price=None):
        params = {
            "symbol": self._format_symbol(symbol),
            "type": order_type,
            "side": side,
            "quantity": amount
        }
        if price:
            params["price"] = price
            
        return await self._make_request(HttpMethod.POST, "/api/v1/order", params, signed=True)
        
    async def cancel_order(self, order_id: str, symbol: str):
        params = {
            "symbol": self._format_symbol(symbol),
            "orderId": order_id
        }
        return await self._make_request(HttpMethod.DELETE, "/api/v1/order", params, signed=True)
        
    async def get_order(self, order_id: str, symbol: str):
        params = {
            "symbol": self._format_symbol(symbol),
            "orderId": order_id
        }
        return await self._make_request(HttpMethod.GET, "/api/v1/order", params, signed=True)
        
    async def transfer(self, currency: str, amount: float, from_account: str, to_account: str):
        params = {
            "currency": currency,
            "amount": amount,
            "fromAccount": from_account,
            "toAccount": to_account
        }
        return await self._make_request(HttpMethod.POST, "/api/v1/transfer", params, signed=True)
        
    async def withdraw(self, currency: str, amount: float, address: str, **params):
        withdraw_params = {
            "currency": currency,
            "amount": amount,
            "address": address,
            **params
        }
        return await self._make_request(HttpMethod.POST, "/api/v1/withdraw", withdraw_params, signed=True)

@pytest.fixture
async def mock_exchange():
    """Create a mock exchange instance for testing."""
    async with MockExchange() as exchange:
        yield exchange

@pytest.mark.asyncio
async def test_initialize_with_env_vars():
    """Test exchange initialization with environment variables."""
    with patch.dict(os.environ, {
        'MOCK_API_KEY': 'test_api_key',
        'MOCK_API_SECRET': 'test_api_secret'
    }, clear=True):
        async with MockExchange() as exchange:
            assert exchange.api_key == 'test_api_key'
            assert exchange.api_secret == 'test_api_secret'
            assert exchange.session is not None

@pytest.mark.asyncio
async def test_initialize_with_params():
    """Test exchange initialization with provided parameters."""
    async with MockExchange() as exchange:
        await exchange.initialize(api_key='test_key', api_secret='test_secret')
        assert exchange.api_key == 'test_key'
        assert exchange.api_secret == 'test_secret'
        assert exchange.session is not None

@pytest.mark.asyncio
async def test_rate_limiting(mock_exchange):
    """Test rate limiting functionality."""
    mock_exchange.rate_limit = 0.1  # Set rate limit to 100ms
    
    start_time = datetime.now()
    
    # Make multiple requests
    for _ in range(3):
        await mock_exchange._handle_rate_limit()
        
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Should take at least 0.2 seconds (2 delays of 0.1s)
    assert duration >= 0.2

@pytest.mark.asyncio
async def test_error_handling(mock_exchange):
    """Test error handling in requests."""
    # Mock aiohttp response
    mock_response = MagicMock()
    mock_response.status = 400
    mock_response.text = AsyncMock(return_value="Bad Request")
    
    with pytest.raises(Exception) as exc_info:
        await mock_exchange._handle_error(mock_response)
    assert "API Error: 400" in str(exc_info.value)

@pytest.mark.asyncio
async def test_make_request_success(mock_exchange):
    """Test successful API request."""
    # Mock successful response
    mock_response = {
        "symbol": "BTCUSDT",
        "price": "50000.00"
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_request.return_value.__aenter__.return_value.content_type = 'application/json'
        
        result = await mock_exchange._make_request(
            HttpMethod.GET,
            "/api/v1/ticker",
            {"symbol": "BTCUSDT"}
        )
        
        assert result == mock_response

@pytest.mark.asyncio
async def test_make_request_failure(mock_exchange):
    """Test failed API request."""
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.side_effect = aiohttp.ClientError("Connection Error")
        
        with pytest.raises(aiohttp.ClientError):
            await mock_exchange._make_request(
                HttpMethod.GET,
                "/api/v1/ticker",
                {"symbol": "BTCUSDT"}
            )

@pytest.mark.asyncio
async def test_signed_request(mock_exchange):
    """Test signed API request."""
    mock_exchange.api_key = "test_key"
    mock_exchange.api_secret = "test_secret"
    
    # Mock successful response
    mock_response = {"balance": "100.00"}
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_request.return_value.__aenter__.return_value.content_type = 'application/json'
        
        result = await mock_exchange._make_request(
            HttpMethod.GET,
            "/api/v1/account",
            signed=True
        )
        
        # Verify the request was made with signed headers
        call_args = mock_request.call_args
        headers = call_args[1]['headers']
        assert 'X-MOCK-APIKEY' in headers
        assert 'X-MOCK-SIGNATURE' in headers
        assert 'X-MOCK-TIMESTAMP' in headers
        assert result == mock_response

@pytest.mark.asyncio
async def test_format_symbol():
    """Test symbol formatting."""
    async with MockExchange() as exchange:
        formatted = exchange._format_symbol("BTC/USDT")
        assert formatted == "BTCUSDT"

@pytest.mark.asyncio
async def test_session_cleanup():
    """Test session cleanup on exit."""
    exchange = MockExchange()
    
    async with exchange:
        assert exchange.session is not None
        
    assert exchange.session is None

@pytest.mark.asyncio
async def test_get_ticker(mock_exchange):
    """Test get_ticker method."""
    mock_response = {
        "symbol": "BTCUSDT",
        "price": "50000.00",
        "volume": "100.00"
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_request.return_value.__aenter__.return_value.content_type = 'application/json'
        
        result = await mock_exchange.get_ticker("BTC/USDT")
        assert result == mock_response
        
        # Verify correct endpoint and parameters
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"  # Method
        assert call_args[0][1].endswith("/api/v1/ticker")  # Endpoint
        assert call_args[1]['params'] == {"symbol": "BTCUSDT"}  # Parameters

@pytest.mark.asyncio
async def test_get_order_book(mock_exchange):
    """Test get_order_book method."""
    mock_response = {
        "symbol": "BTCUSDT",
        "bids": [["49000.00", "1.00"], ["48900.00", "2.00"]],
        "asks": [["50000.00", "1.00"], ["50100.00", "2.00"]]
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_request.return_value.__aenter__.return_value.content_type = 'application/json'
        
        result = await mock_exchange.get_order_book("BTC/USDT", limit=10)
        assert result == mock_response
        
        # Verify correct endpoint and parameters
        call_args = mock_request.call_args
        assert call_args[1]['params'] == {"symbol": "BTCUSDT", "limit": 10}

@pytest.mark.asyncio
async def test_get_balance(mock_exchange):
    """Test get_balance method."""
    mock_exchange.api_key = "test_key"
    mock_exchange.api_secret = "test_secret"
    
    mock_response = {
        "balances": [
            {"asset": "BTC", "free": "1.00", "locked": "0.00"},
            {"asset": "USDT", "free": "50000.00", "locked": "0.00"}
        ]
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_request.return_value.__aenter__.return_value.content_type = 'application/json'
        
        result = await mock_exchange.get_balance()
        assert result == mock_response
        
        # Verify it was a signed request
        call_args = mock_request.call_args
        assert 'headers' in call_args[1]

@pytest.mark.asyncio
async def test_place_order(mock_exchange):
    """Test place_order method."""
    mock_exchange.api_key = "test_key"
    mock_exchange.api_secret = "test_secret"
    
    mock_response = {
        "symbol": "BTCUSDT",
        "orderId": "12345",
        "status": "FILLED"
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_request.return_value.__aenter__.return_value.content_type = 'application/json'
        
        result = await mock_exchange.place_order(
            symbol="BTC/USDT",
            order_type="LIMIT",
            side="BUY",
            amount=1.0,
            price=50000.0
        )
        assert result == mock_response
        
        # Verify correct parameters
        call_args = mock_request.call_args
        assert call_args[1]['json'] == {
            "symbol": "BTCUSDT",
            "type": "LIMIT",
            "side": "BUY",
            "quantity": 1.0,
            "price": 50000.0
        }

@pytest.mark.asyncio
async def test_error_handling_json_error(mock_exchange):
    """Test error handling with JSON error response."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.content_type = 'application/json'
    mock_response.json = AsyncMock(return_value={"error": "Invalid API key"})
    
    with pytest.raises(Exception) as exc_info:
        await mock_exchange._handle_error(mock_response)
    assert "Exchange Error: Invalid API key" in str(exc_info.value)

@pytest.mark.asyncio
async def test_error_handling_non_json_response(mock_exchange):
    """Test error handling with non-JSON response."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.content_type = 'text/plain'
    mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))
    
    # Should not raise an exception for non-JSON responses
    await mock_exchange._handle_error(mock_response)

@pytest.mark.asyncio
async def test_make_request_without_session():
    """Test making request without initializing session."""
    exchange = MockExchange()
    
    with pytest.raises(RuntimeError) as exc_info:
        await exchange._make_request(HttpMethod.GET, "/api/v1/ticker")
    assert "Session not initialized" in str(exc_info.value)

@pytest.mark.asyncio
async def test_close_without_session():
    """Test closing exchange without active session."""
    exchange = MockExchange()
    await exchange.close()  # Should not raise any exception

@pytest.mark.asyncio
async def test_initialize_multiple_times():
    """Test initializing exchange multiple times."""
    async with MockExchange() as exchange:
        # First initialization
        await exchange.initialize(api_key='key1', api_secret='secret1')
        assert exchange.api_key == 'key1'
        
        # Second initialization should update credentials
        await exchange.initialize(api_key='key2', api_secret='secret2')
        assert exchange.api_key == 'key2'
        assert exchange.session is not None  # Session should remain active

@pytest.mark.asyncio
async def test_rate_limit_concurrent_requests(mock_exchange):
    """Test rate limiting with concurrent requests."""
    mock_exchange.rate_limit = 0.1  # 100ms rate limit
    
    # Mock time.time() to have controlled timing
    current_time = [0.0]
    def mock_time():
        return current_time[0]
    
    with patch('time.time', side_effect=mock_time):
        async def make_request():
            await mock_exchange._handle_rate_limit()
            current_time[0] += 0.1  # Simulate time passing
            return current_time[0]
        
        # Make 3 concurrent requests
        results = await asyncio.gather(*[make_request() for _ in range(3)])
        
        # Verify timing
        assert len(results) == 3
        assert results[0] == pytest.approx(0.1, rel=1e-9)  # First request at 0.1s
        assert results[1] == pytest.approx(0.2, rel=1e-9)  # Second request at 0.2s
        assert results[2] == pytest.approx(0.3, rel=1e-9)  # Third request at 0.3s

@pytest.mark.asyncio
async def test_handle_error_with_error_code(mock_exchange):
    """Test error handling with error code response."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.content_type = 'application/json'
    mock_response.json = AsyncMock(return_value={"code": -1001, "msg": "Internal error"})
    
    with pytest.raises(Exception) as exc_info:
        await mock_exchange._handle_error(mock_response)
    assert "Exchange Error: Internal error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_make_request_post_with_json(mock_exchange):
    """Test making POST request with JSON body."""
    mock_response = {"orderId": "12345"}
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_request.return_value.__aenter__.return_value.content_type = 'application/json'
        
        params = {"symbol": "BTCUSDT", "side": "BUY", "quantity": 1.0}
        result = await mock_exchange._make_request(
            HttpMethod.POST,
            "/api/v1/order",
            params
        )
        
        # Verify JSON body was used instead of query params for POST
        call_args = mock_request.call_args
        assert call_args[1]['json'] == params
        assert call_args[1]['params'] is None
        assert result == mock_response 

@pytest.mark.asyncio
async def test_cancel_order(mock_exchange):
    """Test cancel_order method."""
    mock_exchange.api_key = "test_key"
    mock_exchange.api_secret = "test_secret"
    
    mock_response = {
        "orderId": "12345",
        "status": "CANCELED"
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_request.return_value.__aenter__.return_value.content_type = 'application/json'
        
        result = await mock_exchange.cancel_order("12345", "BTC/USDT")
        assert result == mock_response
        
        # Verify correct parameters
        call_args = mock_request.call_args
        assert call_args[1]['params'] == {
            "symbol": "BTCUSDT",
            "orderId": "12345"
        }

@pytest.mark.asyncio
async def test_get_order(mock_exchange):
    """Test get_order method."""
    mock_exchange.api_key = "test_key"
    mock_exchange.api_secret = "test_secret"
    
    mock_response = {
        "orderId": "12345",
        "symbol": "BTCUSDT",
        "status": "FILLED",
        "price": "50000.00",
        "quantity": "1.0"
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_request.return_value.__aenter__.return_value.content_type = 'application/json'
        
        result = await mock_exchange.get_order("12345", "BTC/USDT")
        assert result == mock_response
        
        # Verify correct parameters
        call_args = mock_request.call_args
        assert call_args[1]['params'] == {
            "symbol": "BTCUSDT",
            "orderId": "12345"
        }

@pytest.mark.asyncio
async def test_transfer(mock_exchange):
    """Test transfer method."""
    mock_exchange.api_key = "test_key"
    mock_exchange.api_secret = "test_secret"
    
    mock_response = {
        "success": True,
        "transferId": "12345"
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_request.return_value.__aenter__.return_value.content_type = 'application/json'
        
        result = await mock_exchange.transfer(
            currency="BTC",
            amount=1.0,
            from_account="spot",
            to_account="margin"
        )
        assert result == mock_response
        
        # Verify correct parameters
        call_args = mock_request.call_args
        assert call_args[1]['json'] == {
            "currency": "BTC",
            "amount": 1.0,
            "fromAccount": "spot",
            "toAccount": "margin"
        }

@pytest.mark.asyncio
async def test_withdraw(mock_exchange):
    """Test withdraw method."""
    mock_exchange.api_key = "test_key"
    mock_exchange.api_secret = "test_secret"
    
    mock_response = {
        "success": True,
        "withdrawId": "12345"
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_request.return_value.__aenter__.return_value.content_type = 'application/json'
        
        result = await mock_exchange.withdraw(
            currency="BTC",
            amount=1.0,
            address="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            network="BTC"
        )
        assert result == mock_response
        
        # Verify correct parameters
        call_args = mock_request.call_args
        assert call_args[1]['json'] == {
            "currency": "BTC",
            "amount": 1.0,
            "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "network": "BTC"
        }

@pytest.mark.asyncio
async def test_get_exchange_info(mock_exchange):
    """Test get_exchange_info method."""
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
        mock_request.return_value.__aenter__.return_value.content_type = 'application/json'
        
        result = await mock_exchange.get_exchange_info()
        assert result == mock_response

@pytest.mark.asyncio
async def test_get_trading_fees(mock_exchange):
    """Test get_trading_fees method."""
    mock_exchange.api_key = "test_key"
    mock_exchange.api_secret = "test_secret"
    
    mock_response = {
        "BTC/USDT": {
            "maker": 0.001,
            "taker": 0.001
        }
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_request.return_value.__aenter__.return_value.status = 200
        mock_request.return_value.__aenter__.return_value.json = AsyncMock(
            return_value=mock_response
        )
        mock_request.return_value.__aenter__.return_value.content_type = 'application/json'
        
        # Test with specific symbol
        result = await mock_exchange.get_trading_fees("BTC/USDT")
        assert result == mock_response
        
        # Verify correct parameters
        call_args = mock_request.call_args
        assert call_args[1]['params'] == {"symbol": "BTCUSDT"}
        
        # Test without symbol
        result = await mock_exchange.get_trading_fees()
        assert result == mock_response
        
        # Verify no symbol parameter
        call_args = mock_request.call_args
        assert call_args[1]['params'] is None

def test_abstract_methods():
    """Test that abstract methods raise NotImplementedError."""
    class ConcreteExchange(BaseExchange):
        """Concrete exchange class that doesn't implement abstract methods."""
        pass
    
    with pytest.raises(TypeError, match=r"Can't instantiate abstract class"):
        ConcreteExchange("TEST") 