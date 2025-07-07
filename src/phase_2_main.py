#!/usr/bin/env python
"""
Arbitrage Bot - Phase 2 Main Entry Point

This script initializes the exchange connectors and arbitrage engine,
then starts the main scanning loop to identify arbitrage opportunities.
"""

import asyncio
import os
import requests
from dotenv import load_dotenv

from core.exchanges.binance import BinanceExchange
from core.exchanges.kucoin import KucoinExchange
from core.exchanges.ccxt import CcxtExchange
from core.arbitrage.engine import ArbitrageEngine
from utils.logger import Logger

# Telegram notification support
def send_telegram_message(bot_token, chat_id, message):
    """Send a message to a Telegram chat"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return None

async def main():
    """
    Main entry point for Phase 2 of the arbitrage bot.
    Initializes exchange connectors, sets up the arbitrage engine,
    and starts scanning for opportunities.
    """
    # Setup logger
    logger = Logger("main")
    logger.info("Starting Arbitrage Bot - Phase 2")
    
    # Load environment variables
    load_dotenv()
    
    # Telegram configuration
    telegram_enabled = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    
    if telegram_enabled and (not telegram_bot_token or not telegram_chat_id):
        logger.warning("Telegram notifications enabled but missing bot token or chat ID")
        telegram_enabled = False
    
    try:
        # Initialize exchange connectors
        exchanges = {}
        
        # Binance Exchange
        logger.info("Initializing Binance exchange connector")
        binance = BinanceExchange()
        exchanges["BINANCE"] = binance
        
        # KuCoin Exchange
        logger.info("Initializing KuCoin exchange connector")
        kucoin = KucoinExchange()
        exchanges["KUCOIN"] = kucoin
        
        # Additional exchanges through CCXT
        additional_exchanges = os.getenv("ADDITIONAL_EXCHANGES", "").split(",")
        for exchange_id in additional_exchanges:
            exchange_id = exchange_id.strip().lower()
            if exchange_id and exchange_id not in ['binance', 'kucoin']:  # Skip those we have native implementations for
                try:
                    logger.info(f"Initializing CCXT connector for {exchange_id}")
                    # Get API credentials from environment
                    api_key = os.getenv(f"{exchange_id.upper()}_API_KEY")
                    api_secret = os.getenv(f"{exchange_id.upper()}_API_SECRET")
                    
                    # Additional parameters that might be needed (like passphrase for KuCoin)
                    extra_params = {}
                    api_passphrase = os.getenv(f"{exchange_id.upper()}_API_PASSPHRASE")
                    if api_passphrase:
                        extra_params['password'] = api_passphrase
                    
                    ccxt_exchange = CcxtExchange(
                        exchange_id, 
                        api_key=api_key, 
                        api_secret=api_secret,
                        **extra_params
                    )
                    exchanges[exchange_id.upper()] = ccxt_exchange
                except Exception as e:
                    logger.error(f"Failed to initialize CCXT connector for {exchange_id}: {str(e)}")
        
        # Initialize arbitrage engine
        logger.info("Initializing Arbitrage Engine")
        engine = ArbitrageEngine(
            exchanges=exchanges,
            initial_capital=float(os.getenv("ARBITRAGE_INITIAL_CAPITAL", 1000.0)),
            min_profit_percentage=float(os.getenv("ARBITRAGE_MIN_PROFIT", 0.5)),
            max_slippage=float(os.getenv("ARBITRAGE_MAX_SLIPPAGE", 0.5)),
            target_symbols=os.getenv("ARBITRAGE_TARGET_SYMBOLS", "").split(",") if os.getenv("ARBITRAGE_TARGET_SYMBOLS") else None,
            start_rank=int(os.getenv("ARBITRAGE_START_RANK", "100")),
            end_rank=int(os.getenv("ARBITRAGE_END_RANK", "1500"))
        )
        
        # Hook for sending Telegram notifications on opportunities
        if telegram_enabled:
            # Create a custom callback for the engine to report opportunities
            async def opportunity_callback(opportunity):
                message = (
                    f"🔔 *Arbitrage Opportunity*\n\n"
                    f"*Symbol:* {opportunity['symbol']}\n"
                    f"*Buy from:* {opportunity['buy_exchange']} at {opportunity['buy_price']}\n"
                    f"*Sell on:* {opportunity['sell_exchange']} at {opportunity['sell_price']}\n"
                    f"*Potential profit:* ${opportunity['profit']:.2f} ({opportunity['profit_percentage']:.2f}%)\n"
                    f"*Buy slippage:* {opportunity['buy_slippage']:.2%}\n"
                    f"*Sell slippage:* {opportunity['sell_slippage']:.2%}"
                )
                send_telegram_message(telegram_bot_token, telegram_chat_id, message)
            
            # Set the callback in the engine
            engine.opportunity_callback = opportunity_callback
        
        # Start the engine
        logger.info("Starting arbitrage scanning")
        await engine.start(
            scan_interval=float(os.getenv("ARBITRAGE_SCAN_INTERVAL", 10.0))
        )
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise
    finally:
        logger.info("Shutting down Arbitrage Bot")
        

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 