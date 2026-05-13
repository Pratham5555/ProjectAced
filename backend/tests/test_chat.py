import pytest
from unittest.mock import patch, AsyncMock
from auth import create_access_token
import json

@pytest.fixture
def auth_headers():
    token = create_access_token(data={"sub": "testuser"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def mock_auth_user(patch_db_pool):
    pool, conn = patch_db_pool
    # First call is user verification
    # Need to handle multiple execute/fetch calls
    def fetchrow_side_effect(*args, **kwargs):
        if "FROM users" in args[0]:
            return {"id": 1, "username": "testuser"}
        if "FROM files" in args[0]:
            return {"id": 1, "status": "ready"}
        return None
    conn.fetchrow.side_effect = fetchrow_side_effect
    return conn

@pytest.mark.asyncio
async def test_get_chat_history(client, auth_headers, mock_auth_user):
    mock_auth_user.fetch.return_value = [
        {"role": "user", "content": "Hello", "timestamps": None},
        {"role": "ai", "content": "Hi there [00:10]", "timestamps": '{"00:10": 10}'}
    ]
    
    response = client.get("/api/chat/history/1", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["role"] == "user"

@pytest.mark.asyncio
@patch('routes.chat_routes.search_vectors')
@patch('routes.chat_routes.llm_service.stream_chat')
async def test_chat_stream(mock_stream_chat, mock_search_vectors, client, auth_headers, mock_auth_user):
    # Setup mocks
    mock_search_vectors.return_value = "Vector search context"
    
    async def mock_generator(*args, **kwargs):
        yield "Chunk 1 "
        yield "Chunk 2"
    
    mock_stream_chat.side_effect = mock_generator
    
    response = client.post(
        "/api/chat", 
        headers=auth_headers,
        json={"file_id": 1, "prompt": "Test query"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # Check if stream consumed correctly
    content = b"".join(response.iter_bytes()).decode("utf-8")
    assert "Chunk 1" in content
    assert "Chunk 2" in content
