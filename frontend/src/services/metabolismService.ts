import { apiGet } from './api'

export type MetabolicProfile = {
  sex: 'male' | 'female'
  age_years: number
  height_cm: number
  activity_level:
    | 'sedentary'
    | 'light'
    | 'moderate'
    | 'active'
    | 'very_active'
  bmr_kcal: number | null
  tdee_kcal: number | null
  notes: string | null
  updated_at: string
}

export function fetchMetabolicProfile() {
  return apiGet<MetabolicProfile | null>('/metabolism/profile')
}
