import { apiGet, apiPut } from './api'

export type PreferenceOption = {
  id: string
  label: string
}

export type EventPreferences = {
  home_location: string
  distance_miles: number
  default_timing: string
  start_date: string | null
  end_date: string | null
  free_only: boolean
  max_price_usd: number | null
  interest_keywords: string
  categories: string[]
  updated_at: string
}

export type EventPreferencesUpsert = Omit<EventPreferences, 'updated_at'>

export type EventPreferenceOptions = {
  locations: PreferenceOption[]
  timings: PreferenceOption[]
  categories: PreferenceOption[]
}

export function fetchEventPreferenceOptions() {
  return apiGet<EventPreferenceOptions>('/events/preferences/options')
}

export function fetchEventPreferences() {
  return apiGet<EventPreferences>('/events/preferences')
}

export function saveEventPreferences(body: EventPreferencesUpsert) {
  return apiPut<EventPreferences, EventPreferencesUpsert>(
    '/events/preferences',
    body,
  )
}
