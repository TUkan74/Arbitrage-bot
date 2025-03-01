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

def get_key():
    f = open('documents/demo_key.json', 'r')
    key_dict = json.load(f)
    key = key_dict['coingecko_api_key']
    f.close()
    return key

def get_response(target,headers,params,URL):
    url = "".join((URL,target))
    response = rq.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Failed to get data with return code {response.status_code}")


use_key = {
           "accept": "application/json",
           "api-key" : get_key() 
}

exchange_params = {
            "per_page": 250,
            "page": 1
}

response = get_response("/exchanges",use_key,exchange_params,"https://api.coingecko.com/api/v3")
df_ex = pd.DataFrame(response)
df_subset = df_ex[["id","name","country", "trade_volume_24h_btc"]]
df_ex_subset = df_subset.sort_values(by=["trade_volume_24h_btc"],ascending=False) 
# df_ex_subset = df_ex_subset[(df_ex_subset["trade_volume_24h_btc"] >= 10000)]
df_ex_subset = df_ex_subset[(df_ex_subset["country"] == "United States")]
print(df_ex_subset)