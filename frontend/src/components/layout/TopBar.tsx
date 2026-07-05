import { useCaseStore } from '@/store/caseStore'

export function TopBar() {
  const { caseName, caseId, caseStatus } = useCaseStore()

  return (
    <header
      className="flex items-center justify-between px-6 py-3 border-b flex-shrink-0"
      style={{
        backgroundColor: 'var(--bg-charcoal)',
        borderColor: 'var(--divider)',
        height: '52px',
      }}
    >
      {/* Case name */}
      <div className="flex items-center gap-4">
        <h1
          className="font-report text-base tracking-widest uppercase"
          style={{ color: 'var(--text-primary)' }}
        >
          {caseName || 'UNTITLED CASE'}
        </h1>
        {caseId && (
          <span
            className="evidence-tag"
            style={{ fontSize: '0.6rem' }}
          >
            {caseId}
          </span>
        )}
      </div>

      {/* Status */}
      <div className="flex items-center gap-3">
        {caseStatus !== 'idle' && (
          <>
            <div
              className={`w-1.5 h-1.5 rounded-full ${
                caseStatus === 'ready'
                  ? 'bg-signal-green'
                  : caseStatus === 'error'
                  ? 'bg-signal-red'
                  : 'bg-accent-amber animate-pulse'
              }`}
              style={{
                backgroundColor:
                  caseStatus === 'ready' ? 'var(--signal-green)' :
                  caseStatus === 'error' ? 'var(--signal-red)' :
                  'var(--accent-amber)',
              }}
            />
            <span
              className="font-stamp text-xs tracking-wider"
              style={{
                color: caseStatus === 'ready' ? 'var(--signal-green)' :
                       caseStatus === 'error' ? '#B85450' :
                       'var(--accent-amber)',
                fontSize: '0.62rem',
              }}
            >
              {caseStatus === 'ready' ? 'CASE FILE READY' :
               caseStatus === 'processing' ? 'BUILDING CASE FILE...' :
               caseStatus === 'uploading' ? 'RECEIVING DOCUMENTS...' :
               caseStatus === 'error' ? 'PROCESSING ERROR' : ''}
            </span>
          </>
        )}
      </div>
    </header>
  )
}
