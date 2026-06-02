import type { Layout, PlotData } from 'plotly.js'

import { useMeasurementsQuery } from '../hooks/useMeasurements'
import { Plot } from '../lib/plot'

function sortByDateAsc(
  measurements: { recorded_at: string; body_weight_lbs: number }[],
) {
  return [...measurements].sort((a, b) =>
    a.recorded_at.localeCompare(b.recorded_at),
  )
}

export function WeightOverTimeChart() {
  const measurementsQuery = useMeasurementsQuery()

  if (measurementsQuery.isLoading) {
    return <p className="text-slate-400">Loading chart…</p>
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

  const sorted = sortByDateAsc(measurementsQuery.data ?? [])

  if (sorted.length === 0) {
    return (
      <p className="text-slate-400">Add measurements to see weight over time.</p>
    )
  }

  const trace: Partial<PlotData> = {
    x: sorted.map((m) => m.recorded_at),
    y: sorted.map((m) => m.body_weight_lbs),
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Body weight',
    line: { color: '#a78bfa', width: 2 },
    marker: { color: '#c4b5fd', size: 8 },
    hovertemplate: '%{x}<br>%{y:.1f} lb<extra></extra>',
  }

  const layout: Partial<Layout> = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8', family: 'system-ui, sans-serif' },
    xaxis: {
      title: { text: 'Date' },
      gridcolor: '#334155',
      linecolor: '#475569',
    },
    yaxis: {
      title: { text: 'Weight (lb)' },
      gridcolor: '#334155',
      linecolor: '#475569',
    },
    margin: { t: 16, r: 16, b: 48, l: 56 },
    height: 320,
    showlegend: false,
  }

  return (
    <Plot
      data={[trace]}
      layout={layout}
      config={{ displayModeBar: false, responsive: true }}
      className="w-full"
      useResizeHandler
      style={{ width: '100%' }}
    />
  )
}
