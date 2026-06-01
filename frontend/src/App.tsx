import { useEffect, useState } from 'react'
import { fetchHealth, type HealthStatus } from './services/healthService'

type HealthState =
  | { status: 'loading' }
  | { status: 'success'; data: HealthStatus }
  | { status: 'error'; message: string }

function App() {
  const [health, setHealth] = useState<HealthState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false

    fetchHealth()
      .then((data) => {
        if (!cancelled) {
          setHealth({ status: 'success', data })
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : 'Failed to reach API'
          setHealth({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-slate-950 px-4 text-slate-100">
      <h1 className="text-3xl font-semibold tracking-tight">Weightloss</h1>

      <section
        className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6"
        aria-live="polite"
      >
        <h2 className="text-sm font-medium uppercase tracking-wide text-slate-400">
          API health
        </h2>

        {health.status === 'loading' && (
          <p className="mt-3 text-slate-300">Checking backend…</p>
        )}

        {health.status === 'success' && (
          <p className="mt-3 text-lg">
            Backend status:{' '}
            <span className="font-mono text-emerald-400">
              {health.data.status}
            </span>
          </p>
        )}

        {health.status === 'error' && (
          <p className="mt-3 text-red-400">{health.message}</p>
        )}
      </section>
    </div>
  )
}

export default App
