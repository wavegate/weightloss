import { HttpAgent } from '@ag-ui/client'

import { getBearerToken } from './authToken'

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

      return fetch(requestUrl, { ...init, headers })
    },
  })
}
