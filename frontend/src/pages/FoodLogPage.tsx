import { FoodForm } from '../components/FoodForm'
import { FoodsTable } from '../components/FoodsTable'
import { NutritionDashboard } from '../components/NutritionDashboard'

export function FoodLogPage() {
  return (
    <div className="flex flex-col gap-8">
      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-slate-400">
          Nutrition
        </h2>
        <NutritionDashboard />
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-slate-400">
          Add food
        </h2>
        <FoodForm />
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-slate-400">
          History
        </h2>
        <FoodsTable />
      </section>
    </div>
  )
}
