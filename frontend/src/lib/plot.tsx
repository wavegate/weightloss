import type { FC } from 'react'
import type { Config, Data, Layout } from 'plotly.js'
import factoryModule from 'react-plotly.js/factory'
import plotlyModule from 'plotly.js/dist/plotly'

export type PlotProps = {
  data: Data[]
  layout?: Partial<Layout>
  config?: Partial<Config>
  style?: React.CSSProperties
  className?: string
  useResizeHandler?: boolean
}

function resolveModuleExport<T>(mod: unknown): T {
  if (typeof mod === 'function') {
    return mod as T
  }
  if (mod && typeof mod === 'object' && 'default' in mod) {
    return resolveModuleExport<T>((mod as { default: unknown }).default)
  }
  return mod as T
}

type PlotlyFactory = (plotly: object) => FC<PlotProps>

const createPlotlyComponent = resolveModuleExport<PlotlyFactory>(factoryModule)
const Plotly = resolveModuleExport<object>(plotlyModule)

export const Plot = createPlotlyComponent(Plotly)
