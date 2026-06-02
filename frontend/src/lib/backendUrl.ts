function stripTrailingSlash(url: string): string {
  return url.replace(/\/$/, '')
}

function readApiUrlFromEnv(): string | undefined {
  return (
    import.meta.env.VITE_API_URL?.trim() ||
    import.meta.env.VITE_BACKEND_URL?.trim() ||
    undefined
  )
}

function assertSafeForBrowser(apiUrl: string): void {
  if (typeof window === 'undefined') {
    return
  }

  if (
    window.location.protocol === 'https:' &&
    apiUrl.startsWith('http://')
  ) {
    throw new Error(
      'VITE_API_URL must use https:// when the app is served over HTTPS. ' +
        'Browsers block HTTP API calls from a Vercel site (mixed content). ' +
        'Put TLS on your EC2 API (nginx + certbot) and redeploy Vercel with an https:// API URL.',
    )
  }

  if (
    import.meta.env.PROD &&
    (apiUrl.includes('127.0.0.1') || apiUrl.includes('localhost'))
  ) {
    throw new Error(
      'VITE_API_URL points at localhost in production. Set it to your public EC2/API URL in Vercel and redeploy.',
    )
  }
}

/** Backend API base URL from VITE_API_URL (or legacy VITE_BACKEND_URL). */
export function getBackendUrl(): string {
  const raw = readApiUrlFromEnv()

  if (raw) {
    const url = stripTrailingSlash(raw)
    assertSafeForBrowser(url)
    return url
  }

  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000'
  }

  throw new Error(
    'Missing VITE_API_URL. Add it in Vercel → Settings → Environment Variables, then redeploy (env vars are baked in at build time).',
  )
}
