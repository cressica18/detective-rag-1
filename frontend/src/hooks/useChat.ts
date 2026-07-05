import { useState, useCallback, useRef } from 'react'
import { streamChat } from '@/lib/sse'
import { useCaseStore } from '@/store/caseStore'
import type { Citation } from '@/lib/api'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations: Citation[]
  isStreaming?: boolean
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const abortRef = useRef<(() => void) | null>(null)

  const { caseId, chatHistory, addChatTurn, setActiveCitations } = useCaseStore()

  const sendMessage = useCallback(
    async (text: string) => {
      if (!caseId || !text.trim() || isLoading) return

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: text,
        citations: [],
      }

      const assistantMsgId = `assistant-${Date.now()}`
      const assistantMsg: ChatMessage = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        citations: [],
        isStreaming: true,
      }

      setMessages((prev) => [...prev, userMsg, assistantMsg])
      addChatTurn('user', text)
      setIsLoading(true)

      const abort = streamChat(
        {
          case_id: caseId,
          message: text,
          history: chatHistory,
        },
        {
          onToken: (token) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? { ...m, content: m.content + token }
                  : m
              )
            )
          },
          onDone: (fullText, citations) => {
            const typedCitations = citations as Citation[]
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? { ...m, content: fullText || m.content, citations: typedCitations, isStreaming: false }
                  : m
              )
            )
            addChatTurn('assistant', fullText)
            setActiveCitations(typedCitations)
            setIsLoading(false)
          },
          onError: (err) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? {
                      ...m,
                      content: `[ERROR: ${err.message}]`,
                      isStreaming: false,
                    }
                  : m
              )
            )
            setIsLoading(false)
          },
        }
      )

      abortRef.current = abort
    },
    [caseId, chatHistory, isLoading, addChatTurn, setActiveCitations]
  )

  const abort = useCallback(() => {
    abortRef.current?.()
    setIsLoading(false)
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return { messages, isLoading, sendMessage, abort, clearMessages }
}
