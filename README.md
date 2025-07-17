# Cryptocurrency Arbitrage Bot

## Overview
A fully-featured, asynchronous cryptocurrency arbitrage scanner that identifies price discrepancies across multiple exchanges in real-time.  
Built with Python 3.11+, [Poetry](https://python-poetry.org/) for dependency management, and [CCXT](https://github.com/ccxt/ccxt) for unified exchange access, the bot ships with native high-performance connectors for **Binance** and **KuCoin** and can automatically load any other CCXT-supported exchange.

## Features
*  Modular exchange layer – add a new exchange by dropping a connector class or naming it in `ADDITIONAL_EXCHANGES`.
*  Non-blocking I/O with `asyncio` + `aiohttp` for low-latency order-book pulls.
*  Profit calculation that accounts for trading fees, configurable slippage, and (optionally) withdrawal fees.
*  Colourised console logging **and** persistent log files with runtime-selectable log level (`LOG_LEVEL`).
*  Optional Telegram notifications for every detected opportunity.
*  Zero-touch configuration via `.env` – no code changes required for most settings.
*  Pytest test-suite included.

## Requirements
* Python 3.11 or later
* Poetry >= 1.5 (handles virtual-env creation automatically)

> **Note**  
> You do **not** need to create a virtual environment manually; running any `poetry` command will generate and manage an isolated environment for the project. If you prefer an interactive shell inside that venv, run `poetry shell`.

## Installation
```bash
# Clone repository
git clone https://github.com/yourusername/arbitrage-bot.git
cd arbitrage-bot

# Install Poetry if missing
pip install --user poetry

# Install dependencies (creates the venv on first run)
poetry install
```

## Configuration
Create a `.env` file in the project root (same directory as `pyproject.toml`) and populate it with your desired settings. Only the exchange API keys you actually use are required.

```dotenv
# --- Exchange API keys ------------------------------------------------------
BINANCE_API_KEY=xxxxxxxxxxxxxxxxxxxx
BINANCE_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

KUCOIN_API_KEY=xxxxxxxxxxxxxxxxxxxx
KUCOIN_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
KUCOIN_API_PASSPHRASE=xxxxxxxxxxxxxxxxxxxx

# Automatically load extra exchanges through CCXT (comma-separated id list)
ADDITIONAL_EXCHANGES=huobi,bitget
HUOBI_API_KEY=...
HUOBI_API_SECRET=...
BITGET_API_KEY=...
BITGET_API_SECRET=...
BITGET_API_PASSPHRASE=...

# --- Arbitrage engine settings ---------------------------------------------
ARBITRAGE_INITIAL_CAPITAL=1000          # USD amount used for profit projection
ARBITRAGE_MIN_PROFIT=0.5                # % profit threshold that triggers alert
ARBITRAGE_MAX_SLIPPAGE=0.5              # % max slippage tolerated per leg
ARBITRAGE_SCAN_INTERVAL=10              # Seconds between scans
# Leave empty to auto-discover symbols via CoinMarketCap rank range
ARBITRAGE_TARGET_SYMBOLS=BTC/USDT,ETH/USDT,XRP/USDT
ARBITRAGE_START_RANK=100                # CMC rank range for auto discovery
ARBITRAGE_END_RANK=1500

# --- Logging & notifications -----------------------------------------------
LOG_LEVEL=INFO                          # DEBUG, INFO, WARNING, ERROR or numeric
TELEGRAM_ENABLED=true                   # Enable/disable Telegram alerts
TELEGRAM_BOT_TOKEN=7924736...           # Your bot token
TELEGRAM_CHAT_ID=123456789              # Chat/channel/user id that receives alerts
```

All variables have sensible defaults; omit any you don’t care to tweak.

## Running the Bot
```bash
# Activate the virtual environment (optional but handy)
poetry shell

# Start scanning (Ctrl-C to stop)
python src/main.py
# or, without entering the shell
poetry run python src/main.py
```

When a profitable spread above `ARBITRAGE_MIN_PROFIT` is detected the bot logs the details and, if enabled, sends a Telegram message.

### Log Files
Log output is written to human-readable files under `logs/`:
```
logs/
├── arbitrage/arbitrage.log   # Engine activity, opportunity summaries
├── exchanges/exchange.log    # Low-level exchange requests/responses
├── trades/trades.log         # Reserved for future trade execution records
└── main/main.log             # Start-up, shutdown and top-level errors
```
Adjust verbosity globally via the `LOG_LEVEL` env var.

## Project Layout (abridged)
```
src/
├── api/                  # CoinMarketCap client
├── core/
│   ├── arbitrage/        # Engine & helpers
│   ├── exchanges/        # Exchange connectors
│   │   ├── abstract/     # Base classes / interface
│   │   ├── binance/      # Native Binance implementation
│   │   ├── kucoin/       # Native KuCoin implementation
|   |   └── ccxt/         # Ccxt connector
│   └── enums/            # HTTP method enum, etc.
├── scripts/              # Scripts for handling stats
├── utils/                # Logger, timezone helpers
├── main.py               # Application entry-point
└── tests/                # Tests

```

## Testing
```bash
poetry run pytest      # run all unit & integration tests
```

## Extending
1. **Add a new connector** – subclass `BaseExchange`, implement required methods, and (optionally) a response normaliser.
2. **Point the engine to it** – either add your class in `src/main.py` or simply list its CCXT id in `ADDITIONAL_EXCHANGES` if you’re happy with the generic wrapper.
3. **Create tests** – drop new test files under `tests/` and run the suite.

## Security Notes
* API keys are **never** committed; they live solely in your `.env` file or CI secrets.
* Use read-only / IP-restricted keys when possible.
* The bot only **monitors** opportunities – no real orders are placed unless you extend `execute_arbitrage()` with execution logic.

## Disclaimer
This software is provided **for educational and research purposes only**. Trading cryptocurrencies carries significant risk. The authors make no warranties of profitability and accept no liability for financial loss.

## License
MIT – see `LICENSE` for full text.
