import { motion } from 'framer-motion'
import { useDocuments, useDocument } from '@/hooks/useDocuments'
import { DocumentList } from '@/components/evidence/DocumentList'
import { DocumentPane } from '@/components/evidence/DocumentPane'
import { useCaseStore } from '@/store/caseStore'

export function EvidenceViewerPage() {
  const caseId = useCaseStore((s) => s.caseId)
  const activeDocId = useCaseStore((s) => s.activeDocId)
  const setActiveDocId = useCaseStore((s) => s.setActiveDocId)

  const { data: documents, isLoading: docsLoading, error: docsError } = useDocuments()
  const { data: activeDoc, isLoading: docLoading } = useDocument(activeDocId)

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
            Open or upload a case file to browse evidence.
          </div>
        </div>
      </div>
    )
  }

  if (docsLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div
          className="font-stamp text-xs tracking-widest animate-pulse"
          style={{ color: 'var(--accent-amber)', fontSize: '0.65rem' }}
        >
          LOADING CASE DOCUMENTS...
        </div>
      </div>
    )
  }

  if (docsError || !documents) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="font-stamp text-xs tracking-widest" style={{ color: 'var(--signal-red)', fontSize: '0.65rem' }}>
          FAILED TO LOAD DOCUMENTS
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="flex h-full overflow-hidden"
    >
      {/* Left: Filing drawer — document list */}
      <div
        className="flex-shrink-0 flex flex-col overflow-hidden"
        style={{
          width: '240px',
          borderRight: '1px solid var(--divider)',
          backgroundColor: 'var(--bg-charcoal)',
        }}
      >
        {/* Drawer header */}
        <div
          className="px-4 py-3 flex-shrink-0"
          style={{ borderBottom: '1px solid var(--divider)' }}
        >
          <div className="font-report text-sm tracking-widest uppercase" style={{ color: 'var(--text-primary)' }}>
            Case Documents
          </div>
          <div className="font-stamp text-xs mt-0.5" style={{ color: 'var(--text-muted)', fontSize: '0.58rem' }}>
            {documents.length} FILE{documents.length !== 1 ? 'S' : ''} INDEXED
          </div>
        </div>

        {/* Document list */}
        <div className="flex-1 overflow-hidden">
          <DocumentList
            documents={documents}
            activeDocId={activeDocId}
            onSelect={setActiveDocId}
          />
        </div>
      </div>

      {/* Right: Document viewer — paper surface */}
      <div className="flex-1 overflow-hidden">
        {activeDocId && docLoading ? (
          <div className="flex items-center justify-center h-full">
            <div
              className="font-stamp text-xs tracking-widest animate-pulse"
              style={{ color: 'var(--accent-amber)', fontSize: '0.65rem' }}
            >
              OPENING DOCUMENT...
            </div>
          </div>
        ) : activeDocId && activeDoc ? (
          <DocumentPane document={activeDoc} />
        ) : (
          <div
            className="flex items-center justify-center h-full"
            style={{ backgroundColor: 'var(--bg-charcoal)' }}
          >
            <div className="text-center">
              <div
                className="font-stamp text-xs tracking-widest mb-1"
                style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
              >
                SELECT A DOCUMENT
              </div>
              <div className="font-reading text-sm" style={{ color: 'var(--divider)' }}>
                Choose a file from the index to open it
              </div>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  )
}
