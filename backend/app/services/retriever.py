"""Retriever — embed query and fetch from ChromaDB."""
from app.services import embedder
from app.repositories import chroma_repo
from app.utils.logging import get_logger

logger = get_logger(__name__)


def retrieve(case_id: str, query: str, k: int = 8) -> list[dict]:
    """
    Embed query, search Chroma, return candidate chunk dicts with metadata.
    Each result dict has: chunk_id, text, doc_id, filename, doc_type, page, distance, similarity
    """
    query_embedding = embedder.embed_single(query)
    results = chroma_repo.query_collection(case_id, query_embedding, k=k)

    chunks = []
    if not results or not results.get("ids") or not results["ids"][0]:
        return chunks

    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    for i, (cid, doc, meta, dist) in enumerate(zip(ids, docs, metas, distances)):
        # Cosine distance → similarity (ChromaDB cosine distance: 0=identical, 2=opposite)
        similarity = max(0.0, 1.0 - dist / 2.0)
        chunks.append({
            "chunk_id": cid,
            "text": doc,
            "doc_id": meta.get("doc_id", ""),
            "filename": meta.get("filename", ""),
            "doc_type": meta.get("doc_type", "unknown"),
            "page": meta.get("page", 1),
            "chunk_index": meta.get("chunk_index", i),
            "distance": dist,
            "similarity": similarity,
        })

    return chunks


def retrieve_for_entity(case_id: str, entity_name: str, k: int = 5) -> list[dict]:
    """Retrieve chunks mentioning a specific entity."""
    queries = [
        f"{entity_name} location time",
        f"{entity_name} statement alibi",
        f"{entity_name} evidence",
    ]
    seen = set()
    all_chunks = []
    for q in queries:
        for chunk in retrieve(case_id, q, k=k):
            if chunk["chunk_id"] not in seen and entity_name.lower() in chunk["text"].lower():
                seen.add(chunk["chunk_id"])
                all_chunks.append(chunk)
    return all_chunks[:k]
