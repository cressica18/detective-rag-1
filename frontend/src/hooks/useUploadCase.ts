import { useState, useCallback } from 'react'
import { api, type UploadResponse, type DocumentStatus } from '@/lib/api'
import { useCaseStore } from '@/store/caseStore'
import { generateCaseId } from '@/lib/utils'

export type UploadStage = 'idle' | 'uploading' | 'parsing' | 'chunking' | 'embedding' | 'indexing' | 'ready' | 'error'

interface UploadState {
  stage: UploadStage
  caseId: string | null
  error: string | null
  uploadResponse: UploadResponse | null
}

export function useUploadCase() {
  const [state, setState] = useState<UploadState>({
    stage: 'idle',
    caseId: null,
    error: null,
    uploadResponse: null,
  })

  const { setCaseId, setCaseName, setCaseStatus } = useCaseStore()

  const upload = useCallback(async (files: File[], caseName?: string) => {
    const caseId = generateCaseId()
    setState({ stage: 'uploading', caseId, error: null, uploadResponse: null })
    setCaseId(caseId)
    setCaseName(caseName ?? caseId)
    setCaseStatus('uploading')

    try {
      const response = await api.uploadFiles(caseId, files)
      setState((s) => ({ ...s, uploadResponse: response, stage: 'parsing' }))
      setCaseStatus('processing')

      // Poll for status
      await pollStatus(caseId, setState)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setState((s) => ({ ...s, stage: 'error', error: msg }))
      setCaseStatus('error')
    }
  }, [setCaseId, setCaseName, setCaseStatus])

  return { ...state, upload }
}

async function pollStatus(
  caseId: string,
  setState: React.Dispatch<React.SetStateAction<{
    stage: UploadStage
    caseId: string | null
    error: string | null
    uploadResponse: UploadResponse | null
  }>>
): Promise<void> {
  const terminal = new Set(['ready', 'error'])
  
  while (true) {
    await new Promise((r) => setTimeout(r, 1500))
    
    try {
      const status: DocumentStatus = await api.getDocumentStatus(caseId)
      
      setState((s) => ({ ...s, stage: status.status as UploadStage }))
      
      if (terminal.has(status.status)) {
        const { useCaseStore: store } = await import('@/store/caseStore')
        const { setCaseStatus } = store.getState()
        setCaseStatus(status.status === 'ready' ? 'ready' : 'error')
        return
      }
    } catch {
      // Backend might still be processing — continue polling
    }
  }
}
