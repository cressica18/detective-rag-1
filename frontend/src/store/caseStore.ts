import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Citation } from '@/lib/api'

interface CaseStore {
  // Active case
  caseId: string | null
  caseName: string
  caseStatus: 'idle' | 'uploading' | 'processing' | 'ready' | 'error'

  // Chat history (for context window)
  chatHistory: Array<{ role: string; content: string }>

  // Active document in Evidence Viewer
  activeDocId: string | null

  // Highlighted citations from current chat answer
  activeCitations: Citation[]

  // Actions
  setCaseId: (id: string) => void
  setCaseName: (name: string) => void
  setCaseStatus: (status: CaseStore['caseStatus']) => void
  addChatTurn: (role: string, content: string) => void
  clearChatHistory: () => void
  setActiveDocId: (id: string | null) => void
  setActiveCitations: (citations: Citation[]) => void
  resetCase: () => void
}

export const useCaseStore = create<CaseStore>()(
  persist(
    (set) => ({
      caseId: null,
      caseName: 'UNTITLED CASE',
      caseStatus: 'idle',
      chatHistory: [],
      activeDocId: null,
      activeCitations: [],

      setCaseId: (id) => set({ caseId: id }),
      setCaseName: (name) => set({ caseName: name }),
      setCaseStatus: (status) => set({ caseStatus: status }),

      addChatTurn: (role, content) =>
        set((state) => ({
          chatHistory: [
            ...state.chatHistory.slice(-20), // keep last 20 turns for context
            { role, content },
          ],
        })),

      clearChatHistory: () => set({ chatHistory: [] }),

      setActiveDocId: (id) => set({ activeDocId: id }),

      setActiveCitations: (citations) => set({ activeCitations: citations }),

      resetCase: () =>
        set({
          caseId: null,
          caseName: 'UNTITLED CASE',
          caseStatus: 'idle',
          chatHistory: [],
          activeDocId: null,
          activeCitations: [],
        }),
    }),
    {
      name: 'detective-rag-case',
      partialize: (state) => ({
        caseId: state.caseId,
        caseName: state.caseName,
        chatHistory: state.chatHistory,
      }),
    }
  )
)
