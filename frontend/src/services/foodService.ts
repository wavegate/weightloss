import { apiGet, apiPost } from './api'

export type FoodEntry = {
  id: number
  recorded_at: string
  name: string
  description: string
  calories: number
  protein_g: number
  carbs_g: number
  fat_g: number
  estimation_notes: string | null
}

export type FoodEntryInput = {
  recorded_at: string
  name: string
  description: string
}

export function fetchFoodEntries(): Promise<FoodEntry[]> {
  return apiGet<FoodEntry[]>('/foods')
}

export function createFoodEntry(input: FoodEntryInput): Promise<FoodEntry> {
  return apiPost<FoodEntry, FoodEntryInput>('/foods', input)
}
