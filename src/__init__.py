"""
Arbitrage Bot - A cryptocurrency arbitrage trading bot.
"""

from .core import (
    ExchangeInterface,
    BaseExchange,
    BinanceExchange,
    KuCoinExchange,
    CCXTWrapper,
    ArbitrageEngine
)
from .api import CoinGeckoClient
from .models import Coin, Coins_map
from .utils.logging import Logger

__all__ = [
    # Core components
    'ExchangeInterface',
    'BaseExchange',
    'BinanceExchange',
    'KuCoinExchange',
    'CCXTWrapper',
    'ArbitrageEngine',
    
    # API clients
    'CoinGeckoClient',
    
    # Models
    'Coin',
    'Coins_map',
    
    # Utilities
    'Logger'
]
