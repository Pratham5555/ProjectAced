import json
import re
from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from auth import get_current_user
from database import get_pool
from models import ChatRequest
from services.embedding_service import search_index
from services.llm_service import stream_chat

router = APIRouter()


def extract_timestamps(text: str) -> list[dict]:
    patterns = [
        r"(\d{1,2}):(\d{2}):(\d{2})",
        r"(\d{1,2}):(\d{2})",
        r"(\d+\.?\d*)\s*seconds?",
    ]

    timestamps = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            groups = match.groups()
            if len(groups) == 3:
                seconds = int(groups[0]) * 3600 + int(groups[1]) * 60 + int(groups[2])
            elif len(groups) == 2 and ":" in match.group():
                seconds = int(groups[0]) * 60 + int(groups[1])
            else:
                seconds = float(groups[0])

            start = max(0, seconds - 2)
            end_pos = match.end()
            label = text[max(0, match.start() - 30):end_pos + 30].strip()
            timestamps.append({"time": start, "label": label})

    return timestamps


@router.post("")
async def chat(request: ChatRequest, user=Depends(get_current_user)):
    pool = get_pool()

    async with pool.acquire() as conn:
        file_row = await conn.fetchrow(
            "SELECT id, file_type FROM files WHERE id = $1 AND user_id = $2 AND status = 'ready'",
            request.file_id, user["id"]
        )
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found or not ready")

    results = search_index(user["id"], request.question, top_k=5)

    if not results:
        raise HTTPException(status_code=400, detail="No indexed content found")

    chunk_ids = [r[0] for r in results]
    async with pool.acquire() as conn:
        chunks = await conn.fetch(
            "SELECT id, content, start_time, end_time, page_number FROM chunks WHERE id = ANY($1::int[]) AND file_id = $2",
            chunk_ids, request.file_id
        )

    if not chunks:
        raise HTTPException(status_code=400, detail="No matching content found")

    context_parts = []
    for chunk in chunks:
        prefix = ""
        if chunk["start_time"] is not None:
            minutes = int(chunk["start_time"] // 60)
            seconds = int(chunk["start_time"] % 60)
            prefix = f"[{minutes}:{seconds:02d}] "
        elif chunk["page_number"] is not None:
            prefix = f"[Page {chunk['page_number']}] "
        context_parts.append(f"{prefix}{chunk['content']}")

    context = "\n\n".join(context_parts)

    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO messages (user_id, file_id, role, content) VALUES ($1, $2, 'user', $3)",
            user["id"], request.file_id, request.question
        )

    full_response = []
    file_type = file_row["file_type"]

    async def event_generator():
        async for token in stream_chat(request.question, context):
            full_response.append(token)
            yield {"data": json.dumps({"token": token})}

        response_text = "".join(full_response)
        timestamps = []
        if file_type in ("audio", "video"):
            timestamps = extract_timestamps(response_text)
            for chunk in chunks:
                if chunk["start_time"] is not None:
                    timestamps.append({
                        "time": chunk["start_time"],
                        "label": chunk["content"][:50] + "..."
                    })

        pool2 = get_pool()
        async with pool2.acquire() as conn:
            await conn.execute(
                "INSERT INTO messages (user_id, file_id, role, content, timestamps) VALUES ($1, $2, 'assistant', $3, $4)",
                user["id"], request.file_id, response_text,
                json.dumps(timestamps) if timestamps else None
            )

        yield {"data": json.dumps({"done": True, "timestamps": timestamps})}

    return EventSourceResponse(event_generator())


@router.get("/history/{file_id}")
async def chat_history(file_id: int, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        file_row = await conn.fetchrow(
            "SELECT id FROM files WHERE id = $1 AND user_id = $2", file_id, user["id"]
        )
        if not file_row:
            raise HTTPException(status_code=404, detail="File not found")

        messages = await conn.fetch(
            "SELECT role, content, timestamps, created_at FROM messages WHERE file_id = $1 AND user_id = $2 ORDER BY created_at",
            file_id, user["id"]
        )

    return [
        {
            "role": m["role"],
            "content": m["content"],
            "timestamps": json.loads(m["timestamps"]) if m["timestamps"] else [],
            "created_at": m["created_at"].isoformat(),
        }
        for m in messages
    ]
