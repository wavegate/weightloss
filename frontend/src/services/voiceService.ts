import { getBackendUrl } from '../lib/backendUrl'
import { getBearerToken } from '../lib/authToken'
import { getUserTimezone, todayIsoDate } from '../lib/nutritionTargets'

import { ApiError } from './api'

export async function synthesizeCoachSpeech(
  text: string,
  signal?: AbortSignal,
): Promise<Blob> {
  const token = await getBearerToken()
  if (!token) {
    throw new ApiError('Missing Clerk session. Please sign in again.', 401)
  }

  const response = await fetch(`${getBackendUrl()}/voice/speak`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      'X-User-Local-Date': todayIsoDate(),
      'X-User-Timezone': getUserTimezone(),
    },
    body: JSON.stringify({ text }),
    signal,
  })

  if (!response.ok) {
    let message = response.statusText
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') {
        message = body.detail
      }
    } catch {
      // ignore
    }
    throw new ApiError(message, response.status)
  }

  return response.blob()
}
