import { MeasurementForm } from '../components/MeasurementForm'
import { MeasurementsTable } from '../components/MeasurementsTable'
import { WeightOverTimeChart } from '../components/WeightOverTimeChart'

export function MeasurementsPage() {
  return (
    <div className="flex flex-col gap-8">
      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-slate-400">
          Log measurement
        </h2>
        <MeasurementForm />
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-slate-400">
          Weight over time
        </h2>
        <WeightOverTimeChart />
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-slate-400">
          History
        </h2>
        <MeasurementsTable />
      </section>
    </div>
  )
}
