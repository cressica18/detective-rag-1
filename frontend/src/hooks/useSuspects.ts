import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useCaseStore } from '@/store/caseStore'

export function useSuspects() {
  const caseId = useCaseStore((s) => s.caseId)

  return useQuery({
    queryKey: ['suspects', caseId],
    queryFn: () => api.getSuspects(caseId!),
    enabled: !!caseId,
    staleTime: 5 * 60 * 1000,
  })
}

export function useContradictions() {
  const caseId = useCaseStore((s) => s.caseId)

  return useQuery({
    queryKey: ['contradictions', caseId],
    queryFn: () => api.getContradictions(caseId!),
    enabled: !!caseId,
    staleTime: 5 * 60 * 1000,
  })
}
