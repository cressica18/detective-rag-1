import { motion } from 'framer-motion'
import type { TimelineEvent } from '@/lib/api'
import { fmtTimestamp } from '@/lib/utils'

interface EventCardProps {
  event: TimelineEvent
  index: number
  onClick?: () => void
  isSelected?: boolean
}

export function EventCard({ event, index, onClick, isSelected }: EventCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.2 }}
      onClick={onClick}
      className="relative cursor-pointer"
      style={{
        backgroundColor: isSelected ? 'rgba(200, 149, 80, 0.08)' : 'var(--bg-panel)',
        border: isSelected
          ? '1px solid var(--accent-amber-dim)'
          : event.is_contradicted
          ? '1px solid rgba(140, 47, 43, 0.5)'
          : '1px solid var(--divider)',
        borderRadius: '1px',
        padding: '0.75rem 1rem',
      }}
    >
      {/* Contradiction marker */}
      {event.is_contradicted && (
        <div
          className="absolute -top-1 -right-1 w-2.5 h-2.5 contradiction-pulse"
          style={{ backgroundColor: 'var(--signal-red)', borderRadius: '0' }}
          title="Contradiction detected at this timestamp"
        />
      )}

      {/* Time */}
      <div
        className="font-stamp text-xs mb-1"
        style={{
          color: event.is_contradicted ? '#B85450' : 'var(--accent-amber)',
          fontSize: '0.68rem',
          letterSpacing: '0.08em',
        }}
      >
        {fmtTimestamp(event.timestamp)}
        {event.is_contradicted && (
          <span
            className="ml-2 font-stamp"
            style={{ color: '#B85450', fontSize: '0.55rem' }}
          >
            CONTRADICTION
          </span>
        )}
      </div>

      {/* Description */}
      <p
        className="font-reading text-sm leading-snug"
        style={{ color: 'var(--text-primary)', fontSize: '0.8rem' }}
      >
        {event.description}
      </p>

      {/* Sources */}
      {event.source_doc_ids.length > 0 && (
        <div className="mt-1.5">
          <span
            className="font-stamp text-xs"
            style={{ color: 'var(--text-muted)', fontSize: '0.58rem' }}
          >
            SRC: {event.source_doc_ids.length} DOC{event.source_doc_ids.length !== 1 ? 'S' : ''}
          </span>
        </div>
      )}
    </motion.div>
  )
}
