import pytest
from auth import verify_password, get_password_hash, create_access_token

def test_password_hashing():
    password = "secretpassword"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)

def test_create_access_token():
    token = create_access_token(data={"sub": "testuser"})
    assert isinstance(token, str)
    assert len(token) > 20

@pytest.mark.asyncio
async def test_register(client, patch_db_pool):
    pool, conn = patch_db_pool
    # Mock user doesn't exist
    conn.fetchrow.side_effect = [None, {"id": 1, "username": "testuser", "email": "test@test.com"}]
    
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@test.com",
        "password": "testpassword"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_register_existing_user(client, patch_db_pool):
    pool, conn = patch_db_pool
    # Mock user exists
    conn.fetchrow.return_value = {"id": 1}
    
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@test.com",
        "password": "testpassword"
    })
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

@pytest.mark.asyncio
async def test_login(client, patch_db_pool):
    pool, conn = patch_db_pool
    # Mock DB returning user with valid hashed password
    hashed_password = get_password_hash("testpassword")
    conn.fetchrow.return_value = {
        "id": 1,
        "username": "testuser",
        "password": hashed_password
    }
    
    response = client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "testpassword"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_wrong_password(client, patch_db_pool):
    pool, conn = patch_db_pool
    hashed_password = get_password_hash("testpassword")
    conn.fetchrow.return_value = {
        "id": 1,
        "username": "testuser",
        "password": hashed_password
    }
    
    response = client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401
