import pandas as pd
import requests as rq
import json
import numpy as np
import warnings
import datetime
import time

# from IPython.display import clear_output
pd.set_option("display.precision", 4, "display.colheader_justify", "center")

# from models.Coins_map import Coins_map
from models.Coin import Coin
from api.client import CoinGeckoClient
from utils import convert_to_local_tz

# from test import test_runs

gecko_client = CoinGeckoClient()



"""def create_coin_map() -> Coins_map:
    
    # Creates a json file which maps coin ID and name for easier search

    
    gecko_api = CoinGeckoClient()
    json_file = "docs/coin_map.json"

    response = gecko_api.get_response(
        "/coins/list",
    )
    filtered_data = [{"id": item["id"], "name": item["name"]} for item in response]
    if response:
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(filtered_data, f, indent=4, ensure_ascii=False)

    result_map = Coins_map(json_file)
    # print(result_map)
    return result_map"""


def run_program():
    # Only for testing purposes
    # test_runs(gecko_client)

    df_all_exchanges = fetch_tickers_for_multiple_exchanges(
        coin_id="ethereum",
        base_curr="ETH",
        target_curr="BTC",
        country_filter="United States",
    )

    print(df_all_exchanges)


def get_exchange_rate(base_curr):

    exchange_rate_response = gecko_client.get_response(f"/exchange_rates")
    rate = ""
    try:
        rate = exchange_rate_response["rates"][base_curr.lower()]["value"]
    except KeyError as ke:
        print("Currency not found in the exchange rate API response:", ke)

    return rate


def get_vol_exchange(id, days, base_curr):

    vol_params = {"days": days}

    exchange_vol_response = gecko_client.get_response(
        f"/exchanges/{id}/volume_chart", vol_params
    )

    time, volume = [], []

    # Get exchange rate when base_curr is not BTC
    ex_rate = 1.0
    if base_curr != "BTC":
        ex_rate = get_exchange_rate(base_curr)

        # Give a warning when exchange rate is not found
        if ex_rate == "":
            print(
                f"Unable to find exchange rate for {base_curr}, vol will be reported in BTC"
            )
            ex_rate = 1.0

    for i in range(len(exchange_vol_response)):
        # Convert to seconds
        s = exchange_vol_response[i][0] / 1000
        time.append(datetime.datetime.fromtimestamp(s).strftime("%Y-%m-%d"))

        # Default unit for volume is BTC
        volume.append(float(exchange_vol_response[i][1]) * ex_rate)

    df_vol = pd.DataFrame(list(zip(time, volume)), columns=["date", "volume"])

    # Calculate SMA for a specific window
    df_vol["volume_SMA"] = df_vol["volume"].rolling(7).mean()

    return df_vol.sort_values(by=["date"], ascending=False).reset_index(drop=True)


def display_agg_per_exchange(df_ex_all, base_curr):

    # Group data and calculate statistics per exchange
    df_agg = df_ex_all.groupby("exchange").agg(
        trade_time_min=("trade_time", "min"),
        trade_time_latest=("trade_time", "max"),
        last_price_mean=("last_price", "mean"),
        last_vol_mean=("last_vol", "mean"),
        spread_mean=("spread", "mean"),
        num_trades=("last_price", "count"),
    )

    # Get time interval over which statistics have been calculated
    df_agg["trade_time_duration"] = (
        df_agg["trade_time_latest"] - df_agg["trade_time_min"]
    )

    # Reset columns so that we can access exchanges below
    df_agg = df_agg.reset_index()

    # Calculate % of total volume for all exchanges
    last_vol_pert = []
    for i, row in df_agg.iterrows():
        try:
            df_vol = get_vol_exchange(row["exchange"], 30, base_curr)
            current_vol = df_vol["volume_SMA"][0]
            vol_pert = (row["last_vol_mean"] / current_vol) * 100
            last_vol_pert.append(vol_pert)
        except:
            last_vol_pert.append("")
            continue

    # Add % of total volume column
    df_agg["last_vol_pert"] = last_vol_pert

    # Remove redundant column
    df_agg = df_agg.drop(columns=["trade_time_min"])

    # Round all float values
    # (seems to be overwritten by style below)
    df_agg = df_agg.round({"last_price_mean": 2, "last_vol_mean": 2, "spread_mean": 2})

    print(df_agg)

    return None


def highlight_max_min(x, color):

    return np.where(
        (x == np.nanmax(x.to_numpy())) | (x == np.nanmin(x.to_numpy())),
        f"color: {color};",
        None,
    )


def run_bot(base_id, base_curr, target_curr, country):

    df_ex_all = fetch_tickers_for_multiple_exchanges(
        base_id, base_curr, target_curr, country
    )

    # Collect data every minute
    while True:
        time.sleep(60)
        df_new = fetch_tickers_for_multiple_exchanges(
            base_id, base_curr, target_curr, country
        )

        # Merge to existing DataFrame
        df_ex_all = pd.concat([df_ex_all, df_new])

        # Remove duplicate rows based on all columns
        df_ex_all = df_ex_all.drop_duplicates()

        # Clear previous display once new one is available
        print("---------------------------------------")
        display_agg_per_exchange(df_ex_all, base_curr)

    return None


def fetch_tickers_for_multiple_exchanges(
    coin_id: str, base_curr: str, target_curr: str, country_filter: str = None
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
        print(
            "Warning: get_exchanges() returned None. Possibly rate-limited. Returning empty DataFrame."
        )
        return pd.DataFrame()

    df_ex = pd.DataFrame(response)
    df_subset = df_ex[["id", "name", "country", "trade_volume_24h_btc"]]
    df_ex_subset = df_subset.sort_values(by=["trade_volume_24h_btc"], ascending=False)
    df_all = df_ex_subset[(df_ex_subset["country"] == country_filter)]

    exchanges_list = df_all["id"]
    ex_all = []

    for exchange_id in exchanges_list:
        found_match = gecko_client.get_tickers(
            coin_id, exchange_id, base_curr, target_curr
        )
        if found_match == "" or found_match is None:
            continue
        else:
            old_ts = found_match["last_traded_at"]
            temp_dict = dict(
                exchange=exchange_id,
                last_price=found_match["last"],
                last_vol=found_match["volume"],
                spread=found_match["bid_ask_spread_percentage"],
                trade_time=convert_to_local_tz(old_ts),
            )
            ex_all.append(temp_dict)

    return pd.DataFrame(ex_all)


def main():
    """
    Main entry point of the program
    """
    # coins_map = create_coin_map()
    # run_program()
    # print(get_exchange_rate("ETH"))
    run_bot(
        base_id="ethereum", base_curr="ETH", target_curr="USDT", country="United States"
    )


if __name__ == "__main__":
    main()
