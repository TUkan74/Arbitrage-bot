# file: coingecko_client.py

import json
import requests
import warnings

class CoinGeckoClient:
    """
    A class for interacting with the CoinGecko API.
    """

    def __init__(self, 
                 api_key_file="src/documents/demo_key.json",
                 base_url="https://api.coingecko.com/api/v3"):
        
        """
        Initializes the CoinGeckoClient with an API key and a base URL.

        Args:
            api_key_file (str): Path to the JSON file containing the API key.
            base_url (str): The base URL for the CoinGecko API.
        """
        self.api_key_file = api_key_file
        self.api_key = self._load_api_key()
        self.base_url = base_url

        self.headers = {
            "accept": "application/json",
            "api-key": self.api_key
        }

    def _load_api_key(self):
        """
        Loads and returns the CoinGecko API key from a JSON file.

        Args:
            file_path (str): Path to the JSON file containing the API key.

        Returns:
            str: The CoinGecko API key.
        """
        with open(self.api_key_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["coingecko_api_key"]

    def get_response(self, endpoint, params=None):
        """
        Sends a GET request to the specified endpoint and returns the response data.

        Args:
            endpoint (str): The endpoint path (e.g., "/exchanges").
            params (dict): The query parameters for the request.

        Returns:
            dict or None: The JSON response data if successful, otherwise None.
        """
        params = params or {}
        url = f"{self.base_url}{endpoint}"

        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get data from {url} with code {response.status_code}")
            return None

    def get_exchanges(self, page=1, per_page=250):
        """
        Retrieves a list of exchanges from CoinGecko.

        Args:
            page (int): Page number for pagination.
            per_page (int): Number of items per page.

        Returns:
            list or None: A list of exchange data, or None if request failed.
        """
        endpoint = "/exchanges"
        params = {"page": page, "per_page": per_page}
        return self.get_response(endpoint, params=params)

    def get_tickers(self, coin_id, exchange_id, base_curr, target_curr):
        """
        Fetches the ticker data for a given coin and exchange, 
        filtering by base and target currencies.

        Args:
            coin_id (str): The CoinGecko ID (e.g. 'ethereum').
            exchange_id (str): The exchange ID (e.g. 'gdax').
            base_curr (str): The base currency symbol (e.g. 'ETH').
            target_curr (str): The target currency symbol (e.g. 'BTC').

        Returns:
            dict or None: The matching ticker data, or None if no match is found.
        """
        endpoint = f"/coins/{coin_id}/tickers?exchange_ids={exchange_id}"
        response = self.get_response(endpoint)

        if response and "tickers" in response:
            for ticker in response["tickers"]:
                if (ticker.get("base") == base_curr 
                        and ticker.get("target") == target_curr):
                    return ticker

        warnings.warn(f"No data found for {base_curr}-{target_curr} on {exchange_id}")
        return None

    def list_coins(self):
        """
        Fetches all coins data from CoinGecko.

        Returns:
            list or None: A list of coins, or None if request failed.
        """
        endpoint = "/coins/list"
        return self.get_response(endpoint)
