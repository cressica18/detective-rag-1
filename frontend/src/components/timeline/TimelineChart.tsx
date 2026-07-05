import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { TimelineEvent } from '@/lib/api'
import { EventCard } from './EventCard'
import { fmtTimestamp } from '@/lib/utils'

interface TimelineChartProps {
  events: TimelineEvent[]
}

export function TimelineChart({ events }: TimelineChartProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const sorted = [...events].sort((a, b) => {
    // Sort by timestamp string, handle "HH:MM PM" style
    return a.timestamp.localeCompare(b.timestamp)
  })

  const selectedEvent = sorted.find((e) => e.event_id === selectedId)
  const contradictions = sorted.filter((e) => e.is_contradicted)

  return (
    <div className="flex h-full gap-0">
      {/* Timeline list (left pane) */}
      <div
        className="flex-1 overflow-y-auto"
        style={{ maxWidth: '520px', minWidth: '320px' }}
      >
        {/* Contradiction summary */}
        {contradictions.length > 0 && (
          <div
            className="mx-4 mt-4 mb-3 px-3 py-2"
            style={{
              border: '1px solid rgba(140, 47, 43, 0.4)',
              backgroundColor: 'rgba(140, 47, 43, 0.08)',
            }}
          >
            <p
              className="font-stamp text-xs"
              style={{ color: '#B85450', fontSize: '0.62rem' }}
            >
              {contradictions.length} TEMPORAL CONTRADICTION{contradictions.length !== 1 ? 'S' : ''} DETECTED
            </p>
          </div>
        )}

        {/* Events */}
        <div className="px-4 pb-4">
          {/* Vertical connecting line */}
          <div className="relative">
            <div
              className="absolute left-3 top-2 bottom-2 w-px"
              style={{ backgroundColor: 'var(--divider)' }}
            />
            <div className="space-y-2 pl-8">
              {sorted.map((event, idx) => (
                <div key={event.event_id} className="relative">
                  {/* Pin dot on the line */}
                  <div
                    className="absolute -left-5 top-4 w-2 h-2"
                    style={{
                      backgroundColor: event.is_contradicted
                        ? 'var(--signal-red)'
                        : 'var(--accent-amber-dim)',
                      borderRadius: '0',
                    }}
                  />
                  <EventCard
                    event={event}
                    index={idx}
                    isSelected={selectedId === event.event_id}
                    onClick={() =>
                      setSelectedId(selectedId === event.event_id ? null : event.event_id)
                    }
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Detail pane */}
      <AnimatePresence>
        {selectedEvent && (
          <motion.div
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 16 }}
            transition={{ duration: 0.2 }}
            className="border-l overflow-y-auto"
            style={{
              width: '320px',
              borderColor: 'var(--divider)',
              backgroundColor: 'var(--bg-panel)',
              padding: '1.5rem',
            }}
          >
            <div
              className="font-stamp text-xs tracking-wider mb-3"
              style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
            >
              EVENT DETAIL
            </div>

            <div
              className="font-stamp text-sm mb-2"
              style={{
                color: selectedEvent.is_contradicted ? '#B85450' : 'var(--accent-amber)',
                fontSize: '0.8rem',
              }}
            >
              {fmtTimestamp(selectedEvent.timestamp)}
            </div>

            <p
              className="font-reading text-sm leading-relaxed mb-4"
              style={{ color: 'var(--text-primary)' }}
            >
              {selectedEvent.description}
            </p>

            {selectedEvent.is_contradicted && (
              <div
                className="px-3 py-2 mb-4"
                style={{
                  border: '1px solid rgba(140, 47, 43, 0.5)',
                  backgroundColor: 'rgba(140, 47, 43, 0.08)',
                }}
              >
                <p
                  className="font-stamp text-xs"
                  style={{ color: '#B85450', fontSize: '0.62rem' }}
                >
                  CONFLICTING ACCOUNTS AT THIS TIMESTAMP
                </p>
                <p
                  className="font-reading text-xs mt-1"
                  style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}
                >
                  See the Contradictions section for full analysis.
                </p>
              </div>
            )}

            <div
              className="font-stamp text-xs"
              style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
            >
              SOURCE DOCUMENTS: {selectedEvent.source_doc_ids.length}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
