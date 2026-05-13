import pytest
from unittest.mock import patch, AsyncMock
from auth import create_access_token

@pytest.fixture
def auth_headers():
    token = create_access_token(data={"sub": "testuser"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def mock_auth_user(patch_db_pool):
    pool, conn = patch_db_pool
    # Verify token call
    conn.fetchrow.return_value = {"id": 1, "username": "testuser"}
    return conn

@pytest.mark.asyncio
@patch('routes.search_routes.search_vectors')
async def test_search_vectors_route(mock_search_vectors, client, auth_headers, mock_auth_user):
    # Setup the mock search vector response
    mock_search_vectors.return_value = [
        {"content": "Found context chunk 1", "score": 0.8},
        {"content": "Found context chunk 2", "score": 0.6}
    ]
    
    response = client.post(
        "/api/search",
        headers=auth_headers,
        json={"file_id": 1, "query": "Test search", "top_k": 2}
    )
    
    assert response.status_code == 200
    assert "results" in response.json()
    assert len(response.json()["results"]) == 2
    assert response.json()["results"][0]["score"] == 0.8
