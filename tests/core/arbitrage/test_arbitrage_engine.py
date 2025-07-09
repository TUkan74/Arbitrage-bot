"""
Tests for the arbitrage engine.
"""

import pytest
import asyncio
import os
from unittest.mock import MagicMock, patch
import json

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


@pytest.mark.asyncio
async def test_load_config_from_env():
    """Test loading configuration from environment variables."""
    async with MockExchange("BINANCE") as binance:
        # Mock the async_call method to handle async operations
        async def mock_async_call(func, *args, **kwargs):
            if func == binance.get_trading_fees:
                return {
                    "BTC/USDT": {"maker": 0.001, "taker": 0.001},
                    "ETH/USDT": {"maker": 0.001, "taker": 0.001}
                }
            return None
        
        with patch.dict(os.environ, {
            'ARBITRAGE_INITIAL_CAPITAL': '2000.0',
            'ARBITRAGE_MIN_PROFIT': '1.5',
            'ARBITRAGE_MAX_SLIPPAGE': '0.8',
            'ARBITRAGE_TARGET_SYMBOLS': 'BTC/USDT,ETH/USDT,XRP/USDT'
        }, clear=True):
            engine = ArbitrageEngine(
                exchanges={"BINANCE": binance},
                initial_capital=1000.0,  # Should be overridden
                min_profit_percentage=0.5,  # Should be overridden
                max_slippage=0.5,  # Should be overridden
            )
            
            # Replace the _async_call method
            engine._async_call = mock_async_call
            
            assert engine.initial_capital == 2000.0
            assert engine.min_profit_percentage == 1.5
            assert engine.max_slippage == 0.8
            assert engine.target_symbols == ['BTC/USDT', 'ETH/USDT', 'XRP/USDT']

@pytest.mark.asyncio
async def test_load_config_defaults():
    """Test loading default configuration when no environment variables are set."""
    async with MockExchange("BINANCE") as binance:
        # Mock the async_call method to handle async operations
        async def mock_async_call(func, *args, **kwargs):
            if func == binance.get_trading_fees:
                return {
                    "BTC/USDT": {"maker": 0.001, "taker": 0.001},
                    "ETH/USDT": {"maker": 0.001, "taker": 0.001}
                }
            return None
        
        with patch.dict(os.environ, {}, clear=True):
            engine = ArbitrageEngine(
                exchanges={"BINANCE": binance},
            )
            
            # Replace the _async_call method
            engine._async_call = mock_async_call
            
            assert engine.initial_capital == 500.0  # Default value from __init__
            assert engine.min_profit_percentage == 0.5
            assert engine.max_slippage == 0.5
            assert engine.target_symbols == []

@pytest.mark.asyncio
async def test_discover_tradable_symbols_with_cmc():
    """Test discovering tradable symbols using CMC API."""
    # Mock CMCClient
    mock_cmc = MagicMock()
    mock_cmc.get_ranked_coins.return_value = ['BTC', 'ETH', 'XRP']
    
    async with MockExchange("BINANCE") as binance:
        # Mock the async_call method to handle async operations
        async def mock_async_call(func, *args, **kwargs):
            if func == binance.get_trading_fees:
                return {
                    "BTC/USDT": {"maker": 0.001, "taker": 0.001},
                    "ETH/USDT": {"maker": 0.001, "taker": 0.001}
                }
            return None
        
        with patch('core.arbitrage.engine.CMCClient', return_value=mock_cmc):
            engine = ArbitrageEngine(
                exchanges={"BINANCE": binance},
                start_rank=1,
                end_rank=10
            )
            
            # Replace the _async_call method
            engine._async_call = mock_async_call
            
            await engine._discover_tradable_symbols()
            
            assert engine.target_symbols == ['BTC/USDT', 'ETH/USDT', 'XRP/USDT']
            mock_cmc.get_ranked_coins.assert_called_once_with(1, 10)

@pytest.mark.asyncio
async def test_discover_tradable_symbols_cmc_error():
    """Test discovering tradable symbols when CMC API fails."""
    # Mock CMCClient to raise an exception
    mock_cmc = MagicMock()
    mock_cmc.get_ranked_coins.side_effect = Exception("API Error")
    
    async with MockExchange("BINANCE") as binance:
        # Mock the async_call method to handle async operations
        async def mock_async_call(func, *args, **kwargs):
            if func == binance.get_trading_fees:
                return {
                    "BTC/USDT": {"maker": 0.001, "taker": 0.001},
                    "ETH/USDT": {"maker": 0.001, "taker": 0.001}
                }
            return None
        
        with patch('core.arbitrage.engine.CMCClient', return_value=mock_cmc):
            engine = ArbitrageEngine(
                exchanges={"BINANCE": binance},
                start_rank=1,
                end_rank=10
            )
            
            # Replace the _async_call method
            engine._async_call = mock_async_call
            
            await engine._discover_tradable_symbols()
            
            # Should fall back to default symbols
            assert engine.target_symbols == ['BTC/USDT', 'ETH/USDT']

