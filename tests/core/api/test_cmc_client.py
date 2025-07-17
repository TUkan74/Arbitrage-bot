"""
Tests for the CMC (CoinMarketCap) API client.
"""

import pytest
import os
from unittest.mock import patch, Mock, MagicMock
import json
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects, HTTPError
from api.client import CMCClient

@pytest.fixture
def mock_env_api_key():
    """Mock environment variable for API key"""
    with patch.dict(os.environ, {'CMC_API_KEY': 'test_api_key'}, clear=True):
        yield

@pytest.fixture
def mock_env_no_api_key():
    """Mock environment without API key"""
    with patch.dict(os.environ, {}, clear=True):  # Clear all environment variables
        yield

@pytest.fixture
def mock_session():
    """Mock session for testing"""
    session = MagicMock(spec=Session)
    session.headers = MagicMock()  # Add headers attribute
    session.headers.update = MagicMock()  # Add update method to headers
    return session

def test_init_with_api_key(mock_env_api_key, mock_session):
    """Test initialization with API key"""
    client = CMCClient(session=mock_session)
    assert client.api_key == 'test_api_key'
    mock_session.headers.update.assert_called_once_with({
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': 'test_api_key'
    })

@pytest.mark.parametrize("starting_rank,number_of_tokens,expected", [
    (1, 5, ['BTC', 'ETH', 'XRP', 'BNB', 'ADA']),  # Top 5 coins
    (2, 4, ['ETH', 'XRP', 'BNB', 'ADA']),  # Rank 2-5
    (4, 5, ['BNB', 'ADA', 'SOL', 'DOT', 'DOGE']),  # Rank 4-8
    (5, 6, ['ADA', 'SOL', 'DOT', 'DOGE', 'LINK', 'MATIC'])  # Rank 5-10
])
def test_get_ranked_coins(mock_env_api_key, mock_session, starting_rank, number_of_tokens, expected):
    """Test getting ranked coins with different parameters"""
    mock_data = {
        'data': [
            {'symbol': 'BTC', 'cmc_rank': 1, 'tags': []},
            {'symbol': 'ETH', 'cmc_rank': 2, 'tags': []},
            {'symbol': 'XRP', 'cmc_rank': 3, 'tags': []},
            {'symbol': 'BNB', 'cmc_rank': 4, 'tags': []},
            {'symbol': 'ADA', 'cmc_rank': 5, 'tags': []},
            {'symbol': 'SOL', 'cmc_rank': 6, 'tags': []},
            {'symbol': 'DOT', 'cmc_rank': 7, 'tags': []},
            {'symbol': 'DOGE', 'cmc_rank': 8, 'tags': []},
            {'symbol': 'LINK', 'cmc_rank': 9, 'tags': []},
            {'symbol': 'MATIC', 'cmc_rank': 10, 'tags': []},
            {'symbol': 'USDT', 'cmc_rank': 3, 'tags': ['stablecoin']},  # Should be excluded
        ]
    }
    
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_data)
    mock_session.get.return_value = mock_response

    client = CMCClient(session=mock_session)
    result = client.get_ranked_coins(starting_rank, number_of_tokens)
    assert result == expected

def test_get_ranked_coins_exclude_stablecoins(mock_env_api_key, mock_session):
    """Test that stablecoins are excluded from results"""
    mock_data = {
        'data': [
            {'symbol': 'BTC', 'cmc_rank': 1, 'tags': []},
            {'symbol': 'USDT', 'cmc_rank': 2, 'tags': ['stablecoin']},
            {'symbol': 'ETH', 'cmc_rank': 3, 'tags': []},
            {'symbol': 'USDC', 'cmc_rank': 4, 'tags': ['stablecoin']},
        ]
    }
    
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_data)
    mock_session.get.return_value = mock_response

    client = CMCClient(session=mock_session)
    result = client.get_ranked_coins(1, 4)
    assert result == ['BTC', 'ETH']

@pytest.mark.parametrize("exception_class", [
    ConnectionError,
    Timeout,
    TooManyRedirects
])
def test_get_ranked_coins_connection_errors(mock_env_api_key, mock_session, exception_class):
    """Test error handling for various connection exceptions"""
    mock_session.get.side_effect = exception_class("Test error")

    client = CMCClient(session=mock_session)
    with pytest.raises(Exception) as exc_info:
        client.get_ranked_coins()
    assert str(exc_info.value) == "Error fetching data from CoinMarketCap: Test error"

def test_get_ranked_coins_invalid_json(mock_env_api_key, mock_session):
    """Test handling of invalid JSON response"""
    mock_response = MagicMock()
    mock_response.text = "Invalid JSON"
    mock_session.get.return_value = mock_response

    client = CMCClient(session=mock_session)
    with pytest.raises(json.JSONDecodeError):
        client.get_ranked_coins()

def test_get_ranked_coins_missing_data_field(mock_env_api_key, mock_session):
    """Test handling of response missing 'data' field"""
    mock_response = MagicMock()
    mock_response.text = json.dumps({'status': 'ok'})  # No 'data' field
    mock_session.get.return_value = mock_response

    client = CMCClient(session=mock_session)
    with pytest.raises(Exception, match="Invalid response format from CoinMarketCap: 'data' field missing"):
        client.get_ranked_coins()

def test_get_ranked_coins_http_error(mock_env_api_key, mock_session):
    """Test handling of HTTP errors"""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = HTTPError("404 Client Error")
    mock_session.get.return_value = mock_response

    client = CMCClient(session=mock_session)
    with pytest.raises(Exception, match="Error fetching data from CoinMarketCap: 404 Client Error"):
        client.get_ranked_coins()

def test_session_headers(mock_env_api_key, mock_session):
    """Test that session headers are set correctly"""
    mock_response = MagicMock()
    mock_response.text = json.dumps({'data': []})
    mock_session.get.return_value = mock_response

    client = CMCClient(session=mock_session)
    client.get_ranked_coins()

    # Verify headers were set correctly
    mock_session.headers.update.assert_called_once_with({
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': 'test_api_key'
    }) 