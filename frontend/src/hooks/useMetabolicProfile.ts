import { useQuery } from '@tanstack/react-query'

import { metabolismKeys } from './metabolismKeys'
import { fetchMetabolicProfile } from '../services/metabolismService'

export function useMetabolicProfile() {
  return useQuery({
    queryKey: metabolismKeys.profile,
    queryFn: fetchMetabolicProfile,
  })
}
