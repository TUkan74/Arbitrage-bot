from Classes.Coin import Coin
from init.Import_packages import json


class Coins_map:

    """
    Loads a list of coins from a JSON file and initializes dictionaries
    for quick lookups by coin ID or coin name.

    Args:
        file_path (str): The file path to the coins JSON data.
    """

    def __init__(self,file_path):
        self._coins_by_id = {}
        self.coins_by_name = {}


        with open(file_path,"r",encoding="utf-8") as f:
            data = json.load(f)
    
        for item in data:
            coin_id = item["id"]
            coin_name = item["name"]

            coin_obj = Coin(coin_id,coin_name)

            self._coins_by_id[coin_id] = coin_obj
            self.coins_by_name[coin_name] = coin_obj
        
    
    def get_coin_by_id(id):
        return 