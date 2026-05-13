import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# Mock the database config and pool before importing the app
import os
os.environ["DATABASE_URL"] = "postgres://test:test@localhost:5432/testdb"
os.environ["SECRET_KEY"] = "testsecret"
os.environ["OLLAMA_URL"] = "http://test-ollama:11434"

from main import app
from database import init_db, close_db

@pytest.fixture
def client():
    # Use TestClient for synchronous endpoint testing
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_pool():
    pool = AsyncMock()
    conn = AsyncMock()
    
    # Setup connection mock methods
    conn.fetchrow = AsyncMock()
    conn.fetch = AsyncMock()
    conn.execute = AsyncMock()
    conn.fetchval = AsyncMock()
    
    # Setup acquire context manager
    pool.acquire.return_value.__aenter__.return_value = conn
    
    # Setup transaction context manager
    conn.transaction.return_value.__aenter__.return_value = AsyncMock()
    
    return pool, conn

@pytest.fixture(autouse=True)
def patch_db_pool(mock_pool):
    pool, conn = mock_pool
    with patch('database.pool', pool), patch('database.get_pool', return_value=pool):
        yield pool, conn
