"""
Arbitrage Engine - Identifies and executes arbitrage opportunities across exchanges.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import os
from dotenv import load_dotenv

from core.exchanges.abstract import ExchangeInterface
from utils.logger import Logger

class ArbitrageEngine:
    """Arbitrage engine that identifies profitable trading opportunities across exchanges."""
    
    def __init__(
        self,
        exchanges: Dict[str, ExchangeInterface],
        initial_capital: float = 1000.0,
        min_profit_percentage: float = 0.5,
        max_slippage: float = 0.5,
        target_symbols: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize the arbitrage engine.
        
        Args:
            exchanges: Dict of exchange_name -> exchange_instance
            initial_capital: Starting capital for calculations
            min_profit_percentage: Minimum profit threshold (%)
            max_slippage: Maximum acceptable slippage (%)
            target_symbols: List of trading pairs to monitor
        """
        self.exchanges = exchanges
        self.initial_capital = initial_capital
        self.min_profit_percentage = min_profit_percentage
        self.max_slippage = max_slippage
        self.target_symbols = target_symbols or []
        
        # Setup logger
        self.logger = Logger("arbitrage")
        
        # Cache for market data
        self.order_books_cache = {}
        self.trading_fees_cache = {}
        self.withdrawal_fees_cache = {}
        
        # Track failed symbols to avoid repeated errors
        self.failed_symbols = {}  # Exchange -> set of failed symbols
        self.last_fee_update = 0
        
        # Performance tracking
        self.opportunities_found = 0
        self.successful_trades = 0
        self.total_profit = 0.0
        
        # Callback for notifications
        self.opportunity_callback = None
        
        # Load configuration
        self._load_config()
        
    def _load_config(self):
        """Load configuration from environment variables."""
        load_dotenv()
        
        # Override defaults with environment variables if they exist
        self.initial_capital = float(os.getenv('ARBITRAGE_INITIAL_CAPITAL', self.initial_capital))
        self.min_profit_percentage = float(os.getenv('ARBITRAGE_MIN_PROFIT', self.min_profit_percentage))
        self.max_slippage = float(os.getenv('ARBITRAGE_MAX_SLIPPAGE', self.max_slippage))
        
        # Load target symbols if specified
        symbols_env = os.getenv('ARBITRAGE_TARGET_SYMBOLS')
        if symbols_env:
            self.target_symbols = symbols_env.split(',')
    
    async def start(self, scan_interval: float = 10.0):
        """
        Start the arbitrage engine to continuously scan for opportunities.
        
        Args:
            scan_interval: Time between scans in seconds
        """
        self.logger.info(f"Starting arbitrage engine with {len(self.exchanges)} exchanges and {len(self.target_symbols)} symbols")
        
        try:
            while True:
                start_time = time.time()
                
                # Get exchange info if we don't have symbols yet
                if not self.target_symbols:
                    await self._discover_tradable_symbols()
                
                # Update market data
                await self._update_market_data()
                
                # Scan for opportunities
                opportunities = await self.scan_opportunities()
                
                # Log and potentially execute opportunities
                if opportunities:
                    self.logger.info(f"Found {len(opportunities)} arbitrage opportunities")
                    for opp in opportunities:
                        self.logger.info(
                            f"Opportunity: {opp['symbol']} - "
                            f"Buy: {opp['buy_exchange']} @ {opp['buy_price']}, "
                            f"Sell: {opp['sell_exchange']} @ {opp['sell_price']}, "
                            f"Profit: {opp['profit_percentage']:.2f}%"
                        )
                        # TODO: Implement execution logic in Phase 3
                
                # Calculate time to wait until next scan
                elapsed = time.time() - start_time
                wait_time = max(0, scan_interval - elapsed)
                if wait_time > 0:
                    self.logger.debug(f"Waiting {wait_time:.2f}s until next scan")
                    await asyncio.sleep(wait_time)
                
        except KeyboardInterrupt:
            self.logger.info("Arbitrage engine stopped by user")
        except Exception as e:
            self.logger.error(f"Arbitrage engine error: {str(e)}")
            raise
    
    async def _discover_tradable_symbols(self):
        """Discover tradable symbols common across all exchanges with filtering."""
        all_symbols = {}
        
        # Fetch symbols from each exchange
        for exchange_name, exchange in self.exchanges.items():
            try:
                # Get exchange info with all available symbols
                exchange_info = await self._async_call(exchange.get_exchange_info)
                
                # Ensure we're getting a dictionary, not a string
                if not isinstance(exchange_info, dict):
                    self.logger.error(f"Invalid exchange_info format from {exchange_name}: {type(exchange_info)}")
                    continue
                    
                symbols = [s['symbol'] for s in exchange_info.get('symbols', []) 
                          if s.get('status') == 'TRADING']
                
                # Filter out problematic symbols and keep only major pairs
                filtered_symbols = []
                for symbol in symbols:
                    # Get base and quote currencies
                    if '/' in symbol:
                        base, quote = symbol.split('/')
                        
                        # Only accept major quote currencies and common base currencies
                        if (quote in ['USDT', 'BTC', 'ETH'] and 
                            not any(x in symbol for x in ['3L', '3S', 'UP', 'DOWN', 'BULL', 'BEAR'])):
                            filtered_symbols.append(symbol)
                
                all_symbols[exchange_name] = set(filtered_symbols)
                self.logger.info(f"Found {len(filtered_symbols)} filtered symbols for {exchange_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to get symbols for {exchange_name}: {str(e)}")
        
        # Find symbols available on all exchanges
        if all_symbols:
            if len(all_symbols) > 1:
                common_symbols = set.intersection(*all_symbols.values())
            else:
                # If we only have one exchange, use its symbols
                common_symbols = next(iter(all_symbols.values()))
                
            # Further limit to most common trading pairs for testing
            major_pairs = [
                "BTC/USDT", "ETH/USDT", "XRP/USDT", "LTC/USDT", "BNB/USDT", 
                "ADA/USDT", "DOT/USDT", "SOL/USDT", "DOGE/USDT", "MATIC/USDT"
            ]
            limited_symbols = [s for s in common_symbols if s in major_pairs]
            
            # Use limited symbols if available, otherwise top 20 from common symbols
            if limited_symbols:
                self.target_symbols = limited_symbols
            else:
                self.target_symbols = list(common_symbols)[:20]  # Limit to 20 pairs for testing
                
            self.logger.info(f"Discovered {len(self.target_symbols)} trading symbols to monitor")
        else:
            self.logger.warning("No symbols discovered from exchanges")
            # Fallback to some known common symbols
            self.target_symbols = ["BTC/USDT", "ETH/USDT"]
            self.logger.info(f"Using fallback symbols: {self.target_symbols}")
    
    async def _update_market_data(self):
        """Update all market data (order books, fees) asynchronously with better error handling."""
        tasks = []
        
        # Update order books for non-failed symbols
        for symbol in self.target_symbols:
            for exchange_name, exchange in self.exchanges.items():
                # Skip symbols that have failed for this exchange
                if (exchange_name in self.failed_symbols and 
                    symbol in self.failed_symbols[exchange_name]):
                    continue
                    
                tasks.append(self._async_update_order_book(exchange_name, exchange, symbol))
        
        # Update trading fees if not cached - don't try too frequently
        if not self.trading_fees_cache or time.time() - self.last_fee_update > 3600:
            self.last_fee_update = time.time()
            for exchange_name, exchange in self.exchanges.items():
                tasks.append(self._async_update_trading_fees(exchange_name, exchange))
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _async_update_order_book(self, exchange_name: str, exchange: ExchangeInterface, symbol: str):
        """Fetch and cache order book for a symbol on an exchange with better error handling."""
        try:
            order_book = await self._async_call(exchange.get_order_book, symbol)
            
            # Check if the order book is valid (has bids and asks)
            if not order_book.get('bids') or not order_book.get('asks'):
                # Empty order book, log but don't count as error
                self.logger.debug(f"Empty order book for {exchange_name} {symbol}")
                return
                
            # Cache the result with timestamp
            if symbol not in self.order_books_cache:
                self.order_books_cache[symbol] = {}
            
            self.order_books_cache[symbol][exchange_name] = {
                'data': order_book,
                'timestamp': time.time()
            }
        except Exception as e:
            # Track failed symbols
            if exchange_name not in self.failed_symbols:
                self.failed_symbols[exchange_name] = set()
                
            self.failed_symbols[exchange_name].add(symbol)
            
            # Only log the error the first time it occurs
            if len(self.failed_symbols[exchange_name]) <= 10:
                self.logger.error(f"Failed to update order book for {exchange_name} {symbol}: {str(e)}")
            elif len(self.failed_symbols[exchange_name]) == 11:
                self.logger.warning(f"Suppressing further order book errors for {exchange_name} (too many to log)")
    
    async def _async_update_trading_fees(self, exchange_name: str, exchange: ExchangeInterface):
        """Fetch and cache trading fees for an exchange."""
        try:
            fees = await self._async_call(exchange.get_trading_fees)
            if fees:  # Only update if we got a valid response
                self.trading_fees_cache[exchange_name] = fees
        except Exception as e:
            self.logger.error(f"Failed to update trading fees for {exchange_name}: {str(e)}")
    
    async def _async_call(self, func, *args, **kwargs):
        """Helper to call synchronous exchange methods asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    
    def estimate_slippage(self, order_book: Dict[str, Any], amount: float, side: str = 'buy') -> float:
        """
        Estimate slippage based on the order book depth.
        
        Args:
            order_book: Order book data with bids and asks
            amount: Amount to buy/sell
            side: 'buy' or 'sell'
            
        Returns:
            Estimated slippage as a percentage
        """
        total_amount = 0
        weighted_price = 0
        target_amount = amount

        if side == 'buy':
            for price, size in order_book.get('asks', []):
                if total_amount < target_amount:
                    fill_amount = min(size, target_amount - total_amount)
                    total_amount += fill_amount
                    weighted_price += price * fill_amount
                else:
                    break
                    
            if total_amount > 0:
                average_price = weighted_price / total_amount
                best_ask = order_book['asks'][0][0] if order_book.get('asks') else 0
                if best_ask > 0:
                    slippage = (average_price - best_ask) / best_ask
                    return slippage
        else:  # sell
            for price, size in order_book.get('bids', []):
                if total_amount < target_amount:
                    fill_amount = min(size, target_amount - total_amount)
                    total_amount += fill_amount
                    weighted_price += price * fill_amount
                else:
                    break
                    
            if total_amount > 0:
                average_price = weighted_price / total_amount
                best_bid = order_book['bids'][0][0] if order_book.get('bids') else 0
                if best_bid > 0:
                    slippage = (best_bid - average_price) / best_bid
                    return slippage
                    
        return 0
    
    async def calculate_potential_profit(
        self, 
        symbol: str,
        buy_exchange: str, 
        sell_exchange: str,
        amount: float
    ) -> Tuple[float, float, float, float]:
        """
        Calculate potential profit for an arbitrage opportunity.
        
        Args:
            symbol: Trading pair symbol
            buy_exchange: Exchange to buy from
            sell_exchange: Exchange to sell on
            amount: Amount to trade in quote currency
            
        Returns:
            (profit, profit_percentage, buy_slippage, sell_slippage)
        """
        # Get cached order books
        if (symbol not in self.order_books_cache or
            buy_exchange not in self.order_books_cache[symbol] or
            sell_exchange not in self.order_books_cache[symbol]):
            return 0, 0, 0, 0
            
        buy_order_book = self.order_books_cache[symbol][buy_exchange]['data']
        sell_order_book = self.order_books_cache[symbol][sell_exchange]['data']
        
        # Get best prices
        if not buy_order_book.get('asks') or not sell_order_book.get('bids'):
            return 0, 0, 0, 0
            
        buy_price = buy_order_book['asks'][0][0]
        sell_price = sell_order_book['bids'][0][0]
        
        # Estimate slippage
        buy_slippage = self.estimate_slippage(buy_order_book, amount / buy_price, 'buy')
        sell_slippage = self.estimate_slippage(sell_order_book, amount / buy_price, 'sell')
        
        # Get trading fees
        buy_fee_rate = 0.001  # Default
        sell_fee_rate = 0.001  # Default
        
        if buy_exchange in self.trading_fees_cache:
            fees = self.trading_fees_cache[buy_exchange]
            if symbol in fees:
                buy_fee_rate = fees[symbol].get('taker', 0.001)
                
        if sell_exchange in self.trading_fees_cache:
            fees = self.trading_fees_cache[sell_exchange]
            if symbol in fees:
                sell_fee_rate = fees[symbol].get('maker', 0.001)
        
        # Adjust prices for slippage
        adjusted_buy_price = buy_price * (1 + buy_slippage)
        adjusted_sell_price = sell_price * (1 - sell_slippage)
        
        # Calculate amounts
        buy_fee = amount * buy_fee_rate
        coins_bought = (amount - buy_fee) / adjusted_buy_price
        
        # TODO: Account for withdrawal fees in future phases
        # For now, assuming direct transfer
        coins_after_transfer = coins_bought  
        
        # Calculate sell proceeds
        sale_amount_before_fee = coins_after_transfer * adjusted_sell_price
        sell_fee = sale_amount_before_fee * sell_fee_rate
        sale_amount = sale_amount_before_fee - sell_fee
        
        # Calculate profit
        profit = sale_amount - amount
        profit_percentage = (profit / amount) * 100
        
        return profit, profit_percentage, buy_slippage, sell_slippage
    
    async def scan_opportunities(self) -> List[Dict[str, Any]]:
        """
        Scan for arbitrage opportunities across all exchanges and symbols.
        
        Returns:
            List of opportunity dictionaries
        """
        opportunities = []
        
        for symbol in self.target_symbols:
            # Skip if we don't have order book data
            if symbol not in self.order_books_cache:
                continue
                
            # Get exchanges with order books for this symbol
            exchange_names = list(self.order_books_cache[symbol].keys())
            
            # Compare all exchange pairs
            for i in range(len(exchange_names)):
                for j in range(i + 1, len(exchange_names)):
                    buy_exchange = exchange_names[i]
                    sell_exchange = exchange_names[j]
                    
                    # Get order books
                    buy_book = self.order_books_cache[symbol][buy_exchange]['data']
                    sell_book = self.order_books_cache[symbol][sell_exchange]['data']
                    
                    # Skip if no asks/bids
                    if not buy_book.get('asks') or not sell_book.get('bids'):
                        continue
                        
                    # Get best prices
                    buy_price = buy_book['asks'][0][0]
                    sell_price = sell_book['bids'][0][0]
                    
                    # Quick check if there's potential profit
                    if sell_price <= buy_price:
                        # Check reverse direction
                        buy_price_reverse = sell_book['asks'][0][0]
                        sell_price_reverse = buy_book['bids'][0][0]
                        
                        if sell_price_reverse <= buy_price_reverse:
                            # No opportunity in either direction
                            continue
                        else:
                            # Swap exchanges for reverse direction
                            buy_exchange, sell_exchange = sell_exchange, buy_exchange
                            buy_price, sell_price = buy_price_reverse, sell_price_reverse
                    
                    # Calculate detailed profit with fees and slippage
                    profit, profit_percentage, buy_slippage, sell_slippage = await self.calculate_potential_profit(
                        symbol, buy_exchange, sell_exchange, self.initial_capital
                    )
                    
                    # Check if profitable enough and slippage is acceptable
                    if (profit_percentage >= self.min_profit_percentage and 
                        buy_slippage <= self.max_slippage/100 and 
                        sell_slippage <= self.max_slippage/100):
                        
                        opportunity = {
                            'symbol': symbol,
                            'buy_exchange': buy_exchange,
                            'sell_exchange': sell_exchange,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'profit': profit,
                            'profit_percentage': profit_percentage,
                            'buy_slippage': buy_slippage,
                            'sell_slippage': sell_slippage,
                            'timestamp': time.time()
                        }
                        
                        opportunities.append(opportunity)
                        
                        # Increment counter for statistics
                        self.opportunities_found += 1
                        
                        # Call opportunity callback if defined
                        if self.opportunity_callback:
                            try:
                                asyncio.create_task(self.opportunity_callback(opportunity))
                            except Exception as e:
                                self.logger.error(f"Error in opportunity callback: {str(e)}")
        
        return opportunities
    
    async def execute_arbitrage(self, opportunity: Dict[str, Any]) -> bool:
        """
        Execute an arbitrage opportunity by placing coordinated buy/sell orders.
        
        NOTE: This is a placeholder for Phase 3 implementation.
        
        Args:
            opportunity: Opportunity dict with execution details
            
        Returns:
            Success status
        """
        self.logger.info(f"Executing arbitrage: {opportunity['symbol']} - Buy on {opportunity['buy_exchange']}, Sell on {opportunity['sell_exchange']}")
        self.logger.warning("Arbitrage execution not implemented in Phase 2")
        return False
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a performance report.
        
        Returns:
            Dict with performance metrics
        """
        return {
            'opportunities_found': self.opportunities_found,
            'successful_trades': self.successful_trades,
            'total_profit': self.total_profit,
            'success_rate': self.successful_trades / max(1, self.opportunities_found) * 100,
            'active_exchanges': list(self.exchanges.keys()),
            'monitored_symbols': len(self.target_symbols)
        } 