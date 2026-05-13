import whisper
from config import WHISPER_MODEL

_model = None


def get_model():
    global _model
    if _model is None:
        _model = whisper.load_model(WHISPER_MODEL)
    return _model


def transcribe_media(file_path: str) -> list[dict]:
    model = get_model()
    result = model.transcribe(file_path)
    segments = result.get("segments", [])

    chunks = []
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue
        chunks.append({
            "content": text,
            "start_time": round(seg["start"], 2),
            "end_time": round(seg["end"], 2),
            "page_number": None,
        })

    return chunks
