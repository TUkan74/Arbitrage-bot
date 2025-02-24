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

2. **Create a Virtual Environment**
   ```sh
   python3 -m venv arb_bot_venv
   source arb_bot_venv/bin/activate  # On Windows use `arb_bot_venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```sh
   pip install -r requirements.txt
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
python main.py
```
### Command-Line Options
- `--simulate`: Run the bot in simulation mode to test without real trades.
- `--log-level`: Set the logging level (`INFO`, `DEBUG`, etc.) for more detailed output.

Example:
```sh
python main.py --simulate --log-level DEBUG
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
