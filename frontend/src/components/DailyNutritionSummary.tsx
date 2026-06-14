import { Link } from 'react-router-dom'

import { useFoodsQuery } from '../hooks/useFoods'
import { useMetabolicProfile } from '../hooks/useMetabolicProfile'
import { useWeightLossPlan } from '../hooks/useWeightLossPlan'
import {
  computeCalorieCarryOver,
  effectiveDailyCalorieBudget,
  formatMacroDelta,
  macroTargetsFromTdee,
  sumFoodEntriesForLocalDate,
  todayIsoDate,
} from '../lib/nutritionTargets'
import { MacroBreakdownChart } from './MacroBreakdownChart'

function formatDayHeading(isoDate: string): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

type DailyNutritionSummaryProps = {
  selectedDate: string
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

export function DailyNutritionSummary({ selectedDate }: DailyNutritionSummaryProps) {
  const today = todayIsoDate()
  const isToday = selectedDate === today
  const foodsQuery = useFoodsQuery()
  const profileQuery = useMetabolicProfile()
  const planQuery = useWeightLossPlan()

  const isLoading =
    foodsQuery.isLoading || profileQuery.isLoading || planQuery.isLoading
  const isError =
    foodsQuery.isError || profileQuery.isError || planQuery.isError

  if (isLoading) {
    return (
      <p className="text-slate-400">
        {isToday ? "Loading today's nutrition…" : 'Loading nutrition…'}
      </p>
    )
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
  const plan = planQuery.data
  const baseCalorieBudget =
    plan?.daily_calorie_target ?? profile?.tdee_kcal ?? null

  if (!baseCalorieBudget) {
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

  const consumed = sumFoodEntriesForLocalDate(
    foodsQuery.data ?? [],
    selectedDate,
    today,
  )
  const carryOver = computeCalorieCarryOver(
    foodsQuery.data ?? [],
    baseCalorieBudget,
    selectedDate,
    today,
  )
  const effectiveCalorieBudget = effectiveDailyCalorieBudget(
    baseCalorieBudget,
    carryOver,
  )
  const targets = macroTargetsFromTdee(baseCalorieBudget)
  const baseBudgetLabel = plan
    ? `${Math.round(plan.daily_calorie_target).toLocaleString()} kcal (plan)`
    : `${Math.round(baseCalorieBudget).toLocaleString()} kcal (TDEE)`
  const caloriesRemaining = Math.round(
    effectiveCalorieBudget - consumed.calories,
  )
  const calorieProgress = Math.min(
    100,
    (consumed.calories / effectiveCalorieBudget) * 100,
  )
  const isOverCalories = caloriesRemaining < 0
  const carryOverLabel =
    carryOver === 0
      ? null
      : carryOver > 0
        ? `+${carryOver.toLocaleString()} kcal carry-over`
        : `${carryOver.toLocaleString()} kcal carry-over`

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          {isToday ? 'Today' : 'Day'}
        </p>
        <p className="mt-1 text-sm text-slate-300">
          {formatDayHeading(selectedDate)}
        </p>
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
            {Math.round(effectiveCalorieBudget).toLocaleString()} kcal expected
          </p>
          <p className="text-xs text-slate-500">
            Base {baseBudgetLabel}
            {carryOverLabel ? ` · ${carryOverLabel} from last 3 days` : null}
          </p>
          {plan ? (
            <p className="mt-1 text-xs text-slate-500">
              {Math.round(plan.daily_deficit_kcal)} kcal/day deficit · goal{' '}
              {plan.target_weight_lbs} lb by {plan.target_date}
            </p>
          ) : null}
        </div>
        <div
          className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800"
          role="progressbar"
          aria-valuenow={Math.round(consumed.calories)}
          aria-valuemin={0}
          aria-valuemax={Math.round(effectiveCalorieBudget)}
          aria-label={
            isToday ? 'Calories consumed today' : 'Calories consumed on selected day'
          }
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
            fiber_g: consumed.fiber_g,
          }}
          targets={{
            protein_g: targets.protein_g,
            carbs_g: targets.carbs_g,
            fat_g: targets.fat_g,
            fiber_g: targets.fiber_g,
          }}
        />
        <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
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
          <MacroStat
            label="Fiber"
            consumed={consumed.fiber_g}
            target={targets.fiber_g}
          />
        </div>
        <p className="mt-3 text-xs text-slate-500">
          Macro targets use a 30% protein / 40% carbs / 30% fat split of your
          {plan ? ' daily calorie plan target' : ' TDEE'}. Fiber target is{' '}
          {targets.fiber_g}g/day (general guideline).
        </p>
      </div>
    </div>
  )
}
