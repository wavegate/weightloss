export type ScheduledEvent = {
  meetup_event_id: string
  title: string
  start_at?: string | null
  url: string
  venue?: string | null
  city?: string | null
  reason?: string | null
}

export type EventSchedule = {
  title: string
  events: ScheduledEvent[]
}

export function normalizeScheduledEvent(raw: Record<string, unknown>): ScheduledEvent | null {
  const meetupEventId = raw.meetup_event_id
  const title = raw.title
  const url = raw.url
  if (typeof meetupEventId !== 'string' || typeof title !== 'string' || typeof url !== 'string') {
    return null
  }

  return {
    meetup_event_id: meetupEventId,
    title,
    url,
    start_at: typeof raw.start_at === 'string' ? raw.start_at : null,
    venue: typeof raw.venue === 'string' ? raw.venue : null,
    city: typeof raw.city === 'string' ? raw.city : null,
    reason: typeof raw.reason === 'string' ? raw.reason : null,
  }
}

export function normalizeSchedule(raw: {
  title?: unknown
  events?: unknown
}): EventSchedule {
  const events = Array.isArray(raw.events)
    ? raw.events
        .map((entry) =>
          entry && typeof entry === 'object'
            ? normalizeScheduledEvent(entry as Record<string, unknown>)
            : null,
        )
        .filter((entry): entry is ScheduledEvent => entry !== null)
    : []

  return {
    title: typeof raw.title === 'string' && raw.title.trim() ? raw.title.trim() : 'Suggested schedule',
    events,
  }
}
