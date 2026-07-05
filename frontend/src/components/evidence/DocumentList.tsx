import type { DocumentMeta } from '@/lib/api'
import { inferDocType } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface DocumentListProps {
  documents: DocumentMeta[]
  activeDocId: string | null
  onSelect: (docId: string) => void
}

// Group documents by inferred doc type
function groupByType(docs: DocumentMeta[]) {
  const groups: Record<string, DocumentMeta[]> = {}
  for (const doc of docs) {
    const type = doc.doc_type || inferDocType(doc.filename)
    if (!groups[type]) groups[type] = []
    groups[type].push(doc)
  }
  return groups
}

export function DocumentList({ documents, activeDocId, onSelect }: DocumentListProps) {
  const groups = groupByType(documents)

  return (
    <div className="h-full overflow-y-auto">
      {Object.entries(groups).map(([type, docs]) => (
        <div key={type} className="mb-1">
          {/* Group divider — stamped label */}
          <div
            className="px-3 py-1.5 sticky top-0 z-10"
            style={{ backgroundColor: 'var(--bg-charcoal)', borderBottom: '1px solid var(--divider)' }}
          >
            <span
              className="font-stamp text-xs tracking-wider"
              style={{ color: 'var(--accent-brass)', fontSize: '0.58rem' }}
            >
              {type}
            </span>
          </div>

          {/* Doc items */}
          {docs.map((doc) => (
            <button
              key={doc.doc_id}
              onClick={() => onSelect(doc.doc_id)}
              className={cn(
                'w-full text-left px-3 py-2.5 border-b transition-colors',
                activeDocId === doc.doc_id
                  ? 'bg-amber-dim'
                  : 'hover:bg-panel'
              )}
              style={{
                borderColor: 'var(--divider)',
                backgroundColor: activeDocId === doc.doc_id
                  ? 'rgba(200, 149, 80, 0.1)'
                  : 'transparent',
              }}
            >
              <div
                className="font-reading text-xs truncate mb-0.5"
                style={{
                  color: activeDocId === doc.doc_id ? 'var(--accent-amber)' : 'var(--text-primary)',
                  fontSize: '0.75rem',
                }}
              >
                {doc.filename}
              </div>
              {doc.chunk_count != null && (
                <div
                  className="font-stamp text-xs"
                  style={{ color: 'var(--text-muted)', fontSize: '0.58rem' }}
                >
                  {doc.chunk_count} SEGMENTS
                </div>
              )}
            </button>
          ))}
        </div>
      ))}
    </div>
  )
}
