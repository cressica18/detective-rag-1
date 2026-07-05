import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { Citation } from '@/lib/api'
import { fmtConfidence, truncate } from '@/lib/utils'
import { useCaseStore } from '@/store/caseStore'

import { useNavigate } from 'react-router-dom'

interface CitationChipProps {
  citation: Citation
  index: number
}

export function CitationChip({ citation, index }: CitationChipProps) {
  const [expanded, setExpanded] = useState(false)
  const { setActiveDocId } = useCaseStore()
  const navigate = useNavigate()

  return (
    <span className="inline-block">
      <button
        onClick={() => setExpanded(!expanded)}
        className="evidence-tag inline-block hover:opacity-80 transition-opacity cursor-pointer"
        style={{
          fontSize: '0.58rem',
          backgroundColor: expanded ? 'rgba(200, 149, 80, 0.1)' : 'transparent',
        }}
        title={citation.filename}
      >
        EXHIBIT {String.fromCharCode(64 + index)} — {citation.filename.replace(/\.[^.]+$/, '').slice(0, 20).toUpperCase()}
        {citation.page != null && `, P.${citation.page}`}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, y: -4, scaleY: 0.95 }}
            animate={{ opacity: 1, y: 0, scaleY: 1 }}
            exit={{ opacity: 0, y: -4, scaleY: 0.95 }}
            transition={{ duration: 0.15 }}
            className="mt-1 px-3 py-2 paper-surface"
            style={{
              maxWidth: '480px',
              border: '1px solid var(--accent-amber-dim)',
              fontSize: '0.72rem',
              lineHeight: '1.5',
              transformOrigin: 'top',
            }}
          >
            <div
              className="font-stamp text-xs mb-1 flex items-center justify-between"
              style={{ color: 'var(--text-on-paper)', fontSize: '0.58rem', opacity: 0.7 }}
            >
              <span>{citation.filename.toUpperCase()}{citation.page != null ? ` — PAGE ${citation.page}` : ''}</span>
              <span>CONFIDENCE: {fmtConfidence(citation.confidence)}</span>
            </div>
            <p className="font-archive" style={{ color: 'var(--text-on-paper)', fontSize: '0.75rem' }}>
              "{truncate(citation.snippet, 220)}"
            </p>
            <button
              onClick={() => { 
                setActiveDocId(citation.doc_id)
                setExpanded(false)
                navigate('/evidence')
              }}
              className="font-stamp text-xs mt-2 hover:opacity-80"
              style={{ color: 'var(--accent-amber)', fontSize: '0.58rem' }}
            >
              VIEW IN EVIDENCE FILE →
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </span>
  )
}
