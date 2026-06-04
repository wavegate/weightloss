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
  fiber_g: number
}

/** General daily fiber guideline (grams); not tied to calorie budget. */
export const DAILY_FIBER_TARGET_G = 25

/** Local calendar date (YYYY-MM-DD), not UTC from toISOString(). */
export function todayIsoDate(): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function getUserTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone
}

/**
 * Map a stored DB date to the user's local calendar day (mirrors backend logic).
 * Legacy rows used UTC calendar dates; when stored is ahead of local today,
 * reinterpret as UTC midnight in the browser's local timezone.
 */
export function effectiveFoodLocalDate(
  storedIso: string,
  localToday: string,
): string {
  if (storedIso <= localToday) {
    return storedIso
  }

  const [y, m, d] = storedIso.split('-').map(Number)
  const utcMs = Date.UTC(y, m - 1, d)
  const local = new Date(utcMs)
  const shifted = [
    local.getFullYear(),
    String(local.getMonth() + 1).padStart(2, '0'),
    String(local.getDate()).padStart(2, '0'),
  ].join('-')

  if (shifted <= localToday) {
    return shifted
  }

  return storedIso
}

function formatIsoFromLocalDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function addDays(isoDate: string, days: number): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  const date = new Date(year, month - 1, day)
  date.setDate(date.getDate() + days)
  return formatIsoFromLocalDate(date)
}

/** Inclusive range of `count` local calendar days ending on `endDate`. */
export function lastNDaysIso(endDate: string, count: number): string[] {
  const dates: string[] = []
  for (let offset = count - 1; offset >= 0; offset -= 1) {
    dates.push(addDays(endDate, -offset))
  }
  return dates
}

export function sumFoodEntriesForLocalDate(
  entries: FoodEntry[],
  localDate: string,
  localToday: string = todayIsoDate(),
): MacroTotals {
  return entries
    .filter(
      (entry) =>
        effectiveFoodLocalDate(entry.recorded_at, localToday) === localDate,
    )
    .reduce(
      (acc, entry) => ({
        calories: acc.calories + entry.calories,
        protein_g: acc.protein_g + entry.protein_g,
        carbs_g: acc.carbs_g + entry.carbs_g,
        fat_g: acc.fat_g + entry.fat_g,
        fiber_g: acc.fiber_g + entry.fiber_g,
      }),
      { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0 },
    )
}

export function sumFoodEntriesForLocalToday(
  entries: FoodEntry[],
  localToday: string = todayIsoDate(),
): MacroTotals {
  return sumFoodEntriesForLocalDate(entries, localToday, localToday)
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
        fiber_g: acc.fiber_g + entry.fiber_g,
      }),
      { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0, fiber_g: 0 },
    )
}

export function macroTargetsFromTdee(tdeeKcal: number): MacroTotals {
  return {
    calories: tdeeKcal,
    protein_g: Math.round((tdeeKcal * MACRO_SPLIT.protein) / 4),
    carbs_g: Math.round((tdeeKcal * MACRO_SPLIT.carbs) / 4),
    fat_g: Math.round((tdeeKcal * MACRO_SPLIT.fat) / 9),
    fiber_g: DAILY_FIBER_TARGET_G,
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
