import os
import asyncio
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from auth import get_current_user
from database import get_pool
from config import UPLOAD_DIR, MAX_FILE_SIZE
from models import FileResponse as FileResp
from services.pdf_service import extract_text_from_pdf
from services.whisper_service import transcribe_media
from services.embedding_service import add_to_index, remove_from_index

router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "audio/mpeg": "audio",
    "audio/wav": "audio",
    "audio/mp3": "audio",
    "audio/x-wav": "audio",
    "video/mp4": "video",
    "video/mpeg": "video",
    "video/webm": "video",
    "video/x-matroska": "video",
}


def get_file_type(content_type: str, filename: str) -> str:
    if content_type in ALLOWED_TYPES:
        return ALLOWED_TYPES[content_type]
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    ext_map = {"pdf": "pdf", "mp3": "audio", "wav": "audio", "ogg": "audio",
               "mp4": "video", "webm": "video", "mkv": "video", "avi": "video"}
    if ext in ext_map:
        return ext_map[ext]
    raise HTTPException(status_code=400, detail="Unsupported file type")


async def process_file(file_id: int, file_path: str, file_type: str, user_id: int):
    pool = get_pool()
    try:
        if file_type == "pdf":
            chunks = extract_text_from_pdf(file_path)
        else:
            chunks = await asyncio.to_thread(transcribe_media, file_path)

        if not chunks:
            async with pool.acquire() as conn:
                await conn.execute("UPDATE files SET status = 'error' WHERE id = $1", file_id)
            return

        async with pool.acquire() as conn:
            chunk_ids = []
            for i, chunk in enumerate(chunks):
                row = await conn.fetchrow(
                    """INSERT INTO chunks (file_id, chunk_index, content, start_time, end_time, page_number)
                       VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
                    file_id, i, chunk["content"],
                    chunk.get("start_time"), chunk.get("end_time"), chunk.get("page_number")
                )
                chunk_ids.append(row["id"])

        texts = [c["content"] for c in chunks]
        await asyncio.to_thread(add_to_index, user_id, texts, chunk_ids)

        async with pool.acquire() as conn:
            await conn.execute("UPDATE files SET status = 'ready' WHERE id = $1", file_id)

    except Exception as e:
        print(f"Error processing file {file_id}: {e}")
        async with pool.acquire() as conn:
            await conn.execute("UPDATE files SET status = 'error' WHERE id = $1", file_id)


@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    file_type = get_file_type(file.content_type or "", file.filename or "")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 25MB)")

    user_dir = os.path.join(UPLOAD_DIR, str(user["id"]))
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, file.filename)

    with open(file_path, "wb") as f:
        f.write(content)

    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO files (user_id, filename, file_type, file_path, file_size)
               VALUES ($1, $2, $3, $4, $5) RETURNING id, created_at""",
            user["id"], file.filename, file_type, file_path, len(content)
        )

    background_tasks.add_task(process_file, row["id"], file_path, file_type, user["id"])

    return {
        "id": row["id"],
        "filename": file.filename,
        "file_type": file_type,
        "file_size": len(content),
        "status": "processing",
        "created_at": row["created_at"].isoformat(),
    }


@router.get("")
async def list_files(user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, filename, file_type, file_size, status, created_at FROM files WHERE user_id = $1 ORDER BY created_at DESC",
            user["id"]
        )
    return [dict(r) for r in rows]


@router.get("/{file_id}")
async def get_file(file_id: int, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, filename, file_type, file_size, status, created_at FROM files WHERE id = $1 AND user_id = $2",
            file_id, user["id"]
        )
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    return dict(row)


@router.delete("/{file_id}")
async def delete_file(file_id: int, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, file_path FROM files WHERE id = $1 AND user_id = $2",
            file_id, user["id"]
        )
        if not row:
            raise HTTPException(status_code=404, detail="File not found")

        chunk_ids = await conn.fetch("SELECT id FROM chunks WHERE file_id = $1", file_id)
        chunk_id_list = [c["id"] for c in chunk_ids]

        await conn.execute("DELETE FROM files WHERE id = $1", file_id)

    if chunk_id_list:
        await asyncio.to_thread(remove_from_index, user["id"], chunk_id_list)

    if os.path.exists(row["file_path"]):
        os.remove(row["file_path"])

    return {"message": "File deleted"}


@router.get("/{file_id}/stream")
async def stream_file(file_id: int, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT file_path, filename, file_type FROM files WHERE id = $1 AND user_id = $2",
            file_id, user["id"]
        )
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    if not os.path.exists(row["file_path"]):
        raise HTTPException(status_code=404, detail="File missing from disk")

    media_types = {
        "pdf": "application/pdf",
        "audio": "audio/mpeg",
        "video": "video/mp4",
    }
    return FileResponse(
        row["file_path"],
        media_type=media_types.get(row["file_type"], "application/octet-stream"),
        filename=row["filename"],
    )


@router.get("/{file_id}/summary")
async def get_summary(file_id: int, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        file_row = await conn.fetchrow(
            "SELECT id FROM files WHERE id = $1 AND user_id = $2",
            file_id, user["id"]
        )
        if not file_row:
            raise HTTPException(status_code=404, detail="File not found")

        cached = await conn.fetchrow("SELECT content FROM summaries WHERE file_id = $1", file_id)
        if cached:
            return {"summary": cached["content"]}

        chunks = await conn.fetch(
            "SELECT content FROM chunks WHERE file_id = $1 ORDER BY chunk_index", file_id
        )

    if not chunks:
        raise HTTPException(status_code=400, detail="File not processed yet")

    from services.summary_service import summarize_chunks
    texts = [c["content"] for c in chunks]
    summary = await summarize_chunks(texts)

    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO summaries (file_id, content) VALUES ($1, $2) ON CONFLICT (file_id) DO UPDATE SET content = $2",
            file_id, summary
        )

    return {"summary": summary}
