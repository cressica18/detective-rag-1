import { motion } from 'framer-motion'
import { ChatWindow } from '@/components/chat/ChatWindow'
import { useCaseStore } from '@/store/caseStore'
import { useNavigate } from 'react-router-dom'

export function ChatPage() {
  const { caseId, caseStatus } = useCaseStore()
  const navigate = useNavigate()

  if (!caseId) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <p className="font-stamp text-sm" style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
          NO ACTIVE CASE FILE
        </p>
        <button
          onClick={() => navigate('/upload')}
          className="font-stamp text-xs px-4 py-2"
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
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="h-full relative overflow-hidden"
    >
      {/* Page header */}
      <div
        className="px-6 py-3 border-b flex-shrink-0"
        style={{ borderColor: 'var(--divider)' }}
      >
        <div
          className="font-report text-base tracking-widest uppercase"
          style={{ color: 'var(--text-primary)' }}
        >
          Investigator Terminal
        </div>
        <div
          className="font-stamp text-xs"
          style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
        >
          QUERY THE CASE FILE — ANSWERS GROUNDED IN RETRIEVED DOCUMENTS
        </div>
      </div>

      {/* Chat window fills remaining height */}
      <div className="flex-1 overflow-hidden" style={{ height: 'calc(100% - 60px)' }}>
        <ChatWindow />
      </div>
    </motion.div>
  )
}
