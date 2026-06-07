import { format, getDay, parse, startOfWeek, addHours } from 'date-fns'
import { enUS } from 'date-fns/locale'
import { useEffect, useMemo, useState } from 'react'
import {
  Calendar,
  dateFnsLocalizer,
  type EventProps,
  Views,
} from 'react-big-calendar'
import 'react-big-calendar/lib/css/react-big-calendar.css'

import { useEventSchedule } from '../contexts/EventScheduleContext'
import type { ScheduledEvent } from '../lib/eventSchedule'

type CalendarEvent = {
  id: string
  title: string
  start: Date
  end: Date
  resource: ScheduledEvent
}

const locales = { 'en-US': enUS }

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
})

function parseEventStart(value: string | null | undefined): Date | null {
  if (!value) {
    return null
  }
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function toCalendarEvent(event: ScheduledEvent): CalendarEvent | null {
  const start = parseEventStart(event.start_at)
  if (!start) {
    return null
  }
  return {
    id: event.meetup_event_id,
    title: event.title,
    start,
    end: addHours(start, 1),
    resource: event,
  }
}

function EventCard({ event }: { event: ScheduledEvent }) {
  const location = [event.venue, event.city].filter(Boolean).join(', ')

  return (
    <a
      href={event.url}
      target="_blank"
      rel="noreferrer"
      className="block rounded-lg border border-sky-500/30 bg-sky-950/40 p-3 transition hover:border-sky-400 hover:bg-sky-900/50"
    >
      <h3 className="text-sm font-medium text-slate-100">{event.title}</h3>
      {location ? <p className="mt-1 text-xs text-slate-400">{location}</p> : null}
      {event.reason ? (
        <p className="mt-2 text-xs leading-relaxed text-slate-300">{event.reason}</p>
      ) : null}
    </a>
  )
}

function CalendarEventItem({ event }: EventProps<CalendarEvent>) {
  return (
    <span className="block truncate text-xs font-medium" title={event.title}>
      {event.title}
    </span>
  )
}

export function EventScheduleCalendar() {
  const { schedule } = useEventSchedule()
  const [date, setDate] = useState(new Date())

  const { calendarEvents, unscheduled } = useMemo(() => {
    if (!schedule) {
      return {
        calendarEvents: [] as CalendarEvent[],
        unscheduled: [] as ScheduledEvent[],
      }
    }

    const scheduled: CalendarEvent[] = []
    const withoutDate: ScheduledEvent[] = []

    for (const event of schedule.events) {
      const mapped = toCalendarEvent(event)
      if (mapped) {
        scheduled.push(mapped)
      } else {
        withoutDate.push(event)
      }
    }

    scheduled.sort((left, right) => left.start.getTime() - right.start.getTime())

    return {
      calendarEvents: scheduled,
      unscheduled: withoutDate,
    }
  }, [schedule])

  useEffect(() => {
    if (calendarEvents.length > 0) {
      setDate(calendarEvents[0].start)
    }
  }, [schedule, calendarEvents])

  if (!schedule || schedule.events.length === 0) {
    return (
      <div className="flex h-full min-h-0 flex-col items-center justify-center px-6 text-center text-slate-400">
        <p className="text-lg font-medium text-slate-200">Your schedule will appear here</p>
        <p className="mt-2 max-w-md text-sm">
          Tell the assistant what kind of month you want — interests, timing, budget — and it
          will suggest events on this calendar. Click any event to open it on Meetup.
        </p>
      </div>
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <div className="shrink-0 border-b border-slate-800 px-4 py-3">
        <h2 className="text-base font-semibold text-slate-100">{schedule.title}</h2>
        <p className="text-sm text-slate-400">
          {schedule.events.length} suggested events · click an event to open Meetup
        </p>
      </div>

      <div className="eventScheduleCalendar min-h-0 flex-1 overflow-hidden p-4">
        <Calendar
          localizer={localizer}
          events={calendarEvents}
          startAccessor="start"
          endAccessor="end"
          view={Views.MONTH}
          views={[Views.MONTH]}
          date={date}
          onNavigate={setDate}
          popup
          style={{ height: '100%', minHeight: '28rem' }}
          components={{ event: CalendarEventItem }}
          onSelectEvent={(event) => {
            window.open(event.resource.url, '_blank', 'noopener,noreferrer')
          }}
          eventPropGetter={() => ({
            className: 'event-schedule-calendar-event',
          })}
        />
      </div>

      {unscheduled.length > 0 ? (
        <section className="shrink-0 border-t border-slate-800 bg-slate-900/40 p-4">
          <h3 className="mb-3 text-sm font-medium text-slate-200">Unscheduled picks</h3>
          <div className="grid max-h-40 gap-3 overflow-y-auto md:grid-cols-2 xl:grid-cols-3">
            {unscheduled.map((event) => (
              <EventCard key={event.meetup_event_id} event={event} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  )
}
