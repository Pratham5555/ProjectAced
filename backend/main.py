import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, close_db
from config import UPLOAD_DIR, FAISS_DIR
from routes.auth_routes import router as auth_router
from routes.upload_routes import router as upload_router
from routes.chat_routes import router as chat_router
from routes.search_routes import router as search_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(FAISS_DIR, exist_ok=True)
    await init_db()
    yield
    await close_db()


app = FastAPI(title="AI Document Q&A", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(upload_router, prefix="/api/files", tags=["files"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(search_router, prefix="/api/search", tags=["search"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
