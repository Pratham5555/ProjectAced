from fastapi import APIRouter, HTTPException, Depends
from models import UserRegister, UserLogin, UserResponse, TokenResponse
from auth import hash_password, verify_password, create_token, get_current_user
from database import get_pool

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister):
    pool = get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1 OR username = $2",
            data.email, data.username
        )
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed = hash_password(data.password)
        user = await conn.fetchrow(
            "INSERT INTO users (username, email, password) VALUES ($1, $2, $3) RETURNING id",
            data.username, data.email, hashed
        )
    token = create_token(user["id"])
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    pool = get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT id, password FROM users WHERE email = $1", data.email)
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user["id"])
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(user=Depends(get_current_user)):
    return UserResponse(**user)
