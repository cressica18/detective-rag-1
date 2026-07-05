import { motion } from 'framer-motion'
import type { UploadStage } from '@/hooks/useUploadCase'

interface UploadStepperProps {
  stage: UploadStage
  caseId: string | null
  error: string | null
}

const STAGES: Array<{ key: UploadStage; label: string }> = [
  { key: 'uploading', label: 'RECEIVED' },
  { key: 'parsing', label: 'PARSED' },
  { key: 'chunking', label: 'SEGMENTED' },
  { key: 'embedding', label: 'INDEXED' },
  { key: 'indexing', label: 'CATALOGUED' },
  { key: 'ready', label: 'READY' },
]

const STAGE_ORDER = ['uploading', 'parsing', 'chunking', 'embedding', 'indexing', 'ready']

function getStageIndex(stage: UploadStage): number {
  return STAGE_ORDER.indexOf(stage)
}

export function UploadStepper({ stage, caseId, error }: UploadStepperProps) {
  const currentIdx = getStageIndex(stage)

  if (stage === 'idle') return null

  return (
    <div className="mt-8">
      {/* Case ID stamp */}
      {caseId && (
        <motion.div
          initial={{ opacity: 0, scale: 1.1 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mb-6"
        >
          <span
            className="font-stamp text-xs tracking-widest"
            style={{ color: 'var(--accent-amber)', fontSize: '0.68rem' }}
          >
            FILE OPENED — {caseId}
          </span>
        </motion.div>
      )}

      {/* Stage indicators */}
      <div className="space-y-2">
        {STAGES.map(({ key, label }, idx) => {
          const isDone = currentIdx > idx
          const isCurrent = currentIdx === idx
          const isPending = currentIdx < idx

          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: isPending ? 0.35 : 1, x: 0 }}
              transition={{ delay: idx * 0.08, duration: 0.2 }}
              className="flex items-center gap-3"
            >
              {/* Status glyph */}
              <div
                className="w-4 h-4 flex items-center justify-center flex-shrink-0"
                style={{ fontSize: '0.65rem' }}
              >
                {isDone ? (
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <polyline points="2,7 5,10 12,4" stroke="var(--signal-green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                ) : isCurrent ? (
                  <div
                    className="w-2 h-2 rounded-full animate-pulse"
                    style={{ backgroundColor: 'var(--accent-amber)' }}
                  />
                ) : (
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: 'var(--divider)' }}
                  />
                )}
              </div>

              {/* Stage label */}
              <span
                className="font-stamp text-xs tracking-wider"
                style={{
                  color: isDone ? 'var(--signal-green)' :
                         isCurrent ? 'var(--accent-amber)' :
                         'var(--text-muted)',
                  fontSize: '0.68rem',
                }}
              >
                {label}
              </span>

              {/* Stamp mark for done stages */}
              {isDone && (
                <motion.span
                  initial={{ opacity: 0, scale: 1.2 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="font-stamp text-xs"
                  style={{ color: 'var(--signal-green)', fontSize: '0.55rem', letterSpacing: '0.1em' }}
                >
                  — COMPLETE
                </motion.span>
              )}
            </motion.div>
          )
        })}
      </div>

      {/* Error state */}
      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 px-3 py-2"
          style={{
            border: '1px solid var(--signal-red)',
            backgroundColor: 'rgba(140, 47, 43, 0.1)',
          }}
        >
          <p className="font-stamp text-xs" style={{ color: '#B85450', fontSize: '0.65rem' }}>
            PROCESSING ERROR — {error}
          </p>
        </motion.div>
      )}

      {/* Ready state */}
      {stage === 'ready' && (
        <motion.div
          initial={{ opacity: 0, scale: 1.05 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mt-6 px-3 py-2 stamp-animate"
          style={{
            border: '2px solid var(--signal-green)',
            backgroundColor: 'rgba(92, 107, 79, 0.1)',
            display: 'inline-block',
          }}
        >
          <p
            className="font-stamp text-sm tracking-widest"
            style={{ color: 'var(--signal-green)', fontSize: '0.75rem' }}
          >
            CASE FILE READY FOR INTERROGATION
          </p>
        </motion.div>
      )}
    </div>
  )
}
