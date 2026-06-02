function stripTrailingSlash(url: string): string {
  return url.replace(/\/$/, '')
}

/** Backend API base URL from VITE_API_URL. */
export function getBackendUrl(): string {
  const raw = import.meta.env.VITE_API_URL?.trim()

  if (raw) {
    return stripTrailingSlash(raw)
  }

  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000'
  }

  throw new Error(
    'Missing VITE_API_URL. Set it in .env locally or in Vercel project settings.',
  )
}
