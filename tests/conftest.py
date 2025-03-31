import pytest
import os
import sys

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing"""
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv('BINANCE_API_KEY', 'test_api_key')
        mp.setenv('BINANCE_API_SECRET', 'test_api_secret')
        yield 