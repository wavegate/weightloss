import { apiDelete, apiGet, apiPostForm } from './api'

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
  image?: File | null
}

export function fetchFoodEntries(): Promise<FoodEntry[]> {
  return apiGet<FoodEntry[]>('/foods')
}

export function createFoodEntry(input: FoodEntryInput): Promise<FoodEntry> {
  const form = new FormData()
  form.append('recorded_at', input.recorded_at)
  form.append('name', input.name)
  form.append('description', input.description)
  if (input.image) {
    form.append('image', input.image)
  }
  return apiPostForm<FoodEntry>('/foods', form)
}

export function deleteFoodEntry(id: number): Promise<void> {
  return apiDelete(`/foods/${id}`)
}
