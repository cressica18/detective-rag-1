"""Embedder — sentence-transformers/all-MiniLM-L6-v2 singleton."""
from typing import Optional
from app.utils.logging import get_logger

logger = get_logger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        logger.info("Loading sentence-transformers model all-MiniLM-L6-v2...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Model loaded.")
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts. Returns list of 384-dim float vectors."""
    if not texts:
        return []
    model = _get_model()
    batch_size = 32
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embeddings = model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
        all_embeddings.extend(embeddings.tolist())
    return all_embeddings


def embed_single(text: str) -> list[float]:
    """Embed a single text string."""
    return embed([text])[0]
