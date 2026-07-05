from pydantic import BaseModel
from typing import Optional


class UploadResponse(BaseModel):
    case_id: str
    accepted_files: list[str]
    rejected_files: list[str]


class CaseStatusResponse(BaseModel):
    case_id: str
    status: str  # parsing|chunking|embedding|indexing|ready|error
    message: str = ""
    doc_count: int = 0


class DocumentInfo(BaseModel):
    doc_id: str
    case_id: str
    filename: str
    doc_type: str
    page_count: int
    chunk_count: int = 0


class ChunkInfo(BaseModel):
    chunk_id: str
    chunk_index: int
    page: int
    text: str
    char_start: int = 0
    char_end: int = 0


class DocumentDetail(BaseModel):
    doc_id: str
    filename: str
    doc_type: str
    page_count: int
    chunks: list[ChunkInfo]


class Citation(BaseModel):
    doc_id: str
    filename: str
    page: Optional[int] = None
    chunk_id: str
    snippet: str
    confidence: float


class ChatRequest(BaseModel):
    case_id: str
    message: str
    history: list[dict] = []


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]


class TimelineEvent(BaseModel):
    event_id: str
    timestamp: str
    description: str
    source_doc_ids: list[str]
    is_contradicted: bool


class Suspect(BaseModel):
    name: str
    role: str = "unknown"
    opportunity_score: float
    motive_score: float
    contradiction_count: int
    evidence_strength: float
    total_score: float
    motive_summary: str = ""


class RelationshipEdge(BaseModel):
    source: str
    target: str
    relation_type: str
    evidence_doc_ids: list[str]
    weight: float = 1.0


class SuspectsResponse(BaseModel):
    suspects: list[Suspect]
    edges: list[RelationshipEdge]


class Contradiction(BaseModel):
    id: str
    claim_a: str
    claim_a_source: Citation
    claim_b: str
    claim_b_source: Citation
    explanation: str


class SummaryResponse(BaseModel):
    summary: str
    verdict: str
    prime_suspect: str
    confidence_pct: int
    citations: list[Citation]


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
