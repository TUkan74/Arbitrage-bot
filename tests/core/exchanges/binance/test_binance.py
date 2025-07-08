import pytest
from unittest.mock import Mock, patch, AsyncMock
from core.exchanges.binance import BinanceExchange
from core.enums import HttpMethod


@pytest.fixture
def binance():
    """Create a BinanceExchange instance for testing"""
    return BinanceExchange()


def test_base_url(binance):
    """Test that the base URL is correct"""
    assert binance.base_url == "https://api1.binance.com"


def test_public_data_url(binance):
    """Test that the public data URL is correct"""
    assert binance.public_data_url == "https://data-api.binance.vision"


def test_format_symbol(binance):
    """Test symbol format conversion"""
    # Test standard format to Binance format
    assert binance._format_symbol("BTC/USDT") == "BTCUSDT"

    # Test already formatted symbol
    assert binance._format_symbol("BTCUSDT") == "BTCUSDT"


@pytest.mark.parametrize(
    "endpoint,expected_base",
    [
        ("/api/v3/ticker/24hr", "https://data-api.binance.vision"),
        ("/api/v3/depth", "https://data-api.binance.vision"),
        ("/api/v3/exchangeInfo", "https://data-api.binance.vision"),
        ("/api/v3/order", "https://api1.binance.com"),
        ("/api/v3/account", "https://api1.binance.com"),
    ],
)
@pytest.mark.asyncio
async def test_base_url_selection(binance, endpoint, expected_base):
    """Test that the correct base URL is selected based on the endpoint"""
    with patch("requests.request") as mock_raw_request:
        mock_raw_request.return_value.json.return_value = {}
        mock_raw_request.return_value.status_code = 200

        with (
            patch.object(binance, "_handle_rate_limit", AsyncMock()) as mock_handle_rate_limit,
            patch.object(binance, "_handle_error", AsyncMock()) as mock_handle_error,
        ):

            await binance._make_request(HttpMethod.GET, endpoint)

            assert mock_raw_request.call_args is not None, "requests.request was not called"
            called_args = mock_raw_request.call_args[0]
            called_url = called_args[1]
            assert called_url.startswith(
                expected_base
            ), f"Expected URL to start with {expected_base}, but got {called_url}"


@pytest.mark.asyncio
async def test_get_ticker(binance):
    """Test getting ticker data"""
    mock_response = {
        "lastPrice": "50000.00",
        "bidPrice": "49999.00",
        "askPrice": "50001.00",
        "volume": "100.5",
        "highPrice": "51000.00",
        "lowPrice": "49000.00",
        "closeTime": 1234567890,
        "priceChange": "1000.00",
        "priceChangePercent": "2.00",
    }

    with patch.object(binance, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        result = await binance.get_ticker("BTC/USDT")

        assert result["symbol"] == "BTC/USDT"
        assert result["last_price"] == 50000.00
        assert result["bid"] == 49999.00
        assert result["ask"] == 50001.00
        assert result["volume"] == 100.5
        assert result["high"] == 51000.00
        assert result["low"] == 49000.00
        assert result["timestamp"] == 1234567890
        assert result["change_24h"] == 1000.00
        assert result["change_percent_24h"] == 2.00


@pytest.mark.asyncio
async def test_get_order_book(binance):
    """Test getting order book data"""
    mock_response = {
        "bids": [["49999.00", "1.5"], ["49998.00", "2.0"]],
        "asks": [["50001.00", "1.0"], ["50002.00", "2.5"]],
        "lastUpdateId": 1234567890,
    }

    with patch.object(binance, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        result = await binance.get_order_book("BTC/USDT", limit=2)

        assert result["symbol"] == "BTC/USDT"
        assert result["bids"] == [[49999.00, 1.5], [49998.00, 2.0]]
        assert result["asks"] == [[50001.00, 1.0], [50002.00, 2.5]]
        assert result["timestamp"] == 1234567890


@pytest.mark.asyncio
async def test_get_trading_fees(binance):
    """Test getting trading fees"""
    mock_response = [{"symbol": "BTCUSDT", "makerCommission": "0.001", "takerCommission": "0.001"}]

    with patch.object(binance, "_make_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        result = await binance.get_trading_fees()

        assert "BTC/USDT" in result
        assert result["BTC/USDT"]["maker"] == 0.001
        assert result["BTC/USDT"]["taker"] == 0.001
