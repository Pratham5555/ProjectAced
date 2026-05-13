import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://newgen:newgen_pass@localhost:5432/newgen")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
FAISS_DIR = os.getenv("FAISS_DIR", "faiss_indices")
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
WHISPER_MODEL = "base"
