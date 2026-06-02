import { FoodForm } from './components/FoodForm'
import { FoodsTable } from './components/FoodsTable'
import { MeasurementForm } from './components/MeasurementForm'
import { MeasurementsTable } from './components/MeasurementsTable'
import { useHealthQuery } from './hooks/useHealth'

function App() {
  const healthQuery = useHealthQuery()

  return (
    <div className="min-h-svh bg-slate-950 px-4 py-10 text-slate-100">
      <div className="mx-auto flex w-full max-w-2xl flex-col gap-8">
        <header className="space-y-1">
          <h1 className="text-3xl font-semibold tracking-tight">Weightloss</h1>
          <p className="text-sm text-slate-400">
            API:{' '}
            {healthQuery.isLoading && 'checking…'}
            {healthQuery.isSuccess && (
              <span className="text-emerald-400">{healthQuery.data.status}</span>
            )}
            {healthQuery.isError && (
              <span className="text-red-400">unreachable</span>
            )}
          </p>
        </header>

        <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-slate-400">
            Log measurement
          </h2>
          <MeasurementForm />
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-slate-400">
            Body measurements
          </h2>
          <MeasurementsTable />
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-slate-400">
            Food log
          </h2>
          <FoodForm />
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-slate-400">
            Food history
          </h2>
          <FoodsTable />
        </section>
      </div>
    </div>
  )
}

export default App
