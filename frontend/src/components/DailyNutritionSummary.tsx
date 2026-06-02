import { Link } from 'react-router-dom'

import { useFoodsQuery } from '../hooks/useFoods'
import { useMetabolicProfile } from '../hooks/useMetabolicProfile'
import {
  formatMacroDelta,
  macroTargetsFromTdee,
  sumFoodEntriesForDate,
  todayIsoDate,
} from '../lib/nutritionTargets'
import { MacroBreakdownChart } from './MacroBreakdownChart'

function formatTodayHeading(isoDate: string): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

function MacroStat({
  label,
  consumed,
  target,
}: {
  label: string
  consumed: number
  target: number
}) {
  const delta = consumed - target
  const deltaClass =
    delta > 0 ? 'text-amber-400' : delta < 0 ? 'text-violet-300' : 'text-slate-400'

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-sm text-slate-100">
        {Math.round(consumed)}g{' '}
        <span className="text-slate-500">/ {target}g target</span>
      </p>
      <p className={`mt-0.5 text-xs ${deltaClass}`}>
        {formatMacroDelta(consumed, target)}
      </p>
    </div>
  )
}

export function DailyNutritionSummary() {
  const today = todayIsoDate()
  const foodsQuery = useFoodsQuery()
  const profileQuery = useMetabolicProfile()

  const isLoading = foodsQuery.isLoading || profileQuery.isLoading
  const isError = foodsQuery.isError || profileQuery.isError

  if (isLoading) {
    return <p className="text-slate-400">Loading today&apos;s nutrition…</p>
  }

  if (isError) {
    return (
      <p className="text-red-400">
        {foodsQuery.error instanceof Error
          ? foodsQuery.error.message
          : profileQuery.error instanceof Error
            ? profileQuery.error.message
            : 'Failed to load nutrition summary'}
      </p>
    )
  }

  const profile = profileQuery.data
  const tdee = profile?.tdee_kcal

  if (!tdee) {
    return (
      <div className="rounded-lg border border-dashed border-slate-700 bg-slate-950/40 p-4">
        <p className="text-sm text-slate-300">
          Save a metabolic profile with TDEE to see calories remaining and macro
          targets.
        </p>
        <Link
          to="/metabolism"
          className="mt-2 inline-block text-sm font-medium text-violet-400 hover:text-violet-300"
        >
          Set up metabolism coach →
        </Link>
      </div>
    )
  }

  const consumed = sumFoodEntriesForDate(foodsQuery.data ?? [], today)
  const targets = macroTargetsFromTdee(tdee)
  const caloriesRemaining = Math.round(targets.calories - consumed.calories)
  const calorieProgress = Math.min(
    100,
    (consumed.calories / targets.calories) * 100,
  )
  const isOverCalories = caloriesRemaining < 0

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Today
        </p>
        <p className="mt-1 text-sm text-slate-300">{formatTodayHeading(today)}</p>
      </div>

      <div>
        <div className="flex flex-wrap items-end justify-between gap-2">
          <p
            className={`text-3xl font-semibold tabular-nums ${
              isOverCalories ? 'text-amber-400' : 'text-violet-300'
            }`}
          >
            {isOverCalories
              ? `${Math.abs(caloriesRemaining).toLocaleString()} kcal over`
              : `${caloriesRemaining.toLocaleString()} kcal left`}
          </p>
          <p className="text-sm text-slate-400">
            {Math.round(consumed.calories).toLocaleString()} /{' '}
            {Math.round(targets.calories).toLocaleString()} kcal (TDEE)
          </p>
        </div>
        <div
          className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800"
          role="progressbar"
          aria-valuenow={Math.round(consumed.calories)}
          aria-valuemin={0}
          aria-valuemax={Math.round(targets.calories)}
          aria-label="Calories consumed today"
        >
          <div
            className={`h-full rounded-full transition-all ${
              isOverCalories ? 'bg-amber-500' : 'bg-violet-500'
            }`}
            style={{ width: `${calorieProgress}%` }}
          />
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">
          Macros
        </h3>
        <MacroBreakdownChart
          consumed={{
            protein_g: consumed.protein_g,
            carbs_g: consumed.carbs_g,
            fat_g: consumed.fat_g,
          }}
          targets={{
            protein_g: targets.protein_g,
            carbs_g: targets.carbs_g,
            fat_g: targets.fat_g,
          }}
        />
        <div className="mt-3 grid gap-2 sm:grid-cols-3">
          <MacroStat
            label="Protein"
            consumed={consumed.protein_g}
            target={targets.protein_g}
          />
          <MacroStat
            label="Carbs"
            consumed={consumed.carbs_g}
            target={targets.carbs_g}
          />
          <MacroStat
            label="Fat"
            consumed={consumed.fat_g}
            target={targets.fat_g}
          />
        </div>
        <p className="mt-3 text-xs text-slate-500">
          Macro targets use a 30% protein / 40% carbs / 30% fat split of your
          TDEE.
        </p>
      </div>
    </div>
  )
}
