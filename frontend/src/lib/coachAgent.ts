import { HttpAgent } from '@ag-ui/client'

import { getBearerToken } from './authToken'

export const WEIGHT_LOSS_COACH_AGENT_ID = 'weight_loss_coach'
import { todayIsoDate } from './nutritionTargets'

export function createCoachHttpAgent(url: string) {
  return new HttpAgent({
    url,
    fetch: async (requestUrl, init) => {
      const token = await getBearerToken()
      const headers = new Headers(init.headers)

      if (!token) {
        throw new Error('Missing Clerk session. Please sign in again.')
      }

      headers.set('Authorization', `Bearer ${token}`)
      headers.set('X-User-Local-Date', todayIsoDate())
      headers.set(
        'X-User-Timezone',
        Intl.DateTimeFormat().resolvedOptions().timeZone,
      )

      return fetch(requestUrl, { ...init, headers })
    },
  })
}
