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
from test import test_runs

gecko_client = CoinGeckoClient()
util = Utilities()

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



def run_program():
    # Only for testing purposes
    # test_runs(gecko_client)

    df_all_exchanges = fetch_tickers_for_multiple_exchanges(
        coin_id="ethereum",
        base_curr="ETH",
        target_curr="BTC",
        country_filter="United States"  
    )

    print(df_all_exchanges)

def fetch_tickers_for_multiple_exchanges(
        coin_id: str,
        base_curr: str,
        target_curr: str,
        country_filter: str = None
    ) -> pd.DataFrame:
    """
    Fetches ticker data for a specified coin and trading pair across multiple exchanges.
    Optionally filters exchanges by a given country.

    Args:
        coin_id (str): CoinGecko's coin ID (e.g. 'ethereum').
        base_curr (str): Base currency symbol (e.g. 'ETH').
        target_curr (str): Target currency symbol (e.g. 'BTC').
        country_filter (str): Name of the country to filter by (exact match, case-insensitive).
                             If None, no filtering by country is performed.

    Returns:
        pd.DataFrame: A DataFrame containing exchange name, country, last trade price,
                      volume, spread, and local trade time.
    """
    response = gecko_client.get_exchanges()
    
    if not response:
        print("Warning: get_exchanges() returned None. Possibly rate-limited. Returning empty DataFrame.")
        return pd.DataFrame()

    
    df_ex = pd.DataFrame(response)
    df_subset = df_ex[["id","name","country", "trade_volume_24h_btc"]]
    df_ex_subset = df_subset.sort_values(by=["trade_volume_24h_btc"],ascending=False) 
    
    df_all = df_ex_subset[(df_ex_subset["country"] == country_filter)]    
    
    exchanges_list = df_all["id"]
    ex_all = []    
       
    for exchange_id in exchanges_list:
        found_match = gecko_client.get_tickers(coin_id,exchange_id, base_curr, target_curr)
        if found_match == "" or found_match is None:
            continue
        else:
            old_ts = found_match["last_traded_at"]
            temp_dict = dict(
                             exchange = exchange_id,
                             last_price = found_match["last"],
                             last_vol   = found_match["volume"],
                             spread     = found_match["bid_ask_spread_percentage"],
                             trade_time = util.convert_to_local_tz(old_ts)
                             )
            ex_all.append(temp_dict)
            
    return pd.DataFrame(ex_all)    
   
    

def main():
    """
    Main entry point of the program
    """
    # coins_map = create_coin_map()
    run_program()



if __name__ == "__main__":
    main()