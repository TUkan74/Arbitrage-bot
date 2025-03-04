from Classes.Coin import Coin
import json

class Coins_map:

    """
    Loads a list of coins from a JSON file and initializes dictionaries
    for quick lookups by coin ID or coin name.

    Args:
        file_path (str): The file path to the coins JSON data.
    """

    def __init__(self,file_path):
        self.coins_by_id = {}
        self.coins_by_name = {}


        with open(file_path,"r",encoding="utf-8") as f:
            data = json.load(f)
    
        for item in data:
            coin_id = item["id"]
            coin_name = item["name"]

            coin_obj = Coin(coin_id,coin_name)

            self.coins_by_id[coin_id] = coin_obj
            self.coins_by_name[coin_name] = coin_obj
        print("Done")
        
    
    def get_coin_by_id(self,_id) -> Coin | None:
        return self.coins_by_id.get(_id)
    
    def get_coins_by_name(self,_name) -> Coin | None:
        return self.coins_by_name.get(_name)
    
    def __repr__(self):
        num_id_coins = len(self.coins_by_id)
        num_name_coins = len(self.coins_by_name)
        
        # Take a small sample of coin IDs and names for preview
        sample_size = 3
        id_keys_sample = list(self.coins_by_id.keys())[:sample_size]
        name_keys_sample = list(self.coins_by_name.keys())[:sample_size]
        
        return (
            f"Coins_map("
            f"num_id_coins={num_id_coins}, "
            f"num_name_coins={num_name_coins}, "
            f"coins_by_id_sample={id_keys_sample}, "
            f"coins_by_name_sample={name_keys_sample}"
            f")"
        )