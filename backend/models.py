from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class FileResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: datetime


class ChatRequest(BaseModel):
    file_id: int
    question: str


class SearchRequest(BaseModel):
    query: str


class SearchResult(BaseModel):
    file_id: int
    filename: str
    chunk_content: str
    score: float
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    page_number: Optional[int] = None
