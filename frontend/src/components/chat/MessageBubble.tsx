import { motion } from 'framer-motion'
import { CitationChip } from './CitationChip'
import type { ChatMessage } from '@/hooks/useChat'

interface MessageBubbleProps {
  message: ChatMessage
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18 }}
        className="flex items-start gap-3 py-3"
        style={{ borderBottom: '1px solid var(--divider)' }}
      >
        {/* Query marker */}
        <span
          className="font-stamp flex-shrink-0 mt-0.5"
          style={{ color: 'var(--accent-amber)', fontSize: '0.7rem' }}
        >
          &gt;
        </span>
        <p
          className="font-reading text-sm leading-relaxed"
          style={{ color: 'var(--text-primary)' }}
        >
          {message.content}
        </p>
      </motion.div>
    )
  }

  // Assistant message
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="py-4"
      style={{ borderBottom: '1px solid var(--divider)' }}
    >
      {/* Label */}
      <div
        className="font-stamp text-xs tracking-wider mb-2"
        style={{ color: 'var(--text-muted)', fontSize: '0.6rem' }}
      >
        ANALYSIS
        {message.isStreaming && (
          <span className="ml-2 typewriter-cursor" style={{ color: 'var(--accent-amber)' }} />
        )}
      </div>

      {/* Answer text */}
      <div
        className="font-reading text-sm leading-relaxed whitespace-pre-wrap"
        style={{ color: 'var(--text-primary)' }}
      >
        {message.content}
        {message.isStreaming && !message.content && (
          <span className="typewriter-cursor" />
        )}
      </div>

      {/* Citations */}
      {message.citations && message.citations.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {message.citations.map((c, i) => (
            <CitationChip key={c.chunk_id} citation={c} index={i + 1} />
          ))}
        </div>
      )}
    </motion.div>
  )
}
