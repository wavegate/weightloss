import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  fetchEventPreferenceOptions,
  fetchEventPreferences,
  saveEventPreferences,
  type EventPreferencesUpsert,
} from '../services/eventPreferencesService'

export const eventPreferencesKeys = {
  all: ['eventPreferences'] as const,
  prefs: () => [...eventPreferencesKeys.all, 'prefs'] as const,
  options: () => [...eventPreferencesKeys.all, 'options'] as const,
}

export function useEventPreferenceOptions() {
  return useQuery({
    queryKey: eventPreferencesKeys.options(),
    queryFn: fetchEventPreferenceOptions,
    staleTime: 1000 * 60 * 60,
  })
}

export function useEventPreferences() {
  return useQuery({
    queryKey: eventPreferencesKeys.prefs(),
    queryFn: fetchEventPreferences,
  })
}

export function useSaveEventPreferences() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: EventPreferencesUpsert) => saveEventPreferences(body),
    onSuccess: (data) => {
      queryClient.setQueryData(eventPreferencesKeys.prefs(), data)
    },
  })
}
