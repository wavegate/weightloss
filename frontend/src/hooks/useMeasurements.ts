import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  createMeasurement,
  fetchMeasurements,
  type BodyMeasurementInput,
} from '../services/measurementService'

export const measurementKeys = {
  all: ['measurements'] as const,
}

export function useMeasurementsQuery() {
  return useQuery({
    queryKey: measurementKeys.all,
    queryFn: fetchMeasurements,
  })
}

export function useCreateMeasurementMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (input: BodyMeasurementInput) => createMeasurement(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: measurementKeys.all })
    },
  })
}
