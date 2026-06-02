import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  createFoodEntry,
  deleteFoodEntry,
  fetchFoodEntries,
  type FoodEntryInput,
} from '../services/foodService'

export const foodKeys = {
  all: ['foods'] as const,
}

export function useFoodsQuery() {
  return useQuery({
    queryKey: foodKeys.all,
    queryFn: fetchFoodEntries,
  })
}

export function useCreateFoodMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (input: FoodEntryInput) => createFoodEntry(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: foodKeys.all })
    },
  })
}

export function useDeleteFoodMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => deleteFoodEntry(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: foodKeys.all })
    },
  })
}
