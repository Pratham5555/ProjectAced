import pytest
from unittest.mock import patch, MagicMock
from auth import create_access_token

@pytest.fixture
def auth_headers():
    token = create_access_token(data={"sub": "testuser"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def mock_auth_user(patch_db_pool):
    pool, conn = patch_db_pool
    # Mock verify_token fetching user
    conn.fetchrow.return_value = {"id": 1, "username": "testuser"}
    return conn

@pytest.mark.asyncio
async def test_get_files_empty(client, auth_headers, mock_auth_user):
    mock_auth_user.fetch.return_value = []
    response = client.get("/api/files", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_files_list(client, auth_headers, mock_auth_user):
    mock_files = [
        {"id": 1, "filename": "doc.pdf", "status": "ready"},
        {"id": 2, "filename": "audio.mp3", "status": "processing"}
    ]
    mock_auth_user.fetch.return_value = mock_files
    response = client.get("/api/files", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["filename"] == "doc.pdf"

@pytest.mark.asyncio
@patch('routes.upload_routes.os.makedirs')
@patch('routes.upload_routes.aiofiles.open')
async def test_upload_file(mock_aiofiles, mock_makedirs, client, auth_headers, mock_auth_user):
    # Setup mock file object for aiofiles
    mock_file = MagicMock()
    mock_file.write = MagicMock()
    mock_aiofiles.return_value.__aenter__.return_value = mock_file
    
    # Mock DB insert returning a new file id
    mock_auth_user.fetchval.return_value = 1
    
    # Upload a dummy file
    files = {'file': ('test.pdf', b'dummy content', 'application/pdf')}
    
    with patch('routes.upload_routes.BackgroundTasks.add_task') as mock_bg:
        response = client.post("/api/files/upload", headers=auth_headers, files=files)
        
        assert response.status_code == 200
        assert response.json()["message"] == "File uploaded successfully"
        assert response.json()["file_id"] == 1
        
        # Ensure background processing was queued
        assert mock_bg.called
