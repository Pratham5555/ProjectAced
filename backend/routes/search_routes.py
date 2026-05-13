from fastapi import APIRouter, Depends
from auth import get_current_user
from database import get_pool
from models import SearchRequest
from services.embedding_service import search_index

router = APIRouter()


@router.post("")
async def semantic_search(request: SearchRequest, user=Depends(get_current_user)):
    results = search_index(user["id"], request.query, top_k=10)

    if not results:
        return []

    chunk_ids = [r[0] for r in results]
    scores = {r[0]: r[1] for r in results}

    pool = get_pool()
    async with pool.acquire() as conn:
        chunks = await conn.fetch(
            """SELECT c.id, c.content, c.start_time, c.end_time, c.page_number,
                      f.id as file_id, f.filename
               FROM chunks c JOIN files f ON c.file_id = f.id
               WHERE c.id = ANY($1::int[]) AND f.user_id = $2""",
            chunk_ids, user["id"]
        )

    return [
        {
            "file_id": c["file_id"],
            "filename": c["filename"],
            "chunk_content": c["content"][:200],
            "score": scores.get(c["id"], 0),
            "start_time": c["start_time"],
            "end_time": c["end_time"],
            "page_number": c["page_number"],
        }
        for c in chunks
    ]
