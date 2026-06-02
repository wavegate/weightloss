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

export type WeightLossPlan = {
  start_weight_lbs: number
  target_weight_lbs: number
  start_date: string
  target_date: string
  tdee_kcal: number
  daily_calorie_target: number
  daily_deficit_kcal: number
  weight_to_lose_lbs: number
  days_until_goal: number
  notes: string | null
  updated_at: string
}

export function fetchMetabolicProfile() {
  return apiGet<MetabolicProfile | null>('/metabolism/profile')
}

export function fetchWeightLossPlan() {
  return apiGet<WeightLossPlan | null>('/metabolism/plan')
}
