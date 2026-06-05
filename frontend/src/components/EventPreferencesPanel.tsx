import { useEffect, useState } from 'react'

import {
  useEventPreferenceOptions,
  useEventPreferences,
  useSaveEventPreferences,
} from '../hooks/useEventPreferences'
import type { EventPreferencesUpsert } from '../services/eventPreferencesService'

function labelFor(
  options: { id: string; label: string }[],
  id: string,
): string {
  return options.find((item) => item.id === id)?.label ?? id
}

export function EventPreferencesPanel() {
  const { data: options, isLoading: optionsLoading } = useEventPreferenceOptions()
  const { data: saved, isLoading: prefsLoading } = useEventPreferences()
  const saveMutation = useSaveEventPreferences()

  const [form, setForm] = useState<EventPreferencesUpsert | null>(null)

  useEffect(() => {
    if (saved) {
      setForm({
        home_location: saved.home_location,
        distance_miles: saved.distance_miles,
        default_timing: saved.default_timing,
        start_date: saved.start_date,
        end_date: saved.end_date,
        free_only: saved.free_only,
        max_price_usd: saved.max_price_usd,
        interest_keywords: saved.interest_keywords,
        categories: saved.categories,
      })
    }
  }, [saved])

  if (optionsLoading || prefsLoading || !form || !options) {
    return (
      <div className="flex h-full items-center justify-center p-4 text-sm text-slate-400">
        Loading preferences…
      </div>
    )
  }

  function toggleCategory(categoryId: string) {
    setForm((current) => {
      if (!current) {
        return current
      }
      const has = current.categories.includes(categoryId)
      return {
        ...current,
        categories: has
          ? current.categories.filter((id) => id !== categoryId)
          : [...current.categories, categoryId],
      }
    })
  }

  function normalizeForSave(value: EventPreferencesUpsert): EventPreferencesUpsert {
    const incompleteDateRange =
      value.default_timing === 'date-range' &&
      (!value.start_date || !value.end_date)
    const timing = incompleteDateRange ? 'upcoming' : value.default_timing
    return {
      ...value,
      default_timing: timing,
      start_date: timing === 'date-range' ? value.start_date : null,
      end_date: timing === 'date-range' ? value.end_date : null,
      max_price_usd:
        value.max_price_usd === null || Number.isNaN(value.max_price_usd)
          ? null
          : value.max_price_usd,
    }
  }

  function handleSave() {
    if (!form) {
      return
    }
    saveMutation.mutate(normalizeForSave(form))
  }

  function clearDates() {
    setForm((current) =>
      current
        ? {
            ...current,
            default_timing: 'upcoming',
            start_date: null,
            end_date: null,
          }
        : current,
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-y-auto p-4">
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-slate-100">Your preferences</h2>
        <p className="mt-1 text-xs text-slate-400">
          Used by the event assistant and parallel search across Meetup, Eventbrite,
          Luma, and Funcheap.
        </p>
      </div>

      <form
        className="flex flex-col gap-4"
        onSubmit={(event) => {
          event.preventDefault()
          handleSave()
        }}
      >
        <label className="flex flex-col gap-1 text-xs text-slate-400">
          Home area
          <select
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
            value={form.home_location}
            onChange={(event) =>
              setForm({ ...form, home_location: event.target.value })
            }
          >
            {options.locations.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-400">
          Search radius (miles, Meetup)
          <input
            type="number"
            min={5}
            max={100}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
            value={form.distance_miles}
            onChange={(event) =>
              setForm({
                ...form,
                distance_miles: Number(event.target.value),
              })
            }
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-400">
          Default timing
          <select
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
            value={form.default_timing}
            onChange={(event) => {
              const timing = event.target.value
              setForm({
                ...form,
                default_timing: timing,
                start_date: timing === 'date-range' ? form.start_date : null,
                end_date: timing === 'date-range' ? form.end_date : null,
              })
            }}
          >
            {options.timings.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>

        {form.default_timing === 'date-range' ? (
          <div className="flex flex-col gap-2">
            <div className="grid grid-cols-2 gap-3">
              <label className="flex flex-col gap-1 text-xs text-slate-400">
                From
                <input
                  type="date"
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                  value={form.start_date ?? ''}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      start_date: event.target.value || null,
                    })
                  }
                />
              </label>
              <label className="flex flex-col gap-1 text-xs text-slate-400">
                To
                <input
                  type="date"
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
                  value={form.end_date ?? ''}
                  min={form.start_date ?? undefined}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      end_date: event.target.value || null,
                    })
                  }
                />
              </label>
            </div>
            <button
              type="button"
              onClick={clearDates}
              className="self-start text-xs text-slate-400 underline-offset-2 transition hover:text-slate-200 hover:underline"
            >
              Clear dates
            </button>
          </div>
        ) : null}

        <label className="flex items-center gap-2 text-sm text-slate-200">
          <input
            type="checkbox"
            className="rounded border-slate-600"
            checked={form.free_only}
            onChange={(event) =>
              setForm({ ...form, free_only: event.target.checked })
            }
          />
          Free events only
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-400">
          Max ticket price (USD, optional)
          <input
            type="number"
            min={0}
            step={1}
            placeholder="No limit"
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
            value={form.max_price_usd ?? ''}
            onChange={(event) => {
              const raw = event.target.value
              setForm({
                ...form,
                max_price_usd: raw === '' ? null : Number(raw),
              })
            }}
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-400">
          Extra keywords (Meetup / search)
          <input
            type="text"
            placeholder="e.g. startup, hiking"
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
            value={form.interest_keywords}
            onChange={(event) =>
              setForm({ ...form, interest_keywords: event.target.value })
            }
          />
        </label>

        <fieldset className="flex flex-col gap-2">
          <legend className="text-xs text-slate-400">Event types</legend>
          <div className="flex flex-col gap-2">
            {options.categories.map((item) => (
              <label
                key={item.id}
                className="flex items-center gap-2 text-sm text-slate-200"
              >
                <input
                  type="checkbox"
                  className="rounded border-slate-600"
                  checked={form.categories.includes(item.id)}
                  onChange={() => toggleCategory(item.id)}
                />
                {item.label}
              </label>
            ))}
          </div>
        </fieldset>

        <button
          type="submit"
          disabled={saveMutation.isPending}
          className="rounded-lg bg-violet-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-violet-500 disabled:opacity-60"
        >
          {saveMutation.isPending ? 'Saving…' : 'Save preferences'}
        </button>

        {saveMutation.isError ? (
          <p className="text-xs text-red-400">Could not save. Try again.</p>
        ) : null}
        {saveMutation.isSuccess ? (
          <p className="text-xs text-emerald-400">Preferences saved.</p>
        ) : null}
      </form>

      {saved ? (
        <p className="mt-4 text-xs text-slate-500">
          Active: {labelFor(options.locations, saved.home_location)},{' '}
          {saved.default_timing === 'date-range' && saved.start_date && saved.end_date
            ? `${saved.start_date} – ${saved.end_date}`
            : labelFor(options.timings, saved.default_timing)}
          {saved.free_only ? ', free only' : ''}
          {saved.max_price_usd != null ? `, ≤ $${saved.max_price_usd}` : ''}
          {saved.categories.length > 0
            ? `, ${saved.categories.length} categories`
            : ''}
        </p>
      ) : null}
    </div>
  )
}
