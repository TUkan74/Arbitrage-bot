import pandas as pd
import requests as rq
import json
import numpy as np
import warnings
import pytz
import time
import datetime
# from IPython.display import clear_output
pd.set_option('display.precision', 4,
              'display.colheader_justify', 'center')

from Classes.Coins_map import Coins_map
from Classes.Coin import Coin

PUB_URL = "https://api.coingecko.com/api/v3"
EXCHANGES = "/exchanges"
TICKERS = "/tickers"






################## MAIN API ENDPOINTS ##################

def get_key() -> str:
    """
    Reads and returns api key to coingecko api from a JSON file

    Returns:
        str: coingecko api key stored in documents/demo_key.json file

    Raises:
        FileNotFoundError: If the file does not exist 
        KeyError: If the expected key is not found in the JSON file
    """
    API_KEY_FILE = "documents/demo_key.json"
    API_KEY_JSON = "coingecko_api_key"
    
    f = open(API_KEY_FILE, 'r')
    key_dict = json.load(f)
    key = key_dict[API_KEY_JSON]
    f.close()
    return key

def get_response(target,headers,params,URL) -> dict:
    """
    Sends a GET request to the specified API endpoint and returns the response data.

    Args:
        target (str): The endpoint path to append to the base URL.
        headers (dict): The request headers, typically including authentication details.
        params (dict): The query parameters for the request.
        URL (str): The base URL of the API.

    Returns:
        dict: The JSON response data if the request is successful.

    Prints:
        Error message if the request fails.
    
    Raises:
        requests.exceptions.RequestException: If an HTTP request error occurs.
    """
    
    url = "".join((URL,target))
    response = rq.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Failed to get data with return code {response.status_code}")

def get_tickers(coin_id, exchange_id, base_curr, target_curr) -> dict | None:
    """
    Fetches the ticker data for a given coin and exchange, filtering by base and target currencies.

    Args:
        coin_id (str): The CoinGecko ID of the cryptocurrency (e.g., 'bitcoin').
        exchange_id (str): The CoinGecko ID of the exchange (e.g., 'gdax').
        base_curr (str): The base currency symbol (e.g., 'BTC').
        target_curr (str): The target currency symbol (e.g., 'USD').

    Returns:
        dict: The matching ticker data, or None if no match is found.
    """
    url = f"/coins/{coin_id}/tickers?exchange_ids={exchange_id}"
    response = get_response(url, USE_KEY, {}, PUB_URL)

    if response and "tickers" in response:
        for ticker in response["tickers"]:
            if ticker["base"] == base_curr and ticker["target"] == target_curr:
                return ticker
    
    warnings.warn(f"No data found for {base_curr}-{target_curr} pair on {exchange_id}")
    return None

def convert_to_local_tz(old_ts) -> str:
    """
    Converts the timestamp to localized one

    Args:
        old_ts (str): Old timestamp that needs to be updated

    Returns:
        str: Updated timestamp to our own local time
    """


    new_tz = pytz.timezone("Europe/Amsterdam")
    old_tz = pytz.timezone("UTC")
    
    format = "%Y-%m-%dT%H:%M:%S+00:00"
    datetime_obj = datetime.datetime.strptime(old_ts, format)
    
    localized_ts = old_tz.localize(datetime_obj)
    new_ts = localized_ts.astimezone(new_tz)
    
    return new_ts
    
################## MAIN API ENDPOINTS ##################

def create_coin_map() -> Coins_map :
    """
    Creates a json file which maps coin ID and name for easier search

    """
    json_file = "documents/coin_map.json"

    response = get_response(
        "/coins/list",
        USE_KEY,
        {},
        PUB_URL
    )
    filtered_data = [{"id": item["id"], "name": item["name"]} for item in response]
    if response:
        with open(json_file,"w",encoding="utf-8") as f:
            json.dump(filtered_data,f,indent=4,ensure_ascii=False)

    result_map = Coins_map(json_file)
    # print(result_map)
    return result_map
    

USE_KEY = {
        "accept": "application/json",
        "api-key" : get_key() 
}


def run_program():
    

   
    exchange_parameters = {
                "per_page": 250,
                "page": 1
    }

    response = get_response(EXCHANGES,USE_KEY,exchange_parameters,PUB_URL)
    df_ex = pd.DataFrame(response)
    df_subset = df_ex[["id","name","country", "trade_volume_24h_btc"]]
    df_ex_subset_sorted = df_subset.sort_values(by=["trade_volume_24h_btc"],ascending=False) 
    # df_ex_subset = df_ex_subset[(df_ex_subset["trade_volume_24h_btc"] >= 10000)]
    # df_ex_subset = df_ex_subset[(df_ex_subset["country"] == "United States")]
    print("==========================")
    print(df_ex_subset_sorted)
    tickers = get_tickers("ethereum","gdax","ETH","BTC")
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