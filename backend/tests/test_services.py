import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from services.llm_service import generate_text, stream_chat
from services.summary_service import generate_summary

@pytest.mark.asyncio
@patch('services.llm_service.httpx.AsyncClient')
async def test_generate_text(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance
    
    # Mock the post response
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Mocked LLM Response"}
    mock_client_instance.post.return_value = mock_response
    
    result = await generate_text("Test prompt")
    assert result == "Mocked LLM Response"

@pytest.mark.asyncio
@patch('services.summary_service.generate_text')
async def test_generate_summary(mock_generate_text):
    mock_generate_text.return_value = "This is a summary."
    
    result = await generate_summary("Long document text...")
    assert result == "This is a summary."
    assert mock_generate_text.called

@pytest.mark.asyncio
@patch('services.llm_service.httpx.AsyncClient')
async def test_stream_chat(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance
    
    mock_response = AsyncMock()
    
    async def mock_aiter_lines():
        yield '{"response": "Chunk1", "done": false}'
        yield '{"response": "Chunk2", "done": true}'
        
    mock_response.aiter_lines = mock_aiter_lines
    mock_client_instance.stream.return_value.__aenter__.return_value = mock_response
    
    chunks = []
    async for chunk in stream_chat("Test Prompt", "Test Context"):
        chunks.append(chunk)
        
    assert chunks == ["Chunk1", "Chunk2"]
