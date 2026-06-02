import { useQuery } from '@tanstack/react-query'

import { metabolismKeys } from './metabolismKeys'
import { fetchWeightLossPlan } from '../services/metabolismService'

export function useWeightLossPlan() {
  return useQuery({
    queryKey: metabolismKeys.plan,
    queryFn: fetchWeightLossPlan,
  })
}
