from core.exchanges.binance import BinanceExchange

def main():
    # Create an instance of the Binance exchange
    binance = BinanceExchange()
    
    # Test getting exchange info
    print("\nGetting exchange info...")
    exchange_info = binance.get_exchange_info()
    print(exchange_info)
    
    # Test getting BTC/USDT ticker
    print("\nGetting BTC/USDT ticker...")
    ticker = binance.get_ticker("BTC/USDT")
    print(ticker)
    
    # Test getting BTC/USDT order book
    print("\nGetting BTC/USDT order book...")
    order_book = binance.get_order_book("BTC/USDT", limit=5)
    print(order_book)

if __name__ == "__main__":
    main() 