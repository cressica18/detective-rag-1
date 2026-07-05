// SSE streaming client for /chat endpoint

export interface StreamCallbacks {
  onToken: (token: string) => void
  onDone: (fullText: string, citations: unknown[]) => void
  onError: (err: Error) => void
}

export function streamChat(
  payload: { case_id: string; message: string; history: Array<{ role: string; content: string }> },
  callbacks: StreamCallbacks
): () => void {
  let aborted = false
  let buffer = ''

  const controller = new AbortController()

  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
    body: JSON.stringify(payload),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) {
        const body = await res.text()
        callbacks.onError(new Error(`Chat API ${res.status}: ${body}`))
        return
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let fullText = ''
      let citations: unknown[] = []

      while (true) {
        const { done, value } = await reader.read()
        if (done || aborted) break

        buffer += decoder.decode(value, { stream: true })

        // Process SSE lines
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data:')) continue
          const data = line.slice(5).trim()
          if (data === '[DONE]') continue
          
          try {
            const parsed = JSON.parse(data)
            if (parsed.type === 'token') {
              fullText += parsed.content
              callbacks.onToken(parsed.content)
            } else if (parsed.type === 'citations') {
              citations = parsed.content
            } else if (parsed.type === 'error') {
              callbacks.onError(new Error(parsed.content))
            } else if (parsed.type === 'done') {
              // Final payload might include full answer + citations
              if (parsed.answer) fullText = parsed.answer
              if (parsed.citations) citations = parsed.citations
            }
          } catch {
            // Plain text token (non-JSON SSE line)
            if (data && data !== '[DONE]') {
              fullText += data
              callbacks.onToken(data)
            }
          }
        }
      }

      if (!aborted) {
        callbacks.onDone(fullText, citations)
      }
    })
    .catch((err: Error) => {
      if (err.name !== 'AbortError') {
        callbacks.onError(err)
      }
    })

  return () => {
    aborted = true
    controller.abort()
  }
}
