import type { FoodEntry } from '../services/foodService'

/** Default macro split by calories: 30% protein, 40% carbs, 30% fat. */
export const MACRO_SPLIT = {
  protein: 0.3,
  carbs: 0.4,
  fat: 0.3,
} as const

export type MacroTotals = {
  calories: number
  protein_g: number
  carbs_g: number
  fat_g: number
}

export function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10)
}

export function sumFoodEntriesForDate(
  entries: FoodEntry[],
  date: string,
): MacroTotals {
  return entries
    .filter((entry) => entry.recorded_at === date)
    .reduce(
      (acc, entry) => ({
        calories: acc.calories + entry.calories,
        protein_g: acc.protein_g + entry.protein_g,
        carbs_g: acc.carbs_g + entry.carbs_g,
        fat_g: acc.fat_g + entry.fat_g,
      }),
      { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 },
    )
}

export function macroTargetsFromTdee(tdeeKcal: number): MacroTotals {
  return {
    calories: tdeeKcal,
    protein_g: Math.round((tdeeKcal * MACRO_SPLIT.protein) / 4),
    carbs_g: Math.round((tdeeKcal * MACRO_SPLIT.carbs) / 4),
    fat_g: Math.round((tdeeKcal * MACRO_SPLIT.fat) / 9),
  }
}

export function formatMacroDelta(consumed: number, target: number): string {
  const delta = Math.round(consumed - target)
  if (delta === 0) {
    return 'on target'
  }
  if (delta > 0) {
    return `${delta}g over`
  }
  return `${Math.abs(delta)}g under`
}
