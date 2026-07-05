// Base API client — wired against the frozen backend routes

const BASE_URL = '/api'

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!res.ok) {
    const body = await res.text()
    throw new Error(`API ${res.status}: ${body}`)
  }

  return res.json() as Promise<T>
}

// ─── Types matching backend Pydantic schemas ─────────────────────────────────

export interface HealthResponse {
  status: string
  version: string
}

export interface UploadResponse {
  case_id: string
  accepted_files: string[]
  rejected_files: string[]
}

export interface DocumentStatus {
  case_id: string
  status: 'parsing' | 'chunking' | 'embedding' | 'indexing' | 'ready' | 'error'
  message?: string
  document_count?: number
}

export interface DocumentMeta {
  doc_id: string
  filename: string
  doc_type: string
  page_count?: number
  chunk_count?: number
  created_at?: string
}

export interface DocumentDetail extends DocumentMeta {
  full_text: string
  chunks: Array<{
    chunk_id: string
    text: string
    page: number
    chunk_index: number
  }>
}

export interface Citation {
  doc_id: string
  filename: string
  page: number | null
  chunk_id: string
  snippet: string
  confidence: number
}

export interface ChatRequest {
  case_id: string
  message: string
  history: Array<{ role: string; content: string }>
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
}

export interface TimelineEvent {
  event_id: string
  timestamp: string
  description: string
  source_doc_ids: string[]
  is_contradicted: boolean
}

export interface Suspect {
  name: string
  opportunity_score: number
  motive_score: number
  contradiction_count: number
  evidence_strength: number
  total_score: number
}

export interface RelationshipEdge {
  source: string
  target: string
  relation_type: string
  evidence_doc_ids: string[]
}

export interface SuspectsResponse {
  suspects: Suspect[]
  edges: RelationshipEdge[]
}

export interface Contradiction {
  id: string
  claim_a: string
  claim_a_source: Citation
  claim_b: string
  claim_b_source: Citation
  explanation: string
}

export interface SummaryResponse {
  summary: string
  verdict: string
  prime_suspect: string
  confidence_pct: number
  citations: Citation[]
}

// ─── API functions ─────────────────────────────────────────────────────────────

export const api = {
  health: () => request<HealthResponse>('/health'),

  uploadFiles: (caseId: string, files: File[]) => {
    const form = new FormData()
    files.forEach((f) => form.append('files', f))
    form.append('case_id', caseId)
    return fetch(`${BASE_URL}/upload`, {
      method: 'POST',
      body: form,
    }).then(async (res) => {
      if (!res.ok) {
        const body = await res.text()
        throw new Error(`Upload failed ${res.status}: ${body}`)
      }
      return res.json() as Promise<UploadResponse>
    })
  },

  getDocumentStatus: (caseId: string) =>
    request<DocumentStatus>(`/documents/status/${caseId}`),

  listDocuments: (caseId: string) =>
    request<DocumentMeta[]>(`/documents/${caseId}`),

  getDocument: (caseId: string, docId: string) =>
    request<DocumentDetail>(`/documents/${caseId}/${docId}`),

  getTimeline: (caseId: string) =>
    request<TimelineEvent[]>(`/timeline/${caseId}`),

  getSuspects: (caseId: string) =>
    request<SuspectsResponse>(`/suspects/${caseId}`),

  getContradictions: (caseId: string) =>
    request<Contradiction[]>(`/contradictions/${caseId}`),

  getSummary: (caseId: string) =>
    request<SummaryResponse>(`/summary/${caseId}`),
}
