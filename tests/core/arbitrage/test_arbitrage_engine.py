"""
Tests for the arbitrage engine.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch

from core.arbitrage.engine import ArbitrageEngine
from core.exchanges.abstract import ExchangeInterface


class MockExchange(ExchangeInterface):
    """Mock exchange implementation for testing."""

    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        self.calls = []

    async def initialize(self):
        """Mock initialize method."""
        self._record_call("initialize")
        # In a real scenario, this might involve setting up connections, etc.
        await asyncio.sleep(0)  # Simulate async operation

    async def __aenter__(self):
        """Mock async context manager enter."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Mock async context manager exit."""
        # In a real scenario, this might involve closing connections, etc.
        self._record_call("__aexit__", exc_type, exc_val, exc_tb)
        await asyncio.sleep(0)  # Simulate async operation

    def _record_call(self, method_name, *args, **kwargs):
        self.calls.append((method_name, args, kwargs))

    # ExchangeInterface implementations
    @property
    def base_url(self) -> str:
        return f"https://api.{self.exchange_name.lower()}.com"

    async def get_exchange_info(self):
        self._record_call("get_exchange_info")
        await asyncio.sleep(0)  # Simulate async operation
        return {
            "symbols": [
                {"symbol": "BTC/USDT", "status": "TRADING"},
                {"symbol": "ETH/USDT", "status": "TRADING"},
            ]
        }

    async def get_ticker(self, symbol: str):
        self._record_call("get_ticker", symbol)
        await asyncio.sleep(0)  # Simulate async operation
        return {
            "symbol": symbol,
            "last_price": 50000.0 if symbol == "BTC/USDT" else 3000.0,
            "bid": 49990.0 if symbol == "BTC/USDT" else 2995.0,
            "ask": 50010.0 if symbol == "BTC/USDT" else 3005.0,
        }

    async def get_order_book(self, symbol: str, limit: int = 20):
        self._record_call("get_order_book", symbol, limit)
        await asyncio.sleep(0)  # Simulate async operation
        if self.exchange_name == "BINANCE":
            return {
                "symbol": symbol,
                "bids": [[49990.0, 1.0], [49980.0, 2.0]],
                "asks": [[50010.0, 1.0], [50020.0, 2.0]],
            }
        else:
            return {
                "symbol": symbol,
                "bids": [[49995.0, 1.0], [49985.0, 2.0]],
                "asks": [[50005.0, 1.0], [50015.0, 2.0]],
            }

    async def get_balance(self):
        self._record_call("get_balance")
        await asyncio.sleep(0)  # Simulate async operation
        return {"USDT": 10000.0, "BTC": 1.0, "ETH": 10.0}

    async def get_trading_fees(self, symbol=None):
        self._record_call("get_trading_fees", symbol)
        await asyncio.sleep(0)  # Simulate async operation
        fees = {
            "BTC/USDT": {"maker": 0.001, "taker": 0.001},
            "ETH/USDT": {"maker": 0.001, "taker": 0.001},
        }
        if symbol:
            return {symbol: fees.get(symbol, {"maker": 0.001, "taker": 0.001})}
        return fees

    async def place_order(self, symbol, order_type, side, amount, price=None):
        self._record_call("place_order", symbol, order_type, side, amount, price)
        await asyncio.sleep(0)  # Simulate async operation
        return {"id": "123456", "status": "SUBMITTED"}

    async def cancel_order(self, order_id, symbol):
        self._record_call("cancel_order", order_id, symbol)
        await asyncio.sleep(0)  # Simulate async operation
        return {"id": order_id, "status": "CANCELED"}

    async def get_order(self, order_id, symbol):
        self._record_call("get_order", order_id, symbol)
        await asyncio.sleep(0)  # Simulate async operation
        return {"id": order_id, "status": "FILLED"}

    async def transfer(self, currency, amount, from_account, to_account):
        self._record_call("transfer", currency, amount, from_account, to_account)
        await asyncio.sleep(0)  # Simulate async operation
        return {"success": True}

    async def withdraw(self, currency, amount, address, **params):
        self._record_call("withdraw", currency, amount, address, **params)
        await asyncio.sleep(0)  # Simulate async operation
        return {"success": True}


@pytest.fixture
async def engine():
    """Create an arbitrage engine for testing."""
    async with MockExchange("BINANCE") as binance, MockExchange("KUCOIN") as kucoin:
        exchanges = {"BINANCE": binance, "KUCOIN": kucoin}

        engine_instance = ArbitrageEngine(
            exchanges=exchanges,
            initial_capital=1000.0,
            min_profit_percentage=0.1,
            max_slippage=0.5,
            target_symbols=["BTC/USDT", "ETH/USDT"],
        )
        return engine_instance


