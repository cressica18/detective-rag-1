"""Chunker — wraps LangChain RecursiveCharacterTextSplitter."""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.ids import chunk_id as make_chunk_id

CHUNK_SIZE = 1500  # characters ≈ 500 tokens
CHUNK_OVERLAP = 300  # characters ≈ 100 tokens

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)


def chunk_document(doc_id: str, case_id: str, filename: str, doc_type: str,
                   pages: list[tuple[int, str]]) -> list[dict]:
    """
    Split document pages into chunks.
    Returns list of chunk dicts with all metadata.
    """
    chunks = []
    chunk_idx = 0

    for page_num, text in pages:
        if not text.strip():
            continue
        splits = _splitter.split_text(text)
        char_cursor = 0
        for split_text in splits:
            # Find position in original text for char_start/end tracking
            pos = text.find(split_text, char_cursor)
            char_start = pos if pos >= 0 else char_cursor
            char_end = char_start + len(split_text)
            char_cursor = max(char_end - CHUNK_OVERLAP, char_cursor)

            cid = make_chunk_id(doc_id, chunk_idx)
            chunks.append({
                "chunk_id": cid,
                "doc_id": doc_id,
                "case_id": case_id,
                "chunk_index": chunk_idx,
                "page": page_num,
                "text": split_text,
                "char_start": char_start,
                "char_end": char_end,
                # Metadata for ChromaDB
                "filename": filename,
                "doc_type": doc_type,
            })
            chunk_idx += 1

    return chunks
