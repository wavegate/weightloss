import { HttpAgent } from '@ag-ui/client'

type GetToken = () => Promise<string | null>

export function createMetabolismHttpAgent(url: string, getToken: GetToken) {
  return new HttpAgent({
    url,
    fetch: async (requestUrl, init) => {
      const token = await getToken()
      const headers = new Headers(init.headers)

      if (token) {
        headers.set('Authorization', `Bearer ${token}`)
      } else {
        headers.delete('Authorization')
      }

      return fetch(requestUrl, { ...init, headers })
    },
  })
}
