import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { inferDocType } from '@/lib/utils'

interface DropZoneProps {
  onFiles: (files: File[]) => void
  disabled?: boolean
}

export function DropZone({ onFiles, disabled }: DropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [queuedFiles, setQueuedFiles] = useState<File[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  const acceptedTypes = ['.txt', '.pdf', '.docx']
  const maxSizeMB = 20

  const validate = (files: FileList | File[]): File[] => {
    const arr = Array.from(files)
    return arr.filter((f) => {
      const ext = '.' + f.name.split('.').pop()?.toLowerCase()
      const okType = acceptedTypes.includes(ext)
      const okSize = f.size <= maxSizeMB * 1024 * 1024
      return okType && okSize
    })
  }

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragOver(false)
      if (disabled) return
      const valid = validate(e.dataTransfer.files)
      if (valid.length) {
        setQueuedFiles((prev) => {
          const next = [...prev, ...valid]
          return next
        })
      }
    },
    [disabled]
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (!e.target.files || disabled) return
      const valid = validate(e.target.files)
      if (valid.length) setQueuedFiles((prev) => [...prev, ...valid])
    },
    [disabled]
  )

  const removeFile = (idx: number) => {
    setQueuedFiles((prev) => prev.filter((_, i) => i !== idx))
  }

  const handleSubmit = () => {
    if (queuedFiles.length > 0) {
      onFiles(queuedFiles)
    }
  }

  return (
    <div className="space-y-6">
      {/* Drop zone area */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true) }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className="relative cursor-pointer transition-all duration-200"
        style={{
          border: `2px dashed ${isDragOver ? 'var(--accent-amber)' : 'var(--accent-amber-dim)'}`,
          backgroundColor: isDragOver ? 'rgba(200, 149, 80, 0.06)' : 'transparent',
          borderRadius: '2px',
          padding: '3rem 2rem',
          minHeight: '200px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1rem',
        }}
      >
        {/* Folder icon — SVG lines only, no emoji */}
        <svg width="56" height="44" viewBox="0 0 56 44" fill="none" className="opacity-60">
          <rect x="1" y="12" width="54" height="30" rx="2" stroke="var(--accent-amber-dim)" strokeWidth="1.5"/>
          <path d="M1 12 L1 8 Q1 6 3 6 L22 6 L26 12" stroke="var(--accent-amber-dim)" strokeWidth="1.5" fill="none"/>
          {isDragOver && (
            <>
              <path d="M28 28 L28 20 M24 24 L28 20 L32 24" stroke="var(--accent-amber)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </>
          )}
        </svg>

        <div className="text-center">
          <p
            className="font-stamp text-sm tracking-wider mb-1"
            style={{ color: isDragOver ? 'var(--accent-amber)' : 'var(--text-primary)', fontSize: '0.75rem' }}
          >
            {isDragOver ? 'RELEASE TO FILE DOCUMENTS' : 'PLACE DOCUMENTS IN INTAKE FOLDER'}
          </p>
          <p
            className="font-stamp text-xs"
            style={{ color: 'var(--text-muted)', fontSize: '0.65rem' }}
          >
            PDF · DOCX · TXT — MAX 20MB EACH
          </p>
        </div>

        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={handleFileInput}
        />
      </div>

      {/* Queued files list */}
      <AnimatePresence>
        {queuedFiles.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-2"
          >
            <div
              className="font-stamp text-xs tracking-wider mb-3"
              style={{ color: 'var(--text-muted)', fontSize: '0.62rem' }}
            >
              DOCUMENTS QUEUED FOR INTAKE — {queuedFiles.length} FILE{queuedFiles.length !== 1 ? 'S' : ''}
            </div>
            {queuedFiles.map((file, idx) => (
              <motion.div
                key={`${file.name}-${idx}`}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -8 }}
                transition={{ duration: 0.15, delay: idx * 0.03 }}
                className="flex items-center gap-3 px-3 py-2"
                style={{
                  backgroundColor: 'var(--bg-panel)',
                  border: '1px solid var(--divider)',
                  borderRadius: '1px',
                }}
              >
                {/* Doc type tag */}
                <span className="evidence-tag flex-shrink-0" style={{ fontSize: '0.55rem' }}>
                  {inferDocType(file.name)}
                </span>

                {/* Filename */}
                <span
                  className="font-stamp text-xs flex-1 truncate"
                  style={{ color: 'var(--text-primary)', fontSize: '0.68rem' }}
                >
                  {file.name}
                </span>

                {/* File size */}
                <span
                  className="font-stamp text-xs"
                  style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
                >
                  {(file.size / 1024).toFixed(0)}KB
                </span>

                {/* Remove button */}
                <button
                  onClick={(e) => { e.stopPropagation(); removeFile(idx) }}
                  className="ml-1 hover:opacity-100 opacity-40 transition-opacity"
                  style={{ color: 'var(--signal-red)' }}
                  aria-label={`Remove ${file.name}`}
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <line x1="2" y1="2" x2="10" y2="10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                    <line x1="10" y1="2" x2="2" y2="10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                </button>
              </motion.div>
            ))}

            {/* Submit button */}
            <div className="pt-2">
              <button
                onClick={handleSubmit}
                disabled={disabled}
                className="font-stamp tracking-widest uppercase px-6 py-2.5 transition-all duration-150 disabled:opacity-40"
                style={{
                  backgroundColor: 'var(--accent-amber)',
                  color: 'var(--bg-void)',
                  fontSize: '0.7rem',
                  letterSpacing: '0.12em',
                  border: 'none',
                  borderRadius: '1px',
                  cursor: disabled ? 'not-allowed' : 'pointer',
                }}
              >
                OPEN CASE FILE — BEGIN INTAKE
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
