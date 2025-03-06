import pandas as pd
import requests as rq
import json
import numpy as np
import warnings

# from IPython.display import clear_output
pd.set_option('display.precision', 4,
              'display.colheader_justify', 'center')

from models.Coins_map import Coins_map
from models.Coin import Coin
from api.coingecko_client import CoinGeckoClient
from utils.convert_tz import Utilities

PUB_URL = "https://api.coingecko.com/api/v3"
EXCHANGES = "/exchanges"
TICKERS = "/tickers"






################## MAIN API ENDPOINTS ##################




    
################## MAIN API ENDPOINTS ##################

def create_coin_map() -> Coins_map :
    """
    Creates a json file which maps coin ID and name for easier search

    """
    gecko_api = CoinGeckoClient()
    json_file = "src/documents/coin_map.json"

    response = gecko_api.get_response(
        "/coins/list",
    )
    filtered_data = [{"id": item["id"], "name": item["name"]} for item in response]
    if response:
        with open(json_file,"w",encoding="utf-8") as f:
            json.dump(filtered_data,f,indent=4,ensure_ascii=False)

    result_map = Coins_map(json_file)
    # print(result_map)
    return result_map
    

"""USE_KEY = {
        "accept": "application/json",
        "api-key" : get_key() 
}"""


def run_program():
    
    
    gecko_client = CoinGeckoClient()
    util = Utilities()
   
    exchange_parameters = {
                "per_page": 250,
                "page": 1
    }

    response = gecko_client.get_response(EXCHANGES,exchange_parameters)
    df_ex = pd.DataFrame(response)
    df_subset = df_ex[["id","name","country", "trade_volume_24h_btc"]]
    df_ex_subset_sorted = df_subset.sort_values(by=["trade_volume_24h_btc"],ascending=False) 
    # df_ex_subset = df_ex_subset[(df_ex_subset["trade_volume_24h_btc"] >= 10000)]
    # df_ex_subset = df_ex_subset[(df_ex_subset["country"] == "United States")]
    print("==========================")
    print(df_ex_subset_sorted)
    tickers = gecko_client.get_tickers("ethereum","gdax","ETH","BTC")
    print("==========================")
    print(str(tickers))

def main():
    """
    Main entry point of the program
    """
    coins_map = create_coin_map()
    run_program()



if __name__ == "__main__":
    main()