"""
Pytest configuration and fixtures
"""
import sys
import os
import pytest

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

# Define common fixtures here if needed

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing"""
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv('BINANCE_API_KEY', 'test_api_key')
        mp.setenv('BINANCE_API_SECRET', 'test_api_secret')
        yield 