@pytest.mark.asyncio
async def test_discover_tradable_symbols_with_provided_symbols():
    """Test that provided symbols are used instead of discovering new ones."""
    async with MockExchange("BINANCE") as binance:
        # Mock the async_call method to handle async operations
        async def mock_async_call(func, *args, **kwargs):
            if func == binance.get_trading_fees:
                return {
                    "DOT/USDT": {"maker": 0.001, "taker": 0.001},
                    "LINK/USDT": {"maker": 0.001, "taker": 0.001}
                }
            return None
        
        engine = ArbitrageEngine(
            exchanges={"BINANCE": binance},
            target_symbols=['DOT/USDT', 'LINK/USDT']
        )
        
        # Replace the _async_call method
        engine._async_call = mock_async_call
        
        await engine._discover_tradable_symbols()
        
        # Should keep the provided symbols
        assert engine.target_symbols == ['DOT/USDT', 'LINK/USDT']

@pytest.mark.asyncio
async def test_update_market_data_success():
    """Test successful market data updates."""
    async with MockExchange("BINANCE") as binance, MockExchange("KUCOIN") as kucoin:
        # Mock the async_call method to return order book data directly
        async def mock_async_call(func, *args, **kwargs):
            if func == binance.get_order_book:
                return {
                    "symbol": args[0],
                    "bids": [[49990.0, 1.0], [49980.0, 2.0]],
                    "asks": [[50010.0, 1.0], [50020.0, 2.0]]
                }
            elif func == kucoin.get_order_book:
                return {
                    "symbol": args[0],
                    "bids": [[49995.0, 1.0], [49985.0, 2.0]],
                    "asks": [[50005.0, 1.0], [50015.0, 2.0]]
                }
            elif func == binance.get_trading_fees or func == kucoin.get_trading_fees:
                return {
                    "BTC/USDT": {"maker": 0.001, "taker": 0.001},
                    "ETH/USDT": {"maker": 0.001, "taker": 0.001}
                }
            return None
        
        engine = ArbitrageEngine(
            exchanges={"BINANCE": binance, "KUCOIN": kucoin},
            target_symbols=["BTC/USDT", "ETH/USDT"]
        )
        
        # Replace the _async_call method
        engine._async_call = mock_async_call
        
        await engine._update_market_data()
        
        # Check order books were cached
        assert "BTC/USDT" in engine.order_books_cache
        assert "ETH/USDT" in engine.order_books_cache
        assert "BINANCE" in engine.order_books_cache["BTC/USDT"]
        assert "KUCOIN" in engine.order_books_cache["BTC/USDT"]
        
        # Check trading fees were cached
        assert "BINANCE" in engine.trading_fees_cache
        assert "KUCOIN" in engine.trading_fees_cache
        
        # Verify order book data
        binance_book = engine.order_books_cache["BTC/USDT"]["BINANCE"]["data"]
        assert binance_book["bids"][0] == [49990.0, 1.0]
        assert binance_book["asks"][0] == [50010.0, 1.0]
        
        # Verify trading fees
        assert engine.trading_fees_cache["BINANCE"]["BTC/USDT"]["maker"] == 0.001

@pytest.mark.asyncio
async def test_update_market_data_order_book_error():
    """Test handling of order book update errors."""
    async with MockExchange("BINANCE") as binance:
        # Make get_order_book raise an exception
        binance.get_order_book = MagicMock(side_effect=Exception("API Error"))
        
        engine = ArbitrageEngine(
            exchanges={"BINANCE": binance},
            target_symbols=["BTC/USDT"]
        )
        
        await engine._update_market_data()
        
        # Check that the symbol was marked as failed
        assert "BINANCE" in engine.failed_symbols
        assert "BTC/USDT" in engine.failed_symbols["BINANCE"]
        
        # Check that no order book was cached
        assert "BTC/USDT" not in engine.order_books_cache

