import { motion } from 'framer-motion'
import type { DocumentDetail } from '@/lib/api'
import { inferDocType } from '@/lib/utils'
import { useCaseStore } from '@/store/caseStore'

interface DocumentPaneProps {
  document: DocumentDetail
}

export function DocumentPane({ document: doc }: DocumentPaneProps) {
  const { activeCitations } = useCaseStore()

  // Find which chunks are cited in the current chat
  const citedChunkIds = new Set(activeCitations.map((c) => c.chunk_id))

  const docType = doc.doc_type || inferDocType(doc.filename)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.99 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2 }}
      className="h-full overflow-y-auto paper-surface"
      style={{ padding: '2rem 2.5rem' }}
    >
      {/* Document header stamp */}
      <div
        className="border-b pb-3 mb-6"
        style={{ borderColor: '#C7BFA9' }}
      >
        <div
          className="font-stamp text-xs tracking-widest mb-1"
          style={{ color: 'rgba(30, 27, 22, 0.5)', fontSize: '0.62rem' }}
        >
          {docType} — {doc.filename.toUpperCase()}
        </div>
        {doc.page_count != null && (
          <div
            className="font-stamp text-xs"
            style={{ color: 'rgba(30, 27, 22, 0.4)', fontSize: '0.58rem' }}
          >
            {doc.page_count} PAGE{doc.page_count !== 1 ? 'S' : ''} — {doc.chunk_count || 0} SEGMENTS
          </div>
        )}
      </div>

      {/* Chunks with highlight on cited ones */}
      {doc.chunks && doc.chunks.length > 0 ? (
        <div className="space-y-4">
          {doc.chunks.map((chunk) => {
            const isCited = citedChunkIds.has(chunk.chunk_id)
            return (
              <div
                key={chunk.chunk_id}
                className="relative"
              >
                {/* Page marker */}
                <div
                  className="font-stamp text-xs mb-1"
                  style={{
                    color: 'rgba(30, 27, 22, 0.4)',
                    fontSize: '0.56rem',
                    letterSpacing: '0.08em',
                  }}
                >
                  {chunk.page > 0 ? `P.${chunk.page}` : ''} §{chunk.chunk_index + 1}
                  {isCited && (
                    <span
                      className="ml-2"
                      style={{ color: '#8A6636' }}
                    >
                      — RETRIEVED FOR ANALYSIS
                    </span>
                  )}
                </div>

                {/* Chunk text — with highlighter animation if cited */}
                <div
                  className={isCited ? 'highlight-passage' : ''}
                  style={{
                    padding: isCited ? '0.15rem 0.25rem' : '0',
                  }}
                >
                  <p
                    className="font-archive leading-relaxed"
                    style={{
                      color: 'var(--text-on-paper)',
                      fontSize: '0.82rem',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {chunk.text}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        /* Fallback: show full text */
        <p
          className="font-archive leading-relaxed"
          style={{
            color: 'var(--text-on-paper)',
            fontSize: '0.82rem',
            whiteSpace: 'pre-wrap',
          }}
        >
          {doc.full_text}
        </p>
      )}
    </motion.div>
  )
}
