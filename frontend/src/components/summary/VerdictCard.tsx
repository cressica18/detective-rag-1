import { motion } from 'framer-motion'
import type { Suspect } from '@/lib/api'
import { ScoreBar } from '../suspects/ScoreBar'

interface VerdictCardProps {
  primeSuspect: string
  confidence: number
  suspects: Suspect[]
}

export function VerdictCard({ primeSuspect, confidence, suspects }: VerdictCardProps) {
  const suspect = suspects.find(
    (s) => s.name.toLowerCase() === primeSuspect.toLowerCase()
  )

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.4, duration: 0.3 }}
      className="stamp-animate"
      style={{
        border: '2px solid var(--accent-amber-dim)',
        backgroundColor: 'rgba(200, 149, 80, 0.06)',
        borderRadius: '1px',
        padding: '1.25rem',
      }}
    >
      {/* Stamp header */}
      <div
        className="font-stamp text-xs tracking-widest mb-3 pb-2"
        style={{
          color: 'var(--accent-amber)',
          fontSize: '0.62rem',
          borderBottom: '1px solid var(--accent-amber-dim)',
        }}
      >
        PRIME SUSPECT — IDENTIFIED
      </div>

      {/* Silhouette + name */}
      <div className="flex items-center gap-4 mb-4">
        <div
          style={{
            width: '48px',
            height: '48px',
            backgroundColor: 'var(--divider)',
            borderRadius: '1px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <svg width="26" height="32" viewBox="0 0 26 32" fill="none">
            <circle cx="13" cy="8" r="5.5" stroke="var(--accent-amber-dim)" strokeWidth="1.2"/>
            <path d="M2 30 C2 21 24 21 24 30" stroke="var(--accent-amber-dim)" strokeWidth="1.2" fill="none"/>
          </svg>
        </div>

        <div>
          <div
            className="font-report text-xl tracking-widest"
            style={{ color: 'var(--text-primary)' }}
          >
            {primeSuspect.toUpperCase()}
          </div>
          <div
            className="font-stamp text-xs mt-0.5"
            style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
          >
            SUSPICION INDEX: {suspect ? suspect.total_score.toFixed(0) : '--'}/100
          </div>
        </div>
      </div>

      {/* Confidence stamp */}
      <div className="mb-4">
        <div
          className="inline-block font-stamp text-sm px-3 py-1.5"
          style={{
            border: '2px solid var(--signal-red)',
            color: '#B85450',
            fontSize: '0.75rem',
            letterSpacing: '0.12em',
            transform: 'rotate(-1.5deg)',
          }}
        >
          CONFIDENCE: {Math.round(confidence * 100)}%
        </div>
      </div>

      {/* Sub-scores if suspect found */}
      {suspect && (
        <div className="space-y-1">
          <ScoreBar label="OPPORTUNITY" value={suspect.opportunity_score} />
          <ScoreBar label="MOTIVE" value={suspect.motive_score} />
          <ScoreBar label="CONTRADICTIONS" value={suspect.contradiction_count} max={10} variant="contradiction" />
          <ScoreBar label="EVIDENCE STRENGTH" value={suspect.evidence_strength} />
        </div>
      )}
    </motion.div>
  )
}
