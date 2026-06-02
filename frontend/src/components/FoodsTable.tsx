import { useFoodsQuery } from '../hooks/useFoods'
import type { FoodEntry } from '../services/foodService'

function formatRecordedDate(isoDate: string): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function formatMacro(value: number): string {
  return value.toFixed(1)
}

function FoodRow({ entry }: { entry: FoodEntry }) {
  return (
    <tr className="border-t border-slate-800 align-top">
      <td className="px-3 py-3 text-slate-200">
        {formatRecordedDate(entry.recorded_at)}
      </td>
      <td className="px-3 py-3">
        <p className="font-medium text-slate-100">{entry.name}</p>
        <p className="mt-1 text-xs text-slate-400">{entry.description}</p>
      </td>
      <td className="px-3 py-3 text-slate-200">{Math.round(entry.calories)}</td>
      <td className="px-3 py-3 text-slate-200">
        P {formatMacro(entry.protein_g)}g
        <br />
        C {formatMacro(entry.carbs_g)}g
        <br />
        F {formatMacro(entry.fat_g)}g
      </td>
    </tr>
  )
}

export function FoodsTable() {
  const foodsQuery = useFoodsQuery()

  if (foodsQuery.isLoading) {
    return <p className="text-slate-400">Loading food log…</p>
  }

  if (foodsQuery.isError) {
    return (
      <p className="text-red-400">
        {foodsQuery.error instanceof Error
          ? foodsQuery.error.message
          : 'Failed to load food log'}
      </p>
    )
  }

  const entries = foodsQuery.data ?? []

  if (entries.length === 0) {
    return <p className="text-slate-400">No food entries yet.</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="text-slate-400">
            <th className="px-3 py-2 font-medium">Date</th>
            <th className="px-3 py-2 font-medium">Food</th>
            <th className="px-3 py-2 font-medium">Calories</th>
            <th className="px-3 py-2 font-medium">Macros</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <FoodRow key={entry.id} entry={entry} />
          ))}
        </tbody>
      </table>
    </div>
  )
}