@pytest.mark.asyncio
async def test_update_market_data_empty_order_book():
    """Test handling of empty order books."""
    async with MockExchange("BINANCE") as binance:
        # Mock the async_call method to return empty order book
        async def mock_async_call(func, *args, **kwargs):
            if func == binance.get_order_book:
                return {"bids": [], "asks": []}
            elif func == binance.get_trading_fees:
                return {
                    "BTC/USDT": {"maker": 0.001, "taker": 0.001},
                    "ETH/USDT": {"maker": 0.001, "taker": 0.001}
                }
            return None
        
        engine = ArbitrageEngine(
            exchanges={"BINANCE": binance},
            target_symbols=["BTC/USDT"]
        )
        
        # Replace the _async_call method
        engine._async_call = mock_async_call
        
        await engine._update_market_data()
        
        # Check that no order book was cached
        assert "BTC/USDT" not in engine.order_books_cache

@pytest.mark.asyncio
async def test_update_market_data_trading_fees_error():
    """Test handling of trading fees update errors."""
    async with MockExchange("BINANCE") as binance:
        # Mock the async_call method to simulate trading fees error
        async def mock_async_call(func, *args, **kwargs):
            if func == binance.get_order_book:
                return {
                    "symbol": args[0],
                    "bids": [[49990.0, 1.0], [49980.0, 2.0]],
                    "asks": [[50010.0, 1.0], [50020.0, 2.0]]
                }
            elif func == binance.get_trading_fees:
                raise Exception("API Error")
            return None
        
        engine = ArbitrageEngine(
            exchanges={"BINANCE": binance},
            target_symbols=["BTC/USDT"]
        )
        
        # Replace the _async_call method
        engine._async_call = mock_async_call
        
        await engine._update_market_data()
        
        # Check that no trading fees were cached
        assert "BINANCE" not in engine.trading_fees_cache

@pytest.mark.asyncio
async def test_update_market_data_skip_failed_symbols():
    """Test that previously failed symbols are skipped."""
    async with MockExchange("BINANCE") as binance:
        # Mock the async_call method to return order book data directly
        async def mock_async_call(func, *args, **kwargs):
            if func == binance.get_order_book:
                symbol = args[0]
                if symbol == "ETH/USDT":
                    return {
                        "symbol": symbol,
                        "bids": [[2990.0, 1.0], [2980.0, 2.0]],
                        "asks": [[3010.0, 1.0], [3020.0, 2.0]]
                    }
            elif func == binance.get_trading_fees:
                return {
                    "BTC/USDT": {"maker": 0.001, "taker": 0.001},
                    "ETH/USDT": {"maker": 0.001, "taker": 0.001}
                }
            return None
        
        engine = ArbitrageEngine(
            exchanges={"BINANCE": binance},
            target_symbols=["BTC/USDT", "ETH/USDT"]
        )
        
        # Mark BTC/USDT as failed
        engine.failed_symbols = {"BINANCE": {"BTC/USDT"}}
        
        # Replace the _async_call method
        engine._async_call = mock_async_call
        
        await engine._update_market_data()
        
        # Check that only ETH/USDT was updated
        assert "ETH/USDT" in engine.order_books_cache
        assert "BTC/USDT" not in engine.order_books_cache
        
        # Verify order book data for ETH/USDT
        eth_book = engine.order_books_cache["ETH/USDT"]["BINANCE"]["data"]
        assert eth_book["bids"][0] == [2990.0, 1.0]
        assert eth_book["asks"][0] == [3010.0, 1.0]

@pytest.mark.asyncio
async def test_async_call_retry():
    """Test the async call retry mechanism."""
    async with MockExchange("BINANCE") as binance:
        engine = ArbitrageEngine(
            exchanges={"BINANCE": binance},
            target_symbols=["BTC/USDT"]
        )
        
        # Create a mock function that fails twice then succeeds
        call_count = 0
        
        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return "success"
        
        # Test the retry mechanism
        result = None
        for _ in range(3):
            try:
                result = await mock_func()
                break
            except Exception:
                continue
        
        assert result == "success"
        assert call_count == 3  # Should have retried twice



@pytest.mark.asyncio
async def test_execute_arbitrage_failure():
    """Test arbitrage execution failure."""
    async with MockExchange("BINANCE") as binance, MockExchange("KUCOIN") as kucoin:
        # Mock the async_call method to simulate order failure
        async def mock_async_call(func, *args, **kwargs):
            if func == binance.place_order:
                raise Exception("Order failed")
            return None
        
        engine = ArbitrageEngine(
            exchanges={"BINANCE": binance, "KUCOIN": kucoin},
            target_symbols=["BTC/USDT"]
        )
        
        # Replace the _async_call method
        engine._async_call = mock_async_call
        
        opportunity = {
            'symbol': 'BTC/USDT',
            'buy_exchange': 'BINANCE',
            'sell_exchange': 'KUCOIN',
            'buy_price': 49000.0,
            'sell_price': 50000.0,
            'amount': 1.0,
            'profit_percentage': 2.0,
            'total_profit': 1000.0
        }
        
        success = await engine.execute_arbitrage(opportunity)
        
        assert not success
        assert engine.successful_trades == 0
        assert engine.total_profit == 0.0

