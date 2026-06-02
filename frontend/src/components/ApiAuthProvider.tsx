import { useAuth } from '@clerk/react'
import { useEffect } from 'react'

import { setAuthTokenGetter } from '../lib/authToken'

export function ApiAuthProvider({ children }: { children: React.ReactNode }) {
  const { getToken, isLoaded } = useAuth()

  useEffect(() => {
    setAuthTokenGetter(() => getToken({ skipCache: true }))
  }, [getToken])

  if (!isLoaded) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-slate-950 text-slate-400">
        Loading…
      </div>
    )
  }

  return children
}
