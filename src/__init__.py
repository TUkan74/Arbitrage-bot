"""
Arbitrage Bot - A cryptocurrency arbitrage trading bot.
"""

from .core import (
    ExchangeInterface,
    BaseExchange,
    BinanceExchange,
    BinanceNormalizer,
    KucoinExchange,
    KucoinNormalizer,
    HttpMethod
    
)
from .api import CoinGeckoClient
from .models import Coin, Coins_map
from .utils import Logger

__all__ = [
    # Core components
    'ExchangeInterface',
    'BaseExchange',
    'BinanceExchange',
    'BinanceNormalizer',
    'KucoinExchange',
    'KucoinNormalizer',
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
