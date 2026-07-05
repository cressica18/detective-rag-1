import { useEffect, useRef, useState, KeyboardEvent } from 'react'
import { useChat } from '@/hooks/useChat'
import { MessageBubble } from './MessageBubble'
import { useCaseStore } from '@/store/caseStore'
import { motion, AnimatePresence } from 'framer-motion'

const STARTER_QUESTIONS = [
  'Where was Marcus Bellweather at 8:00 PM?',
  'What contradictions exist between witness statements?',
  'Who had access to the East Corridor?',
  'What does the forensic evidence indicate about time of death?',
]

export function ChatWindow() {
  const { messages, isLoading, sendMessage } = useChat()
  const { caseStatus } = useCaseStore()
  const [input, setInput] = useState('')
  const [showSources, setShowSources] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const caseReady = caseStatus === 'ready'

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    if (!input.trim() || !caseReady || isLoading) return
    sendMessage(input.trim())
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    // Auto-resize
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`
  }

  // Citations from last assistant message
  const lastAssistantMsg = [...messages].reverse().find((m) => m.role === 'assistant' && !m.isStreaming)
  const currentCitations = lastAssistantMsg?.citations ?? []

  return (
    <div className="flex h-full">
      {/* Main chat pane */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-start justify-center h-full min-h-[200px] gap-6">
              <div>
                <p
                  className="font-stamp text-xs tracking-wider mb-1"
                  style={{ color: 'var(--text-muted)', fontSize: '0.62rem' }}
                >
                  INVESTIGATOR TERMINAL — CASE FILE LOADED
                </p>
                <p
                  className="font-reading text-sm"
                  style={{ color: 'var(--text-primary)', opacity: 0.7 }}
                >
                  {caseReady
                    ? 'Interrogate the case documents below.'
                    : 'Awaiting case file upload.'}
                </p>
              </div>

              {caseReady && (
                <div className="space-y-2">
                  <p
                    className="font-stamp text-xs"
                    style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
                  >
                    SUGGESTED QUERIES:
                  </p>
                  {STARTER_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      onClick={() => { setInput(q); textareaRef.current?.focus() }}
                      className="block text-left font-reading text-sm hover:opacity-100 opacity-60 transition-opacity"
                      style={{ color: 'var(--text-primary)' }}
                    >
                      <span style={{ color: 'var(--accent-amber)' }}>&gt;</span> {q}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div
          className="border-t px-6 py-4"
          style={{ borderColor: 'var(--divider)', backgroundColor: 'var(--bg-charcoal)' }}
        >
          <div className="flex items-start gap-3">
            <span
              className="font-stamp mt-2 flex-shrink-0"
              style={{ color: 'var(--accent-amber)', fontSize: '0.8rem' }}
            >
              &gt;
            </span>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleTextareaInput}
              onKeyDown={handleKeyDown}
              disabled={!caseReady || isLoading}
              placeholder={caseReady ? 'Interrogate the file...' : 'Upload a case file to begin interrogation'}
              rows={1}
              className="chat-input text-sm flex-1 leading-relaxed"
              style={{
                resize: 'none',
                fontSize: '0.875rem',
                paddingTop: '0.375rem',
                paddingBottom: '0.375rem',
                color: !caseReady ? 'var(--text-muted)' : 'var(--text-primary)',
              }}
            />
            <button
              onClick={handleSend}
              disabled={!caseReady || isLoading || !input.trim()}
              className="font-stamp text-xs px-3 py-1.5 transition-all flex-shrink-0 disabled:opacity-30"
              style={{
                border: '1px solid var(--accent-amber-dim)',
                color: 'var(--accent-amber)',
                fontSize: '0.62rem',
                letterSpacing: '0.1em',
                backgroundColor: 'transparent',
                cursor: !caseReady || isLoading || !input.trim() ? 'not-allowed' : 'pointer',
                marginTop: '0.25rem',
              }}
            >
              SEND
            </button>
          </div>
          <p
            className="font-stamp text-xs mt-1.5 ml-6"
            style={{ color: 'var(--text-muted)', fontSize: '0.56rem' }}
          >
            ENTER TO SEND — SHIFT+ENTER FOR NEW LINE
          </p>
        </div>
      </div>

      {/* Sources drawer */}
      <AnimatePresence>
        {showSources && currentCitations.length > 0 && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 240, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-l overflow-hidden flex-shrink-0"
            style={{
              borderColor: 'var(--divider)',
              backgroundColor: 'var(--bg-panel)',
            }}
          >
            <div className="p-4">
              <div
                className="font-stamp text-xs tracking-wider mb-3"
                style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
              >
                SOURCES CONSULTED
              </div>
              <div className="space-y-3">
                {currentCitations.map((c, i) => (
                  <div
                    key={c.chunk_id}
                    className="pb-3"
                    style={{ borderBottom: '1px solid var(--divider)' }}
                  >
                    <div
                      className="font-stamp text-xs mb-1"
                      style={{ color: 'var(--accent-amber)', fontSize: '0.58rem' }}
                    >
                      [{String.fromCharCode(64 + i + 1)}] {c.filename.replace(/\.[^.]+$/, '').toUpperCase()}
                    </div>
                    <p
                      className="font-reading text-xs leading-snug"
                      style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}
                    >
                      {c.snippet.slice(0, 100)}...
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Sources toggle button */}
      {currentCitations.length > 0 && (
        <button
          onClick={() => setShowSources(!showSources)}
          className="absolute right-0 top-1/2 -translate-y-1/2 font-stamp text-xs py-4 px-1.5 transition-all"
          style={{
            backgroundColor: 'var(--bg-panel)',
            color: showSources ? 'var(--accent-amber)' : 'var(--text-muted)',
            border: '1px solid var(--divider)',
            borderRight: 'none',
            fontSize: '0.55rem',
            letterSpacing: '0.15em',
            writingMode: 'vertical-rl',
            position: 'absolute',
            right: showSources ? '240px' : '0',
            transition: 'right 0.2s',
          }}
        >
          SOURCES CONSULTED ({currentCitations.length})
        </button>
      )}
    </div>
  )
}
