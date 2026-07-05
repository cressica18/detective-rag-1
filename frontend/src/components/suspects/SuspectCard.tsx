import { motion } from 'framer-motion'
import type { Suspect } from '@/lib/api'
import { ScoreBar } from './ScoreBar'

interface SuspectCardProps {
  suspect: Suspect
  index: number
  isSelected?: boolean
  onClick?: () => void
  rank?: number
}

export function SuspectCard({ suspect, index, isSelected, onClick, rank }: SuspectCardProps) {
  const suspicionLevel = suspect.total_score
  const isPrimary = rank === 1

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.2 }}
      onClick={onClick}
      className="cursor-pointer pin-drop"
      style={{
        backgroundColor: isSelected ? 'rgba(200, 149, 80, 0.06)' : 'var(--bg-panel)',
        border: isPrimary
          ? '1px solid var(--accent-amber-dim)'
          : isSelected
          ? '1px solid rgba(200, 149, 80, 0.3)'
          : '1px solid var(--divider)',
        borderRadius: '1px',
        padding: '1rem',
        position: 'relative',
      }}
    >
      {/* Rank stamp for primary suspect */}
      {isPrimary && (
        <div
          className="absolute top-0 right-0 font-stamp text-xs px-1.5 py-0.5"
          style={{
            backgroundColor: 'var(--accent-amber)',
            color: 'var(--bg-void)',
            fontSize: '0.55rem',
            letterSpacing: '0.1em',
          }}
        >
          PRIME SUSPECT
        </div>
      )}

      {/* Silhouette placeholder + name */}
      <div className="flex items-start gap-3 mb-3">
        {/* Person silhouette — geometric, not a cartoon */}
        <div
          className="flex-shrink-0"
          style={{
            width: '36px',
            height: '36px',
            backgroundColor: 'var(--divider)',
            borderRadius: '1px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <svg width="20" height="24" viewBox="0 0 20 24" fill="none">
            <circle cx="10" cy="6" r="4" stroke="var(--text-muted)" strokeWidth="1.2"/>
            <path d="M2 22 C2 16 18 16 18 22" stroke="var(--text-muted)" strokeWidth="1.2" fill="none"/>
          </svg>
        </div>

        <div className="flex-1 min-w-0">
          <div
            className="font-report text-sm tracking-wider truncate"
            style={{ color: 'var(--text-primary)', fontSize: '0.85rem' }}
          >
            {suspect.name.toUpperCase()}
          </div>
          <div
            className="font-stamp text-xs mt-0.5"
            style={{ color: 'var(--text-muted)', fontSize: '0.58rem' }}
          >
            SUSPICION LEVEL: {suspicionLevel.toFixed(0)}/100
          </div>
        </div>
      </div>

      {/* Suspicion gauge */}
      <div className="mb-3">
        <div
          className="h-1.5 w-full"
          style={{ backgroundColor: 'var(--divider)', borderRadius: '0' }}
        >
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, suspicionLevel)}%` }}
            transition={{ delay: index * 0.08 + 0.3, duration: 0.7, ease: 'easeOut' }}
            className="h-full"
            style={{
              backgroundColor:
                suspicionLevel > 70 ? 'var(--signal-red)' :
                suspicionLevel > 40 ? 'var(--accent-amber)' :
                'var(--accent-amber-dim)',
            }}
          />
        </div>
      </div>

      {/* Sub-scores */}
      <div className="space-y-1">
        <ScoreBar label="OPPORTUNITY" value={suspect.opportunity_score} />
        <ScoreBar label="MOTIVE" value={suspect.motive_score} />
        <ScoreBar
          label="CONTRADICTIONS"
          value={suspect.contradiction_count}
          max={10}
          variant="contradiction"
        />
        <ScoreBar label="EVIDENCE STRENGTH" value={suspect.evidence_strength} />
      </div>
    </motion.div>
  )
}
