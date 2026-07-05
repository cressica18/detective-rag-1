import { useState } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { SummaryReport } from '@/components/summary/SummaryReport'
import { VerdictCard } from '@/components/summary/VerdictCard'
import { useCaseStore } from '@/store/caseStore'

export function CaseSummaryPage() {
  const caseId = useCaseStore((s) => s.caseId)
  const [requested, setRequested] = useState(false)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['summary', caseId],
    queryFn: () => api.getSummary(caseId!),
    enabled: !!caseId && requested,
    staleTime: 10 * 60 * 1000,
  })

  // Suspects query — needed by VerdictCard to show scores for the prime suspect
  const { data: suspectsData } = useQuery({
    queryKey: ['suspects', caseId],
    queryFn: () => api.getSuspects(caseId!),
    enabled: !!caseId && !!data,
    staleTime: 5 * 60 * 1000,
  })

  if (!caseId) {
    return (
      <div
        className="flex items-center justify-center h-full"
        style={{ color: 'var(--text-muted)' }}
      >
        <div className="text-center">
          <div className="font-stamp text-xs tracking-widest mb-2" style={{ fontSize: '0.65rem' }}>
            NO ACTIVE CASE
          </div>
          <div className="font-reading text-sm" style={{ color: 'var(--text-muted)' }}>
            Open or upload a case file to generate a summary.
          </div>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="h-full overflow-y-auto"
      style={{ padding: '2rem 2.5rem', maxWidth: '1100px' }}
    >
      {/* Page header — stamped closure document */}
      <div className="mb-8">
        <div
          className="font-stamp text-xs tracking-widest mb-2"
          style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
        >
          DETECTIVERAG — CLASSIFIED ANALYSIS
        </div>
        <div className="flex items-center gap-4">
          <h1
            className="font-report text-3xl tracking-widest uppercase"
            style={{ color: 'var(--text-primary)' }}
          >
            Case Closure Report
          </h1>
          {data && (
            <div
              className="font-stamp text-xs px-2 py-1"
              style={{
                border: '1px solid var(--accent-amber-dim)',
                color: 'var(--accent-amber)',
                fontSize: '0.62rem',
              }}
            >
              CONFIDENCE: {data.confidence_pct ?? 0}%
            </div>
          )}
        </div>
        <div style={{ borderTop: '1px solid var(--divider)', marginTop: '0.75rem' }} />
      </div>

      {/* Not yet requested */}
      {!requested && !data && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="flex flex-col items-start gap-4"
        >
          <div
            className="font-reading text-sm leading-relaxed"
            style={{ color: 'var(--text-muted)', maxWidth: '480px' }}
          >
            Generate a comprehensive case analysis synthesizing all retrieved evidence, detected
            contradictions, timeline events, and suspect scores into a detective-style closure report.
          </div>
          <button
            id="btn-generate-summary"
            onClick={() => setRequested(true)}
            className="font-stamp tracking-widest uppercase py-3 px-8 text-sm transition-all hover:opacity-90"
            style={{
              backgroundColor: 'var(--accent-amber)',
              color: 'var(--bg-void)',
              border: 'none',
              borderRadius: '1px',
              cursor: 'pointer',
              fontSize: '0.72rem',
              letterSpacing: '0.15em',
            }}
          >
            GENERATE CASE ANALYSIS
          </button>
        </motion.div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex flex-col items-start gap-3">
          <div
            className="font-stamp text-xs tracking-widest animate-pulse"
            style={{ color: 'var(--accent-amber)', fontSize: '0.65rem' }}
          >
            SYNTHESIZING CASE FILE...
          </div>
          <div className="font-reading text-sm" style={{ color: 'var(--text-muted)' }}>
            Analyzing evidence, contradictions, and suspect profiles...
          </div>
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="flex flex-col items-start gap-3">
          <div className="font-stamp text-xs tracking-widest" style={{ color: 'var(--signal-red)', fontSize: '0.65rem' }}>
            ANALYSIS FAILED
          </div>
          <div className="font-reading text-sm" style={{ color: 'var(--text-muted)' }}>
            {(error as Error).message || 'Unknown error — check backend logs.'}
          </div>
          <button
            onClick={() => refetch()}
            className="font-stamp text-xs tracking-widest py-2 px-4 hover:opacity-80 transition-opacity"
            style={{
              border: '1px solid var(--divider)',
              color: 'var(--text-muted)',
              backgroundColor: 'transparent',
              cursor: 'pointer',
              fontSize: '0.62rem',
            }}
          >
            RETRY ANALYSIS
          </button>
        </div>
      )}

      {/* Success — split layout: SummaryReport + VerdictCard */}
      {data && !isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="flex gap-8 items-start"
        >
          {/* Left: narrative report */}
          <div className="flex-1 min-w-0">
            <SummaryReport summary={data} />
          </div>

          {/* Right: verdict dossier card */}
          <div className="flex-shrink-0" style={{ width: '280px' }}>
            <VerdictCard
              primeSuspect={data.prime_suspect}
              confidence={(data.confidence_pct ?? 0) / 100}
              suspects={suspectsData?.suspects ?? []}
            />
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
