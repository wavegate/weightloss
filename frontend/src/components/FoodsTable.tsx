import { useDeleteFoodMutation, useFoodsQuery } from '../hooks/useFoods'
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

function FoodRow({
  entry,
  onDelete,
  isDeleting,
}: {
  entry: FoodEntry
  onDelete: (entry: FoodEntry) => void
  isDeleting: boolean
}) {
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
        <br />
        Fi {formatMacro(entry.fiber_g)}g
      </td>
      <td className="px-3 py-3 text-right">
        <button
          type="button"
          onClick={() => onDelete(entry)}
          disabled={isDeleting}
          className="text-sm text-slate-400 transition hover:text-red-400 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label={`Remove ${entry.name}`}
        >
          {isDeleting ? 'Removing…' : 'Remove'}
        </button>
      </td>
    </tr>
  )
}

export function FoodsTable() {
  const foodsQuery = useFoodsQuery()
  const deleteFood = useDeleteFoodMutation()

  const handleDelete = (entry: FoodEntry) => {
    if (
      !window.confirm(
        `Remove "${entry.name}" from your food log? This cannot be undone.`,
      )
    ) {
      return
    }
    deleteFood.mutate(entry.id)
  }

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
    <div className="space-y-3">
      {deleteFood.isError && (
        <p className="text-sm text-red-400">
          {deleteFood.error instanceof Error
            ? deleteFood.error.message
            : 'Failed to remove food entry'}
        </p>
      )}
      <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="text-slate-400">
            <th className="px-3 py-2 font-medium">Date</th>
            <th className="px-3 py-2 font-medium">Food</th>
            <th className="px-3 py-2 font-medium">Calories</th>
            <th className="px-3 py-2 font-medium">Macros</th>
            <th className="px-3 py-2 font-medium" aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <FoodRow
              key={entry.id}
              entry={entry}
              onDelete={handleDelete}
              isDeleting={
                deleteFood.isPending && deleteFood.variables === entry.id
              }
            />
          ))}
        </tbody>
      </table>
      </div>
    </div>
  )
}
