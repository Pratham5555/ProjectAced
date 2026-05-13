import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, FAISS_DIR

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def encode_texts(texts: list[str]) -> np.ndarray:
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return np.array(embeddings, dtype="float32")


def get_index_path(user_id: int) -> str:
    return os.path.join(FAISS_DIR, f"user_{user_id}.index")


def get_mapping_path(user_id: int) -> str:
    return os.path.join(FAISS_DIR, f"user_{user_id}_map.npy")


def load_index(user_id: int):
    index_path = get_index_path(user_id)
    mapping_path = get_mapping_path(user_id)

    if os.path.exists(index_path) and os.path.exists(mapping_path):
        index = faiss.read_index(index_path)
        chunk_ids = np.load(mapping_path).tolist()
        return index, chunk_ids

    dimension = 384  # all-MiniLM-L6-v2 output dimension
    index = faiss.IndexFlatL2(dimension)
    return index, []


def save_index(user_id: int, index, chunk_ids: list[int]):
    faiss.write_index(index, get_index_path(user_id))
    np.save(get_mapping_path(user_id), np.array(chunk_ids))


def add_to_index(user_id: int, texts: list[str], chunk_ids: list[int]):
    index, existing_ids = load_index(user_id)
    embeddings = encode_texts(texts)
    index.add(embeddings)
    existing_ids.extend(chunk_ids)
    save_index(user_id, index, existing_ids)


def search_index(user_id: int, query: str, top_k: int = 5) -> list[tuple[int, float]]:
    index, chunk_ids = load_index(user_id)
    if index.ntotal == 0:
        return []

    query_embedding = encode_texts([query])
    k = min(top_k, index.ntotal)
    distances, indices = index.search(query_embedding, k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(chunk_ids):
            results.append((chunk_ids[idx], float(distances[0][i])))
    return results


def remove_from_index(user_id: int, chunk_ids_to_remove: list[int]):
    index, chunk_ids = load_index(user_id)
    if not chunk_ids:
        return

    keep_mask = [cid not in set(chunk_ids_to_remove) for cid in chunk_ids]
    if not any(keep_mask):
        dimension = 384
        new_index = faiss.IndexFlatL2(dimension)
        save_index(user_id, new_index, [])
        return

    vectors = faiss.rev_swig_ptr(index.get_xb(), index.ntotal * index.d)
    vectors = vectors.reshape(index.ntotal, index.d)

    new_vectors = vectors[keep_mask]
    new_ids = [cid for cid, keep in zip(chunk_ids, keep_mask) if keep]

    new_index = faiss.IndexFlatL2(index.d)
    new_index.add(np.array(new_vectors, dtype="float32"))
    save_index(user_id, new_index, new_ids)
