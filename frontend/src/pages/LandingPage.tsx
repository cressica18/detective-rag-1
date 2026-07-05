import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useCaseStore } from '@/store/caseStore'
import { generateCaseId } from '@/lib/utils'

export function LandingPage() {
  const navigate = useNavigate()
  const { setCaseId, setCaseName } = useCaseStore()

  const handleNewCase = () => {
    navigate('/upload')
  }

  const handleSampleCase = () => {
    // Pre-load the sample case ID if known, otherwise send to upload
    navigate('/upload?sample=true')
  }

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center lamp-glow-bg"
      style={{ backgroundColor: 'var(--bg-void)' }}
    >
      {/* Desk surface effect */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="w-full max-w-2xl px-8"
      >
        {/* Top classification label */}
        <div
          className="font-stamp text-xs tracking-widest mb-8 text-center"
          style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
        >
          RETRIEVAL-AUGMENTED INVESTIGATION SYSTEM — VERSION 1.0
        </div>

        {/* Main case file card */}
        <div
          className="relative px-10 py-12"
          style={{
            backgroundColor: 'var(--bg-panel)',
            border: '1px solid var(--divider)',
            borderTop: '3px solid var(--accent-amber)',
          }}
        >
          {/* Case stamp top-right */}
          <div
            className="absolute top-4 right-6 font-stamp text-xs tracking-wider"
            style={{ color: 'var(--accent-amber-dim)', fontSize: '0.58rem' }}
          >
            CASE FILE SYSTEM
          </div>

          {/* Main title */}
          <motion.h1
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1, duration: 0.3 }}
            className="font-report text-4xl tracking-widest uppercase mb-3"
            style={{ color: 'var(--text-primary)', lineHeight: '1.1' }}
          >
            DetectiveRAG
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.3 }}
            className="font-stamp text-sm tracking-widest uppercase mb-1"
            style={{ color: 'var(--accent-amber)', fontSize: '0.7rem' }}
          >
            Investigation File System
          </motion.p>

          {/* Divider */}
          <div
            className="my-6"
            style={{ borderTop: '1px solid var(--divider)' }}
          />

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.25, duration: 0.3 }}
            className="font-reading text-sm leading-relaxed mb-8"
            style={{ color: 'var(--text-muted)', maxWidth: '480px' }}
          >
            Upload case documents — police reports, witness statements, forensic
            records, CCTV transcripts — and interrogate them using retrieval-augmented
            reasoning. Detect contradictions, reconstruct timelines, and identify suspects.
          </motion.p>

          {/* Primary CTA */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.35, duration: 0.25 }}
            className="flex flex-col gap-3"
          >
            <button
              id="btn-new-case"
              onClick={handleNewCase}
              className="font-stamp tracking-widest uppercase py-3 px-8 text-sm transition-all hover:opacity-90 active:scale-98"
              style={{
                backgroundColor: 'var(--accent-amber)',
                color: 'var(--bg-void)',
                border: 'none',
                borderRadius: '1px',
                cursor: 'pointer',
                fontSize: '0.75rem',
                letterSpacing: '0.15em',
                alignSelf: 'flex-start',
              }}
            >
              OPEN NEW CASE FILE
            </button>

            <button
              id="btn-sample-case"
              onClick={handleSampleCase}
              className="font-stamp tracking-widest uppercase py-2.5 px-6 text-sm transition-all hover:opacity-80"
              style={{
                backgroundColor: 'transparent',
                color: 'var(--text-muted)',
                border: '1px solid var(--divider)',
                borderRadius: '1px',
                cursor: 'pointer',
                fontSize: '0.68rem',
                letterSpacing: '0.12em',
                alignSelf: 'flex-start',
              }}
            >
              REVIEW SAMPLE CASE — THE RIVERSIDE MUSEUM MURDER
            </button>
          </motion.div>

          {/* Feature tags at bottom */}
          <div className="mt-10 flex gap-3 flex-wrap">
            {['RETRIEVAL-GROUNDED', 'CONTRADICTION DETECTION', 'TIMELINE RECONSTRUCTION', 'SUSPECT ANALYSIS'].map((tag) => (
              <span
                key={tag}
                className="evidence-tag"
                style={{ fontSize: '0.55rem' }}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Footer label */}
        <div
          className="font-stamp text-xs text-center mt-6"
          style={{ color: 'var(--divider)', fontSize: '0.55rem' }}
        >
          DETECTIVERAG — POWERED BY GEMINI + CHROMADB + SENTENCE TRANSFORMERS
        </div>
      </motion.div>
    </div>
  )
}
