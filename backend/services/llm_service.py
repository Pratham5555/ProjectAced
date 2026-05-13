import json
from typing import AsyncGenerator
import httpx
from config import OLLAMA_URL, OLLAMA_MODEL


async def stream_chat(prompt: str, context: str) -> AsyncGenerator[str, None]:
    system_msg = (
        "You are a helpful assistant that answers questions based on the provided context. "
        "If the context contains timestamps, reference them in your answer. "
        "Only use information from the context to answer. "
        "If you cannot find the answer in the context, say so."
    )

    full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "system": system_msg,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue


async def generate_text(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
        )
        data = response.json()
        return data.get("response", "")
