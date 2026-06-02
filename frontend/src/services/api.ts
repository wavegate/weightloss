import { getBearerToken } from '../lib/authToken'
import { getUserTimezone, todayIsoDate } from '../lib/nutritionTargets'

const API_BASE_URL =
  import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function buildHeaders(includeJson: boolean): Promise<HeadersInit> {
  const headers: Record<string, string> = {}

  if (includeJson) {
    headers['Content-Type'] = 'application/json'
  }

  const token = await getBearerToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  headers['X-User-Local-Date'] = todayIsoDate()
  headers['X-User-Timezone'] = getUserTimezone()

  return headers
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = response.statusText
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') {
        message = body.detail
      }
    } catch {
      // ignore non-JSON error bodies
    }
    throw new ApiError(message, response.status)
  }

  return response.json() as Promise<T>
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: await buildHeaders(false),
  })
  return parseResponse<T>(response)
}

export async function apiPost<T, B>(path: string, body: B): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: await buildHeaders(true),
    body: JSON.stringify(body),
  })
  return parseResponse<T>(response)
}
