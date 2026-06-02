import { useMeasurementsQuery } from '../hooks/useMeasurements'
import type { BodyMeasurement } from '../services/measurementService'

function formatRecordedDate(isoDate: string): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function formatWeight(lbs: number): string {
  return `${lbs.toFixed(1)} lb`
}

function formatWaist(inches: number): string {
  return `${inches.toFixed(1)} in`
}

function MeasurementRow({ measurement }: { measurement: BodyMeasurement }) {
  return (
    <tr className="border-t border-slate-800">
      <td className="px-3 py-3 text-slate-200">
        {formatRecordedDate(measurement.recorded_at)}
      </td>
      <td className="px-3 py-3 text-slate-200">
        {formatWeight(measurement.body_weight_lbs)}
      </td>
      <td className="px-3 py-3 text-slate-200">
        {formatWaist(measurement.waist_inches)}
      </td>
    </tr>
  )
}

export function MeasurementsTable() {
  const measurementsQuery = useMeasurementsQuery()

  if (measurementsQuery.isLoading) {
    return <p className="text-slate-400">Loading measurements…</p>
  }

  if (measurementsQuery.isError) {
    return (
      <p className="text-red-400">
        {measurementsQuery.error instanceof Error
          ? measurementsQuery.error.message
          : 'Failed to load measurements'}
      </p>
    )
  }

  const measurements = measurementsQuery.data ?? []

  if (measurements.length === 0) {
    return <p className="text-slate-400">No measurements yet.</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="text-slate-400">
            <th className="px-3 py-2 font-medium">Date</th>
            <th className="px-3 py-2 font-medium">Body weight</th>
            <th className="px-3 py-2 font-medium">Waist circumference</th>
          </tr>
        </thead>
        <tbody>
          {measurements.map((measurement) => (
            <MeasurementRow key={measurement.id} measurement={measurement} />
          ))}
        </tbody>
      </table>
    </div>
  )
}