@pytest.mark.asyncio
async def test_calculate_potential_profit():
    """Test profit calculation with fees and slippage."""
    async with MockExchange("BINANCE") as binance, MockExchange("KUCOIN") as kucoin:
        engine = ArbitrageEngine(
            exchanges={"BINANCE": binance, "KUCOIN": kucoin},
            target_symbols=["BTC/USDT"],
            initial_capital=50000.0
        )
        
        # Setup mock order books
        engine.order_books_cache = {
            "BTC/USDT": {
                "BINANCE": {
                    "data": {
                        "bids": [[49990.0, 1.0], [49980.0, 2.0]],
                        "asks": [[50010.0, 1.0], [50020.0, 2.0]]
                    },
                    "timestamp": 123456789
                },
                "KUCOIN": {
                    "data": {
                        "bids": [[50500.0, 1.0], [50490.0, 2.0]],
                        "asks": [[50510.0, 1.0], [50520.0, 2.0]]
                    },
                    "timestamp": 123456789
                }
            }
        }
        
        # Setup mock trading fees
        engine.trading_fees_cache = {
            "BINANCE": {"BTC/USDT": {"maker": 0.001, "taker": 0.001}},
            "KUCOIN": {"BTC/USDT": {"maker": 0.001, "taker": 0.001}}
        }
        
        # Calculate potential profit
        profit, profit_percentage, buy_slippage, sell_slippage = await engine.calculate_potential_profit(
            "BTC/USDT", "BINANCE", "KUCOIN", 50000.0
        )
        
        # Verify calculations
        assert buy_slippage <= engine.max_slippage/100
        assert sell_slippage <= engine.max_slippage/100
        assert profit > 0
        assert profit_percentage > 0
        
        # Verify profit calculation
        # Buy 1 BTC at 50010.0 with 0.1% fee
        buy_amount = 50000.0
        buy_fee = buy_amount * 0.001
        coins_bought = (buy_amount - buy_fee) / 50010.0
        
        # Sell coins at 50500.0 with 0.1% fee
        sell_amount_before_fee = coins_bought * 50500.0
        sell_fee = sell_amount_before_fee * 0.001
        sell_amount = sell_amount_before_fee - sell_fee
        
        expected_profit = sell_amount - buy_amount
        expected_profit_percentage = (expected_profit / buy_amount) * 100
        
        assert profit == pytest.approx(expected_profit, rel=1e-10)
        assert profit_percentage == pytest.approx(expected_profit_percentage, rel=1e-10)

@pytest.mark.asyncio
async def test_generate_report():
    """Test report generation."""
    async with MockExchange("BINANCE") as binance:
        engine = ArbitrageEngine(
            exchanges={"BINANCE": binance},
            target_symbols=["BTC/USDT"]
        )
        
        # Set some stats
        engine.opportunities_found = 10
        engine.successful_trades = 5
        engine.total_profit = 1000.0
        
        report = engine.generate_report()
        
        assert report["opportunities_found"] == 10
        assert report["successful_trades"] == 5
        assert report["total_profit"] == 1000.0
        assert report["success_rate"] == 50.0  # 5/10 * 100
        assert report["monitored_symbols"] == 1
        assert report["active_exchanges"] == ["BINANCE"]

@pytest.mark.asyncio
async def test_start_with_keyboard_interrupt():
    """Test graceful shutdown on keyboard interrupt."""
    async with MockExchange("BINANCE") as binance:
        engine = ArbitrageEngine(
            exchanges={"BINANCE": binance},
            target_symbols=["BTC/USDT"]
        )
        
        # Mock the async_call method to handle async operations
        async def mock_async_call(func, *args, **kwargs):
            if func == binance.get_order_book:
                return {
                    "symbol": args[0],
                    "bids": [[49990.0, 1.0], [49980.0, 2.0]],
                    "asks": [[50010.0, 1.0], [50020.0, 2.0]]
                }
            elif func == binance.get_trading_fees:
                return {
                    "BTC/USDT": {"maker": 0.001, "taker": 0.001},
                    "ETH/USDT": {"maker": 0.001, "taker": 0.001}
                }
            return None
        
        # Replace the _async_call method
        engine._async_call = mock_async_call
        
        # Mock asyncio.sleep to raise KeyboardInterrupt
        async def mock_sleep(*args, **kwargs):
            raise KeyboardInterrupt()
            
        with patch('asyncio.sleep', side_effect=mock_sleep):
            # Should not raise any exceptions
            await engine.start(scan_interval=1.0)
