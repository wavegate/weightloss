/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly VITE_CLERK_PUBLISHABLE_KEY: string
  readonly VITE_COPILOT_PUBLIC_LICENSE_KEY?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module 'react-plotly.js/factory' {
  import type { FC } from 'react'
  import type { Config, Data, Layout } from 'plotly.js'

  type PlotParams = {
    data: Data[]
    layout?: Partial<Layout>
    config?: Partial<Config>
    style?: React.CSSProperties
    className?: string
    useResizeHandler?: boolean
  }

  function createPlotlyComponent(plotly: object): FC<PlotParams>

  export default createPlotlyComponent
}

declare module 'plotly.js/dist/plotly' {
  const Plotly: object
  export default Plotly
}
