import { motion } from 'framer-motion'
import { useTimeline } from '@/hooks/useTimeline'
import { TimelineChart } from '@/components/timeline/TimelineChart'
import { useNavigate } from 'react-router-dom'
import { useCaseStore } from '@/store/caseStore'

export function TimelinePage() {
  const { caseId } = useCaseStore()
  const navigate = useNavigate()
  const { data: events, isLoading, error } = useTimeline()

  if (!caseId) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <p className="font-stamp text-sm" style={{ color: 'var(--text-muted)' }}>NO ACTIVE CASE FILE</p>
        <button onClick={() => navigate('/upload')} className="font-stamp text-xs px-4 py-2" style={{ border: '1px solid var(--accent-amber-dim)', color: 'var(--accent-amber)', fontSize: '0.65rem', background: 'none', cursor: 'pointer' }}>OPEN CASE FILE</button>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="h-full flex flex-col"
    >
      {/* Header */}
      <div
        className="px-6 py-3 border-b flex-shrink-0"
        style={{ borderColor: 'var(--divider)' }}
      >
        <h2
          className="font-report text-base tracking-widest uppercase"
          style={{ color: 'var(--text-primary)' }}
        >
          Reconstruction Board
        </h2>
        <div
          className="font-stamp text-xs"
          style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
        >
          CHRONOLOGICAL EVENT RECONSTRUCTION — CONTRADICTION MARKERS SHOWN IN RED
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {isLoading && (
          <div className="flex items-center justify-center h-full">
            <p className="font-stamp text-xs" style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}>
              RECONSTRUCTING TIMELINE...
            </p>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center h-full">
            <p className="font-stamp text-xs" style={{ color: '#B85450', fontSize: '0.65rem' }}>
              FAILED TO LOAD TIMELINE — {(error as Error).message}
            </p>
          </div>
        )}

        {events && <TimelineChart events={events} />}
      </div>
    </motion.div>
  )
}
