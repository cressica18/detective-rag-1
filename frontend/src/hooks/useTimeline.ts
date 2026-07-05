import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useCaseStore } from '@/store/caseStore'

export function useTimeline() {
  const caseId = useCaseStore((s) => s.caseId)

  return useQuery({
    queryKey: ['timeline', caseId],
    queryFn: () => api.getTimeline(caseId!),
    enabled: !!caseId,
    staleTime: 5 * 60 * 1000,
  })
}
