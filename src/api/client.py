"""
CMC Client - Interface for CoinMarketCap API
"""

import os
from typing import List, Optional
import json
from requests import Session, RequestException
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects, HTTPError
from utils.logger import Logger
from dotenv import load_dotenv

class CMCClient:
    def __init__(self, session: Optional[Session] = None):
        """Initialize the CMC client with API key from environment.
        
        Args:
            session: Optional requests Session object for testing
        """
        load_dotenv()
        self.api_key = os.getenv('CMC_API_KEY')
        if not self.api_key:
            raise ValueError("CMC_API_KEY environment variable is required")
        self.logger = Logger("cmc")
        self.session = session or Session()
        self.session.headers.update({
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        })
            
    def get_ranked_coins(self, starting_rank: int = 100, number_of_tokens: int = 1500) -> List[str]:
        """
        Get coin symbols ranked from starting_rank to number_of_tokens, excluding stablecoins.
        
        Args:
            starting_rank: Starting rank (inclusive)
            number_of_tokens: End rank (exclusive)
            
        Returns:
            List of coin symbols
            
        Raises:
            Exception: If there is an error fetching data from CoinMarketCap
            json.JSONDecodeError: If the response is not valid JSON
        """
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        parameters = {
            'start': '1',
            'limit': str(number_of_tokens),
            'convert': 'USD'
        }
        
        try:
            response = self.session.get(url, params=parameters)
            response.raise_for_status()
            
            try:
                data = json.loads(response.text)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(f"Invalid JSON response from CoinMarketCap: {str(e)}", e.doc, e.pos)
                
            if 'data' not in data:
                raise Exception("Invalid response format from CoinMarketCap: 'data' field missing")
                
            # Filter coins by rank and exclude stablecoins
            coin_list = []
            for coin in data['data']:
                if (starting_rank <= coin['cmc_rank'] < starting_rank + number_of_tokens and 
                    'stablecoin' not in coin.get('tags', [])):
                    coin_list.append(coin['symbol'])
                    
            return coin_list
            
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            raise Exception(f"Error fetching data from CoinMarketCap: {str(e)}")
        except HTTPError as e:
            raise Exception(f"Error fetching data from CoinMarketCap: {str(e)}")
        except RequestException as e:
            raise Exception(f"Error fetching data from CoinMarketCap: {str(e)}")
