import type { Layout, PlotData } from 'plotly.js'

import type { MacroTotals } from '../lib/nutritionTargets'
import { Plot } from '../lib/plot'

const MACRO_LABELS = ['Protein', 'Carbs', 'Fat', 'Fiber'] as const

type MacroBreakdownChartProps = {
  consumed: Pick<MacroTotals, 'protein_g' | 'carbs_g' | 'fat_g' | 'fiber_g'>
  targets: Pick<MacroTotals, 'protein_g' | 'carbs_g' | 'fat_g' | 'fiber_g'>
}

function macroValues(
  macros: Pick<MacroTotals, 'protein_g' | 'carbs_g' | 'fat_g' | 'fiber_g'>,
): [number, number, number, number] {
  return [macros.protein_g, macros.carbs_g, macros.fat_g, macros.fiber_g]
}

export function MacroBreakdownChart({
  consumed,
  targets,
}: MacroBreakdownChartProps) {
  const consumedValues = macroValues(consumed)
  const targetValues = macroValues(targets)
  const loggedColors = consumedValues.map((value, index) =>
    value > targetValues[index] ? '#f59e0b' : '#8b5cf6',
  )

  const maxValue = Math.max(...consumedValues, ...targetValues, 1)

  const targetTrace: Partial<PlotData> = {
    type: 'bar',
    orientation: 'h',
    y: [...MACRO_LABELS],
    x: targetValues,
    name: 'Target',
    marker: { color: 'rgba(71, 85, 105, 0.55)' },
    hovertemplate: '%{y}<br>Target: %{x:.0f} g<extra></extra>',
  }

  const loggedTrace: Partial<PlotData> = {
    type: 'bar',
    orientation: 'h',
    y: [...MACRO_LABELS],
    x: consumedValues,
    name: 'Logged',
    marker: { color: loggedColors },
    hovertemplate: '%{y}<br>Logged: %{x:.1f} g<extra></extra>',
  }

  const layout: Partial<Layout> = {
    barmode: 'overlay',
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8', family: 'system-ui, sans-serif' },
    xaxis: {
      title: { text: 'Grams' },
      gridcolor: '#334155',
      linecolor: '#475569',
      range: [0, maxValue * 1.15],
    },
    yaxis: {
      automargin: true,
      gridcolor: '#334155',
      linecolor: '#475569',
    },
    margin: { t: 8, r: 16, b: 48, l: 72 },
    height: 280,
    legend: {
      orientation: 'h',
      y: -0.2,
      x: 0,
      font: { size: 11 },
    },
    showlegend: true,
  }

  return (
    <Plot
      data={[targetTrace, loggedTrace]}
      layout={layout}
      config={{ displayModeBar: false, responsive: true }}
      className="w-full"
      useResizeHandler
      style={{ width: '100%' }}
    />
  )
}
