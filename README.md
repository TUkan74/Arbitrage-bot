# Cryptocurrency Arbitrage Bot Documentation

## Project Overview
This project involves building a cryptocurrency arbitrage bot that identifies and exploits price discrepancies across various cryptocurrency exchanges. The project aims to create a semi-automated bot that will initially serve as a semestral project and later be possibly expanded into a bachelor's thesis, with a focus on improving performance and exploring decentralized finance (DeFi) opportunities.


## Table of Contents
- [Project Scope](#project-scope)
- [Installation and Setup](#installation-and-setup)
- [Dependencies](#dependencies)
- [Configuration](#configuration)
- [Usage](#usage)
- [Arbitrage Strategies](#arbitrage-strategies)
- [Technical Considerations](#technical-considerations)
- [Potential Future Work](#potential-future-work)
- [License](#license)

## Project Scope
- **Semestral Work**: The bot will initially use centralized exchanges (CEXs) such as Binance, Kraken, and KuCoin to identify arbitrage opportunities between exchanges. The main emphasis will be on speed and efficiency in detecting and executing profitable trades.
- **Bachelor's Thesis Upgrade (Possibility)**: The next phase will expand to include decentralized exchanges (DEXs), potentially employing cross-exchange or cross-chain arbitrage using tools such as Web3.py and Infura. Additional strategies like flash loans may also be explored.

## Installation and Setup
1. **Clone the Repository**
   ```sh
   git clone https://github.com/TUkan74/Arbitrage-bot.git
   cd arbitrage-bot
   ```

2. **Install Poetry**
   ```sh
   pip isntall poetry
   ```

3. **Install Dependencies**
   ```sh
   poetry install
   ```

4. **API Keys Setup**
   - Create an `.env` file in the root directory.
   - Add your API keys for each exchange as follows:
     ```
     BINANCE_API_KEY=your_binance_api_key
     BINANCE_API_SECRET=your_binance_api_secret
     KRAKEN_API_KEY=your_kraken_api_key
     KRAKEN_API_SECRET=your_kraken_api_secret
     ```

## Dependencies
- **Python 3.8+**
- **CCXT**: A unified API for interacting with multiple cryptocurrency exchanges.
- **dotenv**: To securely manage API keys and other sensitive information.
- **aiohttp**: For making asynchronous API requests.

## Configuration
The bot can be configured by modifying the `config.json` file. Key configuration parameters include:
- **Trading Pairs**: Specify which trading pairs the bot will focus on (e.g., `BTC/USDT`, `ETH/BTC`).
- **Trade Threshold**: Set the minimum profit percentage required to trigger an arbitrage trade.
- **Polling Interval**: Define the frequency at which the bot should poll exchanges for price data.

Example `config.json`:
```json
{
  "pairs": ["BTC/USDT", "ETH/USDT"],
  "trade_threshold": 0.3,
  "polling_interval": 1
}
```

## Usage
To start the bot, simply run the `main.py` script:
```sh
poetry run python main.py
```
### Command-Line Options
- `--simulate`: Run the bot in simulation mode to test without real trades.
- `--log-level`: Set the logging level (`INFO`, `DEBUG`, etc.) for more detailed output.

Example:
```sh
poetry run python main.py --simulate --log-level DEBUG
```

## Arbitrage Strategies
1. **Inter-Exchange Arbitrage**:
   - The bot identifies price discrepancies between different centralized exchanges and executes trades to profit from the differences.
   - Example: Buy BTC on Kraken at a lower price and sell on Binance at a higher price.

2. **Triangular Arbitrage (Future Scope)**:
   - Triangular arbitrage involves three currency pairs within a single exchange.
   - For instance, trading BTC for ETH, ETH for USDT, and USDT back to BTC to exploit any price imbalances.

## Technical Considerations
- **Speed Optimization**: The bot is designed with a focus on minimizing latency by:
  - Using WebSocket APIs where available.
  - Implementing asynchronous API calls with `aiohttp`.
  - Hosting the bot close to exchange servers for minimal latency.

- **Risk Management**: Key features include:
  - **Minimum Profit Threshold**: Ensure trades are only executed when the potential profit exceeds the combined cost of trading fees.
  - **Stop-Loss**: For reducing risks in case market conditions change unfavorably during trade execution.

- **Concurrency**: The bot monitors multiple pairs and exchanges concurrently using `asyncio` to ensure opportunities are not missed due to sequential processing.

## Potential Future Work
- **Decentralized Exchanges (DEX) Integration**: Expanding the bot to work with decentralized exchanges such as Uniswap and SushiSwap, leveraging Web3 for blockchain access.
- **Cross-Chain Arbitrage**: Utilizing tools like Polkadot bridges to find arbitrage opportunities across different blockchain networks.
- **Flash Loans**: Incorporating flash loans for executing arbitrage opportunities in a single atomic transaction within DeFi protocols.
- **Machine Learning**: Exploring machine learning techniques for price prediction and smarter decision-making in arbitrage opportunities.


---

**Disclaimer**: Cryptocurrency trading involves risk, and this bot is for educational purposes. Profitable arbitrage opportunities may vary significantly depending on market conditions, fees, and other variables.

# Arbitrage Bot - Phase 2

This project implements a cryptocurrency arbitrage bot that identifies and analyzes price differences across multiple exchanges. Phase 2 adds custom exchange connectors and an arbitrage engine.

## Features

- Custom exchange connectors for Binance and KuCoin
- Abstract exchange interface design for easy addition of new exchanges
- Asynchronous arbitrage engine to scan for opportunities
- Slippage and fee estimation for accurate profit calculation
- Advanced logging with different levels (DEBUG, INFO, WARNING, ERROR)
- Configuration via environment variables

## Project Structure

```
.
├── src/
│   ├── core/
│   │   ├── arbitrage/
│   │   │   └── engine.py         # Arbitrage scanning engine
│   │   ├── exchanges/
│   │   │   ├── abstract/
│   │   │   │   ├── exchange_interface.py  # Interface contract
│   │   │   │   └── base_exchange.py      # Common functionality
│   │   │   ├── binance/
│   │   │   │   ├── binance.py          # Binance connector
│   │   │   │   └── binance_normalizer.py  # Response normalizer
│   │   │   └── kucoin/
│   │   │       ├── kucoin.py           # KuCoin connector
│   │   │       └── kucoin_normalizer.py   # Response normalizer
│   │   └── enums.py               # Common enumerations
│   ├── utils/
│   │   ├── logger.py              # Custom logging utility
│   │   └── timezone.py            # Timezone conversion utility
│   ├── phase_1_main.py            # Phase 1 entry point
│   └── phase_2_main.py            # Phase 2 entry point
└── .env                           # Environment configuration (not in repo)
```

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/arbitrage-bot.git
   cd arbitrage-bot
   ```

2. Install Poetry (if not already installed):
   ```
   pip install poetry
   ```

3. Install dependencies using Poetry:
   ```
   poetry install
   ```

4. Create a `.env` file with your API keys and configuration:
   ```
   # Exchange API Keys
   BINANCE_API_KEY=your_binance_api_key
   BINANCE_API_SECRET=your_binance_api_secret
   
   KUCOIN_API_KEY=your_kucoin_api_key
   KUCOIN_API_SECRET=your_kucoin_api_secret
   KUCOIN_API_PASSPHRASE=your_kucoin_passphrase
   
   # Additional CCXT Exchanges
   ADDITIONAL_EXCHANGES=huobi,bitget
   HUOBI_API_KEY=your_huobi_api_key
   HUOBI_API_SECRET=your_huobi_api_secret
   BITGET_API_KEY=your_bitget_api_key
   BITGET_API_SECRET=your_bitget_api_secret
   BITGET_API_PASSPHRASE=your_bitget_passphrase
   
   # Arbitrage Settings
   ARBITRAGE_INITIAL_CAPITAL=1000
   ARBITRAGE_MIN_PROFIT=0.5
   ARBITRAGE_MAX_SLIPPAGE=0.5
   ARBITRAGE_SCAN_INTERVAL=10
   ARBITRAGE_TARGET_SYMBOLS=BTC/USDT,ETH/USDT,XRP/USDT
   ```

## Running the Bot

1. Activate the Poetry virtual environment:
   ```
   poetry shell
   ```

2. Run the bot:
   ```
   poetry run python src/phase_2_main.py
   ```

## Using Additional Exchanges (CCXT)

The bot supports both custom exchange connectors (Binance, KuCoin) and any exchange supported by the CCXT library. To use additional exchanges:

1. Add the exchange names to the `ADDITIONAL_EXCHANGES` variable in your `.env` file:
   ```
   ADDITIONAL_EXCHANGES=huobi,bitget,bybit,okx
   ```

2. Add API credentials for each exchange:
   ```
   HUOBI_API_KEY=your_huobi_api_key
   HUOBI_API_SECRET=your_huobi_api_secret
   
   # Some exchanges require additional authentication parameters
   BITGET_API_KEY=your_bitget_api_key
   BITGET_API_SECRET=your_bitget_api_secret
   BITGET_API_PASSPHRASE=your_bitget_passphrase
   ```

3. The bot will automatically initialize these exchanges using the CCXT wrapper

### Supported CCXT Exchanges

The bot can work with any exchange supported by CCXT, including:
- Binance
- KuCoin
- Huobi
- Bitget
- OKX
- Bybit
- Kraken
- And many more

## Enhanced Logging

The bot now provides more detailed logs to help you understand what's happening:

1. **Symbol Discovery Logs**: Detailed information about available trading pairs across exchanges
2. **Market Data Logs**: Updates on order book fetching with price information
3. **Opportunity Scanning Logs**: Detailed logs of price comparisons, favorable differences, and potential profits
4. **Summary Logs**: At the end of each scan, a summary of comparisons and opportunities found

You can see these logs in the console and in the log files under the `logs/` directory.

## Adding a New Exchange

1. Create a new folder under `src/core/exchanges/` for your exchange
2. Create an exchange connector class that extends `BaseExchange`
3. Implement a normalizer class for standardizing API responses
4. Add the exchange to `phase_2_main.py`

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `ARBITRAGE_INITIAL_CAPITAL` | Starting capital for calculations | 1000.0 |
| `ARBITRAGE_MIN_PROFIT` | Minimum profit threshold (%) | 0.5 |
| `ARBITRAGE_MAX_SLIPPAGE` | Maximum acceptable slippage (%) | 0.5 |
| `ARBITRAGE_SCAN_INTERVAL` | Time between scans (seconds) | 10.0 |
| `ARBITRAGE_TARGET_SYMBOLS` | Trading pairs to monitor (comma-separated) | None (auto-discover) |
| `ADDITIONAL_EXCHANGES` | CCXT exchanges to use (comma-separated) | None |

## Phase 2 Development Goals

- [x] Abstract exchange interface
- [x] Base exchange with common functionality
- [x] Custom exchange connectors (Binance, KuCoin)
- [x] Arbitrage engine
- [x] Opportunity detection
- [x] Profit calculation with fees and slippage
- [ ] Actual trade execution (planned for Phase 3)

## Development

### Adding Dependencies

To add new dependencies:
```bash
# Add a production dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name
```

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

The project uses Black for code formatting and isort for import sorting. To format your code:

```bash
poetry run black .
poetry run isort .
```

### Type Checking

The project uses mypy for type checking:

```bash
poetry run mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure code formatting
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
