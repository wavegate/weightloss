import { addDays, todayIsoDate } from '../lib/nutritionTargets'

export type NutritionViewMode = 'daily' | 'weekly'

type NutritionDateNavProps = {
  selectedDate: string
  onSelectedDateChange: (date: string) => void
  viewMode: NutritionViewMode
  onViewModeChange: (mode: NutritionViewMode) => void
}

const viewModeButtonClass = (active: boolean) =>
  active
    ? 'bg-violet-600 text-white'
    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'

export function NutritionDateNav({
  selectedDate,
  onSelectedDateChange,
  viewMode,
  onViewModeChange,
}: NutritionDateNavProps) {
  const today = todayIsoDate()
  const step = viewMode === 'weekly' ? 7 : 1
  const isToday = selectedDate === today
  const canGoForward = addDays(selectedDate, step) <= today

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
      <div className="inline-flex rounded-lg border border-slate-700 p-0.5">
        <button
          type="button"
          onClick={() => onViewModeChange('daily')}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${viewModeButtonClass(viewMode === 'daily')}`}
        >
          Day
        </button>
        <button
          type="button"
          onClick={() => onViewModeChange('weekly')}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${viewModeButtonClass(viewMode === 'weekly')}`}
        >
          Week
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => onSelectedDateChange(addDays(selectedDate, -step))}
          className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 transition hover:bg-slate-700"
          aria-label={viewMode === 'weekly' ? 'Previous week' : 'Previous day'}
        >
          ←
        </button>
        <input
          type="date"
          value={selectedDate}
          max={today}
          onChange={(event) => {
            const next = event.target.value
            if (next) {
              onSelectedDateChange(next > today ? today : next)
            }
          }}
          className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm text-slate-100"
          aria-label="Select date"
        />
        <button
          type="button"
          onClick={() => onSelectedDateChange(addDays(selectedDate, step))}
          disabled={!canGoForward}
          className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
          aria-label={viewMode === 'weekly' ? 'Next week' : 'Next day'}
        >
          →
        </button>
        <button
          type="button"
          onClick={() => onSelectedDateChange(today)}
          disabled={isToday}
          className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-violet-400 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Today
        </button>
      </div>
    </div>
  )
}
