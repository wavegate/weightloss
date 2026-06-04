import type { Layout, PlotData } from 'plotly.js'

import type { MacroTotals } from '../lib/nutritionTargets'
import { Plot } from '../lib/plot'

export type WeeklyDaySnapshot = {
  date: string
  label: string
  consumed: MacroTotals
  targets: MacroTotals
}

type WeeklyNutritionChartProps = {
  days: WeeklyDaySnapshot[]
}

function shortDayLabel(isoDate: string): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'numeric',
    day: 'numeric',
  })
}

export function WeeklyNutritionChart({ days }: WeeklyNutritionChartProps) {
  const labels = days.map((d) => d.label || shortDayLabel(d.date))
  const calorieConsumed = days.map((d) => Math.round(d.consumed.calories))
  const calorieTarget = days.map((d) => d.targets.calories)
  const calorieColors = days.map((_, index) =>
    calorieConsumed[index] > calorieTarget[index] ? '#f59e0b' : '#8b5cf6',
  )

  const proteinRemaining = days.map(
    (d) => d.targets.protein_g - d.consumed.protein_g,
  )
  const carbsRemaining = days.map((d) => d.targets.carbs_g - d.consumed.carbs_g)
  const fatRemaining = days.map((d) => d.targets.fat_g - d.consumed.fat_g)
  const fiberRemaining = days.map(
    (d) => d.targets.fiber_g - d.consumed.fiber_g,
  )

  const calorieTrace: Partial<PlotData> = {
    type: 'bar',
    x: labels,
    y: calorieConsumed,
    name: 'Logged',
    marker: { color: calorieColors },
    hovertemplate: '%{x}<br>Logged: %{y} kcal<extra></extra>',
  }

  const targetTrace: Partial<PlotData> = {
    type: 'scatter',
    mode: 'lines+markers',
    x: labels,
    y: calorieTarget,
    name: 'Daily target',
    line: { color: '#64748b', width: 2, dash: 'dot' },
    marker: { color: '#94a3b8', size: 6 },
    hovertemplate: '%{x}<br>Target: %{y:.0f} kcal<extra></extra>',
  }

  const calorieLayout: Partial<Layout> = {
    barmode: 'group',
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8', family: 'system-ui, sans-serif' },
    xaxis: {
      tickangle: -30,
      gridcolor: '#334155',
      linecolor: '#475569',
    },
    yaxis: {
      title: { text: 'kcal' },
      gridcolor: '#334155',
      linecolor: '#475569',
    },
    margin: { t: 8, r: 16, b: 64, l: 56 },
    height: 240,
    legend: {
      orientation: 'h',
      y: -0.35,
      x: 0,
      font: { size: 11 },
    },
    showlegend: true,
  }

  const macroRemainingTrace = (
    name: string,
    values: number[],
    color: string,
  ): Partial<PlotData> => ({
    type: 'bar',
    x: labels,
    y: values,
    name,
    marker: { color },
    hovertemplate: `%{x}<br>${name}: %{y:.0f} g left<extra></extra>`,
  })

  const macroLayout: Partial<Layout> = {
    barmode: 'group',
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8', family: 'system-ui, sans-serif' },
    xaxis: {
      tickangle: -30,
      gridcolor: '#334155',
      linecolor: '#475569',
    },
    yaxis: {
      title: { text: 'g remaining' },
      zeroline: true,
      zerolinecolor: '#475569',
      gridcolor: '#334155',
      linecolor: '#475569',
    },
    margin: { t: 8, r: 16, b: 64, l: 56 },
    height: 260,
    legend: {
      orientation: 'h',
      y: -0.35,
      x: 0,
      font: { size: 11 },
    },
    shapes: [
      {
        type: 'line',
        xref: 'paper',
        yref: 'y',
        x0: 0,
        x1: 1,
        y0: 0,
        y1: 0,
        line: { color: '#475569', width: 1 },
      },
    ],
    showlegend: true,
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h3 className="mb-2 text-sm font-medium uppercase tracking-wide text-slate-400">
          Calories
        </h3>
        <Plot
          data={[calorieTrace, targetTrace]}
          layout={calorieLayout}
          config={{ displayModeBar: false, responsive: true }}
          className="w-full"
          useResizeHandler
          style={{ width: '100%' }}
        />
      </div>
      <div>
        <h3 className="mb-2 text-sm font-medium uppercase tracking-wide text-slate-400">
          Macro room (target − logged)
        </h3>
        <p className="mb-2 text-xs text-slate-500">
          Bars above zero mean grams left; below zero means over target.
        </p>
        <Plot
          data={[
            macroRemainingTrace('Protein', proteinRemaining, '#a78bfa'),
            macroRemainingTrace('Carbs', carbsRemaining, '#38bdf8'),
            macroRemainingTrace('Fat', fatRemaining, '#fbbf24'),
            macroRemainingTrace('Fiber', fiberRemaining, '#34d399'),
          ]}
          layout={macroLayout}
          config={{ displayModeBar: false, responsive: true }}
          className="w-full"
          useResizeHandler
          style={{ width: '100%' }}
        />
      </div>
    </div>
  )
}
