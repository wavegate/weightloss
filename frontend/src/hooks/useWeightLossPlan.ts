import { useQuery } from '@tanstack/react-query'

import { fetchWeightLossPlan } from '../services/metabolismService'

export function useWeightLossPlan() {
  return useQuery({
    queryKey: ['weight-loss-plan'],
    queryFn: fetchWeightLossPlan,
  })
}
