import { useQuery } from '@tanstack/react-query'

import { fetchMetabolicProfile } from '../services/metabolismService'

export function useMetabolicProfile() {
  return useQuery({
    queryKey: ['metabolic-profile'],
    queryFn: fetchMetabolicProfile,
  })
}
