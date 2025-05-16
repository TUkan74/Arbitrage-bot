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
    
    def _record_call(self, method_name, *args, **kwargs):
        self.calls.append((method_name, args, kwargs))
    
    # ExchangeInterface implementations
    @property
    def base_url(self) -> str:
        return f"https://api.{self.exchange_name.lower()}.com"
    
    def get_exchange_info(self):
        self._record_call("get_exchange_info")
        return {"symbols": [
            {"symbol": "BTC/USDT", "status": "TRADING"},
            {"symbol": "ETH/USDT", "status": "TRADING"}
        ]}
    
    def get_ticker(self, symbol: str):
        self._record_call("get_ticker", symbol)
        return {
            "symbol": symbol,
            "last_price": 50000.0 if symbol == "BTC/USDT" else 3000.0,
            "bid": 49990.0 if symbol == "BTC/USDT" else 2995.0,
            "ask": 50010.0 if symbol == "BTC/USDT" else 3005.0
        }
    
    def get_order_book(self, symbol: str, limit: int = 20):
        self._record_call("get_order_book", symbol, limit)
        if self.exchange_name == "BINANCE":
            return {
                "symbol": symbol,
                "bids": [[49990.0, 1.0], [49980.0, 2.0]],
                "asks": [[50010.0, 1.0], [50020.0, 2.0]]
            }
        else:
            return {
                "symbol": symbol,
                "bids": [[49995.0, 1.0], [49985.0, 2.0]],
                "asks": [[50005.0, 1.0], [50015.0, 2.0]]
            }
    
    def get_balance(self):
        self._record_call("get_balance")
        return {"USDT": 10000.0, "BTC": 1.0, "ETH": 10.0}
    
    def get_trading_fees(self, symbol=None):
        self._record_call("get_trading_fees", symbol)
        fees = {
            "BTC/USDT": {"maker": 0.001, "taker": 0.001},
            "ETH/USDT": {"maker": 0.001, "taker": 0.001}
        }
        if symbol:
            return {symbol: fees.get(symbol, {"maker": 0.001, "taker": 0.001})}
        return fees
    
    def place_order(self, symbol, order_type, side, amount, price=None):
        self._record_call("place_order", symbol, order_type, side, amount, price)
        return {"id": "123456", "status": "SUBMITTED"}
    
    def cancel_order(self, order_id, symbol):
        self._record_call("cancel_order", order_id, symbol)
        return {"id": order_id, "status": "CANCELED"}
    
    def get_order(self, order_id, symbol):
        self._record_call("get_order", order_id, symbol)
        return {"id": order_id, "status": "FILLED"}
    
    def transfer(self, currency, amount, from_account, to_account):
        self._record_call("transfer", currency, amount, from_account, to_account)
        return {"success": True}
    
    def withdraw(self, currency, amount, address, **params):
        self._record_call("withdraw", currency, amount, address, **params)
        return {"success": True}


@pytest.fixture
def engine():
    """Create an arbitrage engine for testing."""
    binance = MockExchange("BINANCE")
    kucoin = MockExchange("KUCOIN")
    
    exchanges = {
        "BINANCE": binance,
        "KUCOIN": kucoin
    }
    
    engine = ArbitrageEngine(
        exchanges=exchanges,
        initial_capital=1000.0,
        min_profit_percentage=0.1,
        max_slippage=0.5,
        target_symbols=["BTC/USDT", "ETH/USDT"]
    )
    return engine


def test_initialization(engine):
    """Test that the engine initializes correctly."""
    assert len(engine.exchanges) == 2
    assert engine.initial_capital == 1000.0
    assert engine.min_profit_percentage == 0.1
    assert len(engine.target_symbols) == 2


def test_estimate_slippage(engine):
    """Test slippage estimation."""
    order_book = {
        "bids": [[100.0, 1.0], [99.0, 2.0], [98.0, 3.0]],
        "asks": [[101.0, 1.0], [102.0, 2.0], [103.0, 3.0]]
    }
    
    # Test buy slippage when order size fits in first level
    buy_slippage_small = engine.estimate_slippage(order_book, 0.5, "buy")
    assert buy_slippage_small == 0.0
    
    # Test buy slippage when order requires multiple levels
    buy_slippage_large = engine.estimate_slippage(order_book, 2.5, "buy")
    assert buy_slippage_large > 0.0
    
    # Test sell slippage
    sell_slippage_small = engine.estimate_slippage(order_book, 0.5, "sell")
    assert sell_slippage_small == 0.0
    
    sell_slippage_large = engine.estimate_slippage(order_book, 2.5, "sell")
    assert sell_slippage_large > 0.0


@pytest.mark.asyncio
async def test_scan_opportunities(engine, monkeypatch):
    """Test opportunity scanning."""
    # Setup order books cache with a very clear arbitrage opportunity
    engine.order_books_cache = {
        "BTC/USDT": {
            "BINANCE": {
                "data": {
                    "bids": [[49900.0, 1.0], [49800.0, 2.0]],
                    "asks": [[50000.0, 1.0], [50100.0, 2.0]]
                },
                "timestamp": 123456789
            },
            "KUCOIN": {
                "data": {
                    "bids": [[50500.0, 1.0], [50400.0, 2.0]],
                    "asks": [[50600.0, 1.0], [50700.0, 2.0]]
                },
                "timestamp": 123456789
            }
        }
    }
    
    # Set a lower minimum profit threshold for the test
    engine.min_profit_percentage = 0.05
    
    # Mock trading fees (make them very low to ensure profit)
    engine.trading_fees_cache = {
        "BINANCE": {
            "BTC/USDT": {"maker": 0.0005, "taker": 0.0005}
        },
        "KUCOIN": {
            "BTC/USDT": {"maker": 0.0005, "taker": 0.0005}
        }
    }
    
    # Mock asyncio.sleep
    async def mock_sleep(*args, **kwargs):
        pass
    
    monkeypatch.setattr(asyncio, 'sleep', mock_sleep)
    
    # Run scan
    opportunities = await engine.scan_opportunities()
    
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
    # Setup order books cache with very close prices
    engine.order_books_cache = {
        "BTC/USDT": {
            "BINANCE": {
                "data": {
                    "bids": [[50000.0, 1.0], [49990.0, 2.0]],
                    "asks": [[50010.0, 1.0], [50020.0, 2.0]]
                },
                "timestamp": 123456789
            },
            "KUCOIN": {
                "data": {
                    "bids": [[50005.0, 1.0], [49995.0, 2.0]],
                    "asks": [[50015.0, 1.0], [50025.0, 2.0]]
                },
                "timestamp": 123456789
            }
        }
    }
    
    # Set min profit to 0.5%
    engine.min_profit_percentage = 0.5
    
    # Mock trading fees
    engine.trading_fees_cache = {
        "BINANCE": {
            "BTC/USDT": {"maker": 0.001, "taker": 0.001}
        },
        "KUCOIN": {
            "BTC/USDT": {"maker": 0.001, "taker": 0.001}
        }
    }
    
    # Mock asyncio.sleep
    async def mock_sleep(*args, **kwargs):
        pass
    
    monkeypatch.setattr(asyncio, 'sleep', mock_sleep)
    
    # Run scan
    opportunities = await engine.scan_opportunities()
    
    # There should be no opportunities
    assert len(opportunities) == 0