@pytest.mark.asyncio
async def test_initialization(engine):
    """Test that the engine initializes correctly."""
    engine_instance = engine
    assert len(engine_instance.exchanges) == 2
    assert engine_instance.initial_capital == 1000.0
    assert engine_instance.min_profit_percentage == 0.1
    assert len(engine_instance.target_symbols) == 2


@pytest.mark.asyncio
async def test_estimate_slippage(engine):
    """Test slippage estimation."""
    engine_instance = engine
    order_book = {
        "bids": [[100.0, 1.0], [99.0, 2.0], [98.0, 3.0]],
        "asks": [[101.0, 1.0], [102.0, 2.0], [103.0, 3.0]],
    }

    # Test buy slippage when order size fits in first level
    buy_slippage_small = engine_instance.estimate_slippage(order_book, 0.5, "buy")
    assert buy_slippage_small == 0.0

    # Test buy slippage when order requires multiple levels
    buy_slippage_large = engine_instance.estimate_slippage(order_book, 2.5, "buy")
    assert buy_slippage_large > 0.0

    # Test sell slippage
    sell_slippage_small = engine_instance.estimate_slippage(order_book, 0.5, "sell")
    assert sell_slippage_small == 0.0

    sell_slippage_large = engine_instance.estimate_slippage(order_book, 2.5, "sell")
    assert sell_slippage_large > 0.0


@pytest.mark.asyncio
async def test_scan_opportunities(engine, monkeypatch):
    """Test opportunity scanning."""
    engine_instance = engine
    # Setup order books cache with a very clear arbitrage opportunity
    engine_instance.order_books_cache = {
        "BTC/USDT": {
            "BINANCE": {
                "data": {
                    "bids": [[49900.0, 1.0], [49800.0, 2.0]],
                    "asks": [[50000.0, 1.0], [50100.0, 2.0]],
                },
                "timestamp": 123456789,
            },
            "KUCOIN": {
                "data": {
                    "bids": [[50500.0, 1.0], [50400.0, 2.0]],
                    "asks": [[50600.0, 1.0], [50700.0, 2.0]],
                },
                "timestamp": 123456789,
            },
        }
    }

    # Set a lower minimum profit threshold for the test
    engine_instance.min_profit_percentage = 0.05

    # Mock trading fees (make them very low to ensure profit)
    engine_instance.trading_fees_cache = {
        "BINANCE": {"BTC/USDT": {"maker": 0.0005, "taker": 0.0005}},
        "KUCOIN": {"BTC/USDT": {"maker": 0.0005, "taker": 0.0005}},
    }

    # Mock asyncio.sleep
    async def mock_sleep(*args, **kwargs):
        pass

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    # Run scan
    opportunities = await engine_instance.scan_opportunities()

    # There should be an opportunity (BINANCE buy, KUCOIN sell)
    assert len(opportunities) > 0
    if opportunities:
        opp = opportunities[0]
        assert opp["symbol"] == "BTC/USDT"
        assert opp["buy_exchange"] == "BINANCE"
        assert opp["sell_exchange"] == "KUCOIN"
        assert opp["profit_percentage"] > 0.05  # Verify profit exceeds threshold


@pytest.mark.asyncio
async def test_no_opportunity_when_prices_too_close(engine, monkeypatch):
    """Test that no opportunity is found when prices are too close."""
    engine_instance = engine
    # Setup order books cache with very close prices
    engine_instance.order_books_cache = {
        "BTC/USDT": {
            "BINANCE": {
                "data": {
                    "bids": [[50000.0, 1.0], [49990.0, 2.0]],
                    "asks": [[50010.0, 1.0], [50020.0, 2.0]],
                },
                "timestamp": 123456789,
            },
            "KUCOIN": {
                "data": {
                    "bids": [[50005.0, 1.0], [49995.0, 2.0]],
                    "asks": [[50015.0, 1.0], [50025.0, 2.0]],
                },
                "timestamp": 123456789,
            },
        }
    }

    # Set min profit to 0.5%
    engine_instance.min_profit_percentage = 0.5

    # Mock trading fees
    engine_instance.trading_fees_cache = {
        "BINANCE": {"BTC/USDT": {"maker": 0.001, "taker": 0.001}},
        "KUCOIN": {"BTC/USDT": {"maker": 0.001, "taker": 0.001}},
    }

    # Mock asyncio.sleep
    async def mock_sleep(*args, **kwargs):
        pass

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    # Run scan
    opportunities = await engine_instance.scan_opportunities()

    # There should be no opportunities
    assert len(opportunities) == 0
