import { useEffect, useState } from 'react'
import {
  fetchEventLocations,
  fetchStoredEventCount,
  streamMeetupSync,
  type MeetupSyncProgress,
} from '../services/eventService'

type SyncStatus = 'idle' | 'syncing' | 'complete' | 'error'

export function EventSyncPanel() {
  const [locations, setLocations] = useState<string[]>(['cupertino'])
  const [location, setLocation] = useState('cupertino')
  const [storedCount, setStoredCount] = useState<number | null>(null)
  const [status, setStatus] = useState<SyncStatus>('idle')
  const [progress, setProgress] = useState<MeetupSyncProgress | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void fetchEventLocations()
      .then((payload) => {
        if (payload.locations.length > 0) {
          setLocations(payload.locations)
        }
      })
      .catch(() => {
        // keep default location list
      })

    void fetchStoredEventCount()
      .then((payload) => setStoredCount(payload.count))
      .catch(() => setStoredCount(null))
  }, [])

  async function handleSync() {
    setStatus('syncing')
    setError(null)
    setProgress(null)

    try {
      const finalUpdate = await streamMeetupSync({ location }, (update) => {
        setProgress(update)
      })
      setStatus('complete')
      setProgress(finalUpdate)
      const countPayload = await fetchStoredEventCount()
      setStoredCount(countPayload.count)
    } catch (syncError) {
      setStatus('error')
      setError(
        syncError instanceof Error ? syncError.message : 'Sync failed unexpectedly',
      )
    }
  }

  const isSyncing = status === 'syncing'

  return (
    <section className="shrink-0 border-b border-slate-800 bg-slate-900/50 px-4 py-3">
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex min-w-[10rem] flex-col gap-1 text-sm">
          <span className="text-slate-400">Location</span>
          <select
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
            value={location}
            disabled={isSyncing}
            onChange={(event) => setLocation(event.target.value)}
          >
            {locations.map((option) => (
              <option key={option} value={option}>
                {option.replace(/-/g, ' ')}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSyncing}
          onClick={() => void handleSync()}
        >
          {isSyncing ? 'Syncing…' : 'Sync Meetup events'}
        </button>

        {storedCount !== null ? (
          <p className="text-sm text-slate-400">
            {storedCount.toLocaleString()} events in database
          </p>
        ) : null}
      </div>

      {progress ? (
        <div className="mt-3 space-y-1 text-sm text-slate-300">
          {progress.message ? <p>{progress.message}</p> : null}
          <p>
            {progress.saved.toLocaleString()} saved ·{' '}
            {progress.skipped.toLocaleString()} duplicates skipped ·{' '}
            {progress.fetched.toLocaleString()} fetched
            {progress.page > 0 ? ` · page ${progress.page}` : ''}
          </p>
        </div>
      ) : null}

      {error ? <p className="mt-2 text-sm text-rose-400">{error}</p> : null}
    </section>
  )
}
