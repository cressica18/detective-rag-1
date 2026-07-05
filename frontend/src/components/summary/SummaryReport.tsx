import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import type { SummaryResponse } from '@/lib/api'
import { CitationChip } from '../chat/CitationChip'

interface SummaryReportProps {
  summary: SummaryResponse
}

export function SummaryReport({ summary }: SummaryReportProps) {
  const [displayedText, setDisplayedText] = useState('')
  const [isTyping, setIsTyping] = useState(true)

  // Typewriter effect for the summary text
  useEffect(() => {
    const text = summary.summary
    let i = 0
    setDisplayedText('')
    setIsTyping(true)

    // Faster reveal: 8 chars at a time
    const interval = setInterval(() => {
      if (i >= text.length) {
        setIsTyping(false)
        clearInterval(interval)
        return
      }
      const chunk = text.slice(i, i + 8)
      setDisplayedText((prev) => prev + chunk)
      i += 8
    }, 16)

    return () => clearInterval(interval)
  }, [summary.summary])

  return (
    <div className="space-y-6">
      {/* Closure Report Header */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div
          className="font-stamp text-xs tracking-widest mb-1"
          style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
        >
          DETECTIVERAG — AUTOMATED CASE ANALYSIS
        </div>
        <div className="flex items-baseline gap-4">
          <h2
            className="font-report text-2xl tracking-widest uppercase"
            style={{ color: 'var(--text-primary)' }}
          >
            Case Closure Report
          </h2>
          <div
            className="font-stamp text-xs"
            style={{
              border: '1px solid var(--accent-amber-dim)',
              color: 'var(--accent-amber)',
              padding: '0.15rem 0.5rem',
              fontSize: '0.62rem',
            }}
          >
            CONFIDENCE: {summary.confidence_pct ?? 0}%
          </div>
        </div>
        <hr style={{ borderColor: 'var(--divider)', marginTop: '0.75rem' }} />
      </motion.div>

      {/* Summary narrative — typewriter reveal */}
      <div
        className={`font-reading text-sm leading-relaxed ${isTyping ? 'typewriter-cursor' : ''}`}
        style={{ color: 'var(--text-primary)', maxWidth: '680px' }}
      >
        {displayedText}
      </div>

      {/* Citations */}
      {summary.citations && summary.citations.length > 0 && !isTyping && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div
            className="font-stamp text-xs tracking-wider mb-2"
            style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
          >
            SUPPORTING EVIDENCE
          </div>
          <div className="flex flex-wrap gap-1.5">
            {summary.citations.map((c, i) => (
              <CitationChip key={c.chunk_id} citation={c} index={i + 1} />
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}
