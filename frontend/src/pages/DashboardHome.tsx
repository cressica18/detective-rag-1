import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { useCaseStore } from '@/store/caseStore'
import { api } from '@/lib/api'

export function DashboardHome() {
  const navigate = useNavigate()
  const { caseId, caseName, caseStatus } = useCaseStore()

  const { data: documents } = useQuery({
    queryKey: ['documents', caseId],
    queryFn: () => api.listDocuments(caseId!),
    enabled: !!caseId && caseStatus === 'ready',
  })

  const { data: contradictions } = useQuery({
    queryKey: ['contradictions', caseId],
    queryFn: () => api.getContradictions(caseId!),
    enabled: !!caseId && caseStatus === 'ready',
  })

  const { data: suspects } = useQuery({
    queryKey: ['suspects', caseId],
    queryFn: () => api.getSuspects(caseId!),
    enabled: !!caseId && caseStatus === 'ready',
  })

  const QUICK_ACCESS = [
    { path: '/chat', label: 'INTERROGATE', sub: 'Query the case documents' },
    { path: '/timeline', label: 'TIMELINE', sub: 'Reconstruct chronology' },
    { path: '/suspects', label: 'SUSPECTS', sub: 'Persons of interest' },
    { path: '/evidence', label: 'EVIDENCE', sub: 'Browse source documents' },
    { path: '/summary', label: 'CASE REPORT', sub: 'Final synthesis' },
  ]

  if (!caseId) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <p className="font-stamp text-sm" style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
          NO ACTIVE CASE FILE
        </p>
        <button
          onClick={() => navigate('/upload')}
          className="font-stamp text-xs px-4 py-2 transition-all"
          style={{
            border: '1px solid var(--accent-amber-dim)',
            color: 'var(--accent-amber)',
            fontSize: '0.65rem',
            background: 'none',
            cursor: 'pointer',
          }}
        >
          OPEN CASE FILE
        </button>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      {/* Case at a glance */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        <div
          className="font-stamp text-xs tracking-widest mb-4"
          style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
        >
          CASE AT A GLANCE
        </div>

        {/* Case info form */}
        <div
          className="p-5 mb-6"
          style={{
            backgroundColor: 'var(--bg-panel)',
            border: '1px solid var(--divider)',
          }}
        >
          <div className="grid grid-cols-2 gap-y-3 gap-x-6">
            <Field label="CASE ID" value={caseId} />
            <Field label="STATUS" value={caseStatus.toUpperCase()} />
            <Field
              label="DOCUMENTS"
              value={documents ? String(documents.length) : '--'}
            />
            <Field
              label="CONTRADICTIONS"
              value={contradictions ? String(contradictions.length) : '--'}
              highlight={contradictions && contradictions.length > 0}
            />
            <Field
              label="ACTIVE SUSPECTS"
              value={suspects ? String(suspects.suspects.length) : '--'}
            />
            <Field
              label="PRIME SUSPECT"
              value={
                suspects?.suspects.length
                  ? suspects.suspects.sort((a, b) => b.total_score - a.total_score)[0].name.toUpperCase()
                  : '--'
              }
            />
          </div>
        </div>

        {/* Quick access tiles */}
        <div
          className="font-stamp text-xs tracking-widest mb-3"
          style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
        >
          INVESTIGATION SECTIONS
        </div>

        <div className="grid grid-cols-2 gap-2 lg:grid-cols-3">
          {QUICK_ACCESS.map(({ path, label, sub }, i) => (
            <motion.button
              key={path}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06, duration: 0.18 }}
              onClick={() => navigate(path)}
              className="text-left p-4 transition-all hover:border-amber-dim"
              style={{
                backgroundColor: 'var(--bg-panel)',
                border: '1px solid var(--divider)',
                borderRadius: '1px',
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-amber-dim)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--divider)'
              }}
            >
              <div
                className="font-stamp text-sm tracking-wider mb-1"
                style={{ color: 'var(--accent-amber)', fontSize: '0.72rem' }}
              >
                {label}
              </div>
              <div
                className="font-reading text-xs"
                style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}
              >
                {sub}
              </div>
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  )
}

function Field({
  label,
  value,
  highlight,
}: {
  label: string
  value: string
  highlight?: boolean
}) {
  return (
    <div>
      <div
        className="font-stamp text-xs"
        style={{ color: 'var(--text-muted)', fontSize: '0.58rem', marginBottom: '0.15rem' }}
      >
        {label}
      </div>
      <div
        className="font-stamp text-xs"
        style={{
          color: highlight ? '#B85450' : 'var(--text-primary)',
          fontSize: '0.72rem',
        }}
      >
        {value}
      </div>
    </div>
  )
}
