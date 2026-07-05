import { NavLink, useNavigate } from 'react-router-dom'
import { useCaseStore } from '@/store/caseStore'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'OVERVIEW', shortLabel: 'CASE' },
  { to: '/chat', label: 'INTERROGATE', shortLabel: 'CHAT' },
  { to: '/timeline', label: 'TIMELINE', shortLabel: 'TIME' },
  { to: '/suspects', label: 'SUSPECTS', shortLabel: 'SUSPE' },
  { to: '/evidence', label: 'EVIDENCE', shortLabel: 'EVID' },
  { to: '/summary', label: 'CASE REPORT', shortLabel: 'RPT' },
]

export function Sidebar() {
  const { caseId, caseName, caseStatus, resetCase } = useCaseStore()
  const navigate = useNavigate()

  const handleNewCase = () => {
    resetCase()
    navigate('/')
  }

  return (
    <aside
      className="flex flex-col h-full border-r"
      style={{
        width: '180px',
        minWidth: '180px',
        backgroundColor: 'var(--bg-charcoal)',
        borderColor: 'var(--divider)',
      }}
    >
      {/* Logo / Case ID */}
      <div
        className="px-4 py-5 border-b"
        style={{ borderColor: 'var(--divider)' }}
      >
        <div
          className="font-report text-sm tracking-widest uppercase mb-1"
          style={{ color: 'var(--accent-amber)' }}
        >
          DetectiveRAG
        </div>
        {caseId && (
          <div
            className="font-stamp text-xs truncate"
            style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
          >
            {caseId}
          </div>
        )}
        {caseName && caseName !== 'UNTITLED CASE' && (
          <div
            className="font-stamp text-xs truncate mt-0.5"
            style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
          >
            {caseName.toUpperCase()}
          </div>
        )}
      </div>

      {/* Status indicator */}
      {caseId && (
        <div
          className="px-4 py-2 border-b"
          style={{ borderColor: 'var(--divider)' }}
        >
          <div
            className={cn(
              'font-stamp text-xs tracking-wider',
              caseStatus === 'ready' ? 'text-signal-green' : 'text-accent-amber-dim'
            )}
            style={{ fontSize: '0.6rem' }}
          >
            {caseStatus === 'ready' ? 'CASE FILE READY' :
             caseStatus === 'processing' ? 'BUILDING FILE...' :
             caseStatus === 'uploading' ? 'RECEIVING DOCS...' :
             caseStatus === 'error' ? 'FILE ERROR' : 'STANDBY'}
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 py-2">
        {NAV_ITEMS.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn('folder-tab block', isActive && 'active')
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer actions */}
      <div
        className="px-4 py-3 border-t"
        style={{ borderColor: 'var(--divider)' }}
      >
        <button
          onClick={handleNewCase}
          className="font-stamp text-xs tracking-wider w-full text-left hover:text-accent-amber transition-colors"
          style={{ color: 'var(--text-muted)', fontSize: '0.62rem' }}
        >
          NEW CASE FILE
        </button>
      </div>
    </aside>
  )
}
