"""Chat router — SSE streaming with RAG pipeline."""
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest
from app.services import retriever, reranker, llm_client
from app.services.prompt_builder import SYSTEM_PROMPT, build_chat_prompt
from app.services.citation_engine import extract_citations
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    SSE streaming chat endpoint.
    Events:
      - data: {"type": "token", "content": "..."}
      - data: {"type": "citations", "citations": [...]}
      - data: {"type": "done"}
    """
    case_id = request.case_id
    message = request.message
    history = request.history

    # Retrieve and rerank
    candidates = retriever.retrieve(case_id, message, k=8)
    top_chunks = reranker.rerank(candidates, message, top_k=5)

    if not top_chunks:
        async def no_context_stream():
            yield f"data: {json.dumps({'type': 'token', 'content': 'No relevant documents found in the case file for this query.'})}\n\n"
            yield f"data: {json.dumps({'type': 'citations', 'citations': []})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return StreamingResponse(no_context_stream(), media_type="text/event-stream")

    prompt = build_chat_prompt(top_chunks, message, history)

    async def generate_stream():
        full_text = ""
        try:
            for token in llm_client.generate_stream(prompt, system_instruction=SYSTEM_PROMPT):
                full_text += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # Post-process citations
            cleaned_text, citations = extract_citations(full_text, top_chunks)
            citations_data = [c.model_dump() for c in citations]

            yield f"data: {json.dumps({'type': 'final_answer', 'content': cleaned_text})}\n\n"
            yield f"data: {json.dumps({'type': 'citations', 'citations': citations_data})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
