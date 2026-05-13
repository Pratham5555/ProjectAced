import fitz
from config import CHUNK_SIZE, CHUNK_OVERLAP


def extract_text_from_pdf(file_path: str) -> list[dict]:
    doc = fitz.open(file_path)
    chunks = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if not text.strip():
            continue
        page_chunks = split_text(text, page_number=page_num + 1)
        chunks.extend(page_chunks)
    doc.close()
    return chunks


def split_text(text: str, page_number: int = None,
               start_time: float = None, end_time: float = None) -> list[dict]:
    words = text.split()
    chunks = []
    current = []
    current_len = 0

    for word in words:
        current.append(word)
        current_len += len(word) + 1
        if current_len >= CHUNK_SIZE:
            chunk_text = " ".join(current)
            chunks.append({
                "content": chunk_text,
                "page_number": page_number,
                "start_time": start_time,
                "end_time": end_time,
            })
            overlap_words = current[-CHUNK_OVERLAP // 5:] if len(current) > CHUNK_OVERLAP // 5 else []
            current = list(overlap_words)
            current_len = sum(len(w) + 1 for w in current)

    if current:
        chunk_text = " ".join(current)
        chunks.append({
            "content": chunk_text,
            "page_number": page_number,
            "start_time": start_time,
            "end_time": end_time,
        })

    return chunks
