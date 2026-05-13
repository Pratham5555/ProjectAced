from services.llm_service import generate_text


async def summarize_chunks(chunks: list[str]) -> str:
    combined = "\n".join(chunks[:20])
    prompt = (
        "Summarize the following content in a clear and concise way. "
        "Cover the main topics and key points.\n\n"
        f"{combined}"
    )
    return await generate_text(prompt)
