"""ChromaDB repository wrapper."""
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
from typing import Optional
import os

_client: Optional[chromadb.PersistentClient] = None


def get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        os.makedirs(settings.chroma_path, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    return _client


def get_or_create_collection(case_id: str):
    client = get_client()
    collection_name = f"case_{case_id.replace('-', '_')}"
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )


def add_chunks(case_id: str, chunk_ids: list[str], embeddings: list[list[float]],
               documents: list[str], metadatas: list[dict]):
    collection = get_or_create_collection(case_id)
    # ChromaDB add in batches of 1000
    batch_size = 500
    for i in range(0, len(chunk_ids), batch_size):
        collection.add(
            ids=chunk_ids[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size]
        )


def query_collection(case_id: str, query_embedding: list[float], k: int = 8,
                      where: Optional[dict] = None) -> dict:
    collection = get_or_create_collection(case_id)
    count = collection.count()
    k = min(k, max(1, count))
    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": k,
        "include": ["documents", "metadatas", "distances"]
    }
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)


def delete_collection(case_id: str):
    client = get_client()
    collection_name = f"case_{case_id.replace('-', '_')}"
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass


def collection_count(case_id: str) -> int:
    try:
        collection = get_or_create_collection(case_id)
        return collection.count()
    except Exception:
        return 0
