import { useNavigate, useSearchParams } from 'react-router-dom'
import { useEffect } from 'react'
import { motion } from 'framer-motion'
import { DropZone } from '@/components/upload/DropZone'
import { UploadStepper } from '@/components/upload/UploadStepper'
import { useUploadCase } from '@/hooks/useUploadCase'

export function UploadPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const isSample = searchParams.get('sample') === 'true'

  const { stage, caseId, error, upload } = useUploadCase()

  // Navigate to dashboard when ready
  useEffect(() => {
    if (stage === 'ready') {
      const t = setTimeout(() => navigate('/dashboard'), 1800)
      return () => clearTimeout(t)
    }
  }, [stage, navigate])

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center lamp-glow-bg py-16 px-6"
      style={{ backgroundColor: 'var(--bg-void)' }}
    >
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-xl"
      >
        {/* Header */}
        <div className="mb-8">
          <div
            className="font-stamp text-xs tracking-widest mb-2"
            style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
          >
            DOCUMENT INTAKE — STEP 1 OF 1
          </div>
          <h1
            className="font-report text-2xl tracking-widest uppercase"
            style={{ color: 'var(--text-primary)' }}
          >
            {isSample ? 'Riverside Museum Murder' : 'Open Case File'}
          </h1>
          <p
            className="font-reading text-sm mt-2"
            style={{ color: 'var(--text-muted)' }}
          >
            {isSample
              ? 'Upload the bundled sample case documents to begin the demonstration.'
              : 'Place your case documents into the intake folder below. Accepted: PDF, DOCX, TXT.'}
          </p>
        </div>

        {/* Drop zone — only show when not processing */}
        {stage === 'idle' || stage === 'error' ? (
          <DropZone
            onFiles={(files) => upload(files, isSample ? 'RIVERSIDE MUSEUM MURDER' : undefined)}
            disabled={false}
          />
        ) : null}

        {/* Processing stepper */}
        {stage !== 'idle' && (
          <UploadStepper stage={stage} caseId={caseId} error={error} />
        )}

        {/* Back link */}
        {stage === 'idle' && (
          <button
            onClick={() => navigate('/')}
            className="font-stamp text-xs mt-6 hover:opacity-80 transition-opacity"
            style={{ color: 'var(--text-muted)', fontSize: '0.62rem', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            &larr; RETURN TO FILE INDEX
          </button>
        )}
      </motion.div>
    </div>
  )
}
