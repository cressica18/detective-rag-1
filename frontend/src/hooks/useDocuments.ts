import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useCaseStore } from '@/store/caseStore'

export function useDocuments() {
  const caseId = useCaseStore((s) => s.caseId)

  return useQuery({
    queryKey: ['documents', caseId],
    queryFn: () => api.listDocuments(caseId!),
    enabled: !!caseId,
    staleTime: 2 * 60 * 1000,
  })
}

export function useDocument(docId: string | null) {
  const caseId = useCaseStore((s) => s.caseId)

  return useQuery({
    queryKey: ['document', caseId, docId],
    queryFn: () => api.getDocument(caseId!, docId!),
    enabled: !!caseId && !!docId,
    staleTime: 10 * 60 * 1000,
  })
}
