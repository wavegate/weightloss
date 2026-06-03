import { Link } from 'react-router-dom'

import { useFoodsQuery } from '../hooks/useFoods'
import { useMetabolicProfile } from '../hooks/useMetabolicProfile'
import { useWeightLossPlan } from '../hooks/useWeightLossPlan'
import {
  addDays,
  lastNDaysIso,
  macroTargetsFromTdee,
  sumFoodEntriesForLocalDate,
  todayIsoDate,
} from '../lib/nutritionTargets'
import { WeeklyNutritionChart } from './WeeklyNutritionChart'

function formatWeekHeading(endDate: string): string {
  const startDate = addDays(endDate, -6)
  const format = (iso: string) => {
    const [year, month, day] = iso.split('-').map(Number)
    return new Date(year, month - 1, day).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }
  return `${format(startDate)} – ${format(endDate)}`
}

type WeeklyNutritionSummaryProps = {
  weekEndDate: string
}

export function WeeklyNutritionSummary({ weekEndDate }: WeeklyNutritionSummaryProps) {
  const localToday = todayIsoDate()
  const foodsQuery = useFoodsQuery()
  const profileQuery = useMetabolicProfile()
  const planQuery = useWeightLossPlan()

  const isLoading =
    foodsQuery.isLoading || profileQuery.isLoading || planQuery.isLoading
  const isError =
    foodsQuery.isError || profileQuery.isError || planQuery.isError

  if (isLoading) {
    return <p className="text-slate-400">Loading weekly nutrition…</p>
  }

  if (isError) {
    return (
      <p className="text-red-400">
        {foodsQuery.error instanceof Error
          ? foodsQuery.error.message
          : profileQuery.error instanceof Error
            ? profileQuery.error.message
            : 'Failed to load weekly nutrition'}
      </p>
    )
  }

  const profile = profileQuery.data
  const plan = planQuery.data
  const calorieBudget =
    plan?.daily_calorie_target ?? profile?.tdee_kcal ?? null

  if (!calorieBudget) {
    return (
      <div className="rounded-lg border border-dashed border-slate-700 bg-slate-950/40 p-4">
        <p className="text-sm text-slate-300">
          Save a metabolic profile with TDEE to see weekly calories and macros.
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

  const targets = macroTargetsFromTdee(calorieBudget)
  const entries = foodsQuery.data ?? []
  const weekDates = lastNDaysIso(weekEndDate, 7)

  const days = weekDates.map((date) => ({
    date,
    label: '',
    consumed: sumFoodEntriesForLocalDate(entries, date, localToday),
    targets,
  }))

  const totalConsumed = days.reduce((sum, d) => sum + d.consumed.calories, 0)
  const totalTarget = targets.calories * 7
  const weekCaloriesRemaining = Math.round(totalTarget - totalConsumed)
  const daysUnderTarget = days.filter(
    (d) => d.consumed.calories <= targets.calories,
  ).length

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Week
        </p>
        <p className="mt-1 text-sm text-slate-300">
          {formatWeekHeading(weekEndDate)}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2">
          <p className="text-xs uppercase tracking-wide text-slate-500">
            Week calories
          </p>
          <p className="mt-1 text-sm text-slate-100">
            {Math.round(totalConsumed).toLocaleString()} /{' '}
            {Math.round(totalTarget).toLocaleString()} kcal
          </p>
          <p
            className={`mt-0.5 text-xs ${
              weekCaloriesRemaining < 0 ? 'text-amber-400' : 'text-violet-300'
            }`}
          >
            {weekCaloriesRemaining < 0
              ? `${Math.abs(weekCaloriesRemaining).toLocaleString()} kcal over`
              : `${weekCaloriesRemaining.toLocaleString()} kcal left`}
          </p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2">
          <p className="text-xs uppercase tracking-wide text-slate-500">
            Days at or under target
          </p>
          <p className="mt-1 text-sm text-slate-100">
            {daysUnderTarget} / 7
          </p>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2">
          <p className="text-xs uppercase tracking-wide text-slate-500">
            Daily target
          </p>
          <p className="mt-1 text-sm text-slate-100">
            {Math.round(targets.calories).toLocaleString()} kcal
            {plan ? ' (plan)' : ' (TDEE)'}
          </p>
        </div>
      </div>

      <WeeklyNutritionChart days={days} />
    </div>
  )
}
