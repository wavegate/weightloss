import { getBackendUrl } from '../lib/backendUrl'
import { getBearerToken } from '../lib/authToken'

export type MeetupSyncProgress = {
  type: 'started' | 'progress' | 'complete' | 'error'
  page: number
  fetched: number
  saved: number
  skipped: number
  message?: string
}

export type MeetupSyncRequest = {
  location: string
  keywords?: string
}

export async function fetchEventLocations() {
  const token = await getBearerToken()
  const response = await fetch(`${getBackendUrl()}/events/locations`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!response.ok) {
    throw new Error('Failed to load event locations')
  }
  return (await response.json()) as { locations: string[] }
}

export async function fetchStoredEventCount() {
  const token = await getBearerToken()
  const response = await fetch(`${getBackendUrl()}/events/count`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!response.ok) {
    throw new Error('Failed to load event count')
  }
  return (await response.json()) as { count: number }
}

export async function streamMeetupSync(
  body: MeetupSyncRequest,
  onProgress: (update: MeetupSyncProgress) => void,
): Promise<MeetupSyncProgress> {
  const token = await getBearerToken()
  const response = await fetch(`${getBackendUrl()}/events/sync`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      location: body.location,
      keywords: body.keywords ?? '',
    }),
  })

  if (!response.ok || !response.body) {
    let message = 'Sync failed'
    try {
      const payload = (await response.json()) as { detail?: string }
      if (payload.detail) {
        message = payload.detail
      }
    } catch {
      // ignore
    }
    throw new Error(message)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let lastUpdate: MeetupSyncProgress = {
    type: 'started',
    page: 0,
    fetched: 0,
    saved: 0,
    skipped: 0,
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''

    for (const part of parts) {
      const line = part
        .split('\n')
        .find((entry) => entry.startsWith('data: '))
      if (!line) {
        continue
      }
      const update = JSON.parse(line.slice(6)) as MeetupSyncProgress
      lastUpdate = update
      onProgress(update)
      if (update.type === 'error') {
        throw new Error(update.message ?? 'Sync failed')
      }
    }
  }

  return lastUpdate
}
