import { UserButton, useAuth } from '@clerk/react'
import { CopilotKit } from '@copilotkit/react-core'
import { CopilotChat } from '@copilotkit/react-ui'
import '@copilotkit/react-ui/styles.css'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { getBackendUrl } from '../lib/backendUrl'
import { createCoachHttpAgent } from '../lib/coachAgent'
import {
  EVENT_MANAGER_AGENT_ID,
  EVENT_MANAGER_AG_UI_PATH,
} from '../lib/eventManagerAgent'

const COPILOT_PUBLIC_LICENSE_KEY = import.meta.env
  .VITE_COPILOT_PUBLIC_LICENSE_KEY as string | undefined

export function EventManagerPage() {
  const { userId, isLoaded, isSignedIn, getToken } = useAuth()
  const [authHeaders, setAuthHeaders] = useState<Record<string, string>>({})
  const [hasToken, setHasToken] = useState(false)

  useEffect(() => {
    if (!isLoaded) {
      return
    }

    let cancelled = false
    async function syncAuth() {
      const token = await getToken({ skipCache: true }).catch(() => null)
      if (cancelled) {
        return
      }
      if (token) {
        setAuthHeaders({ Authorization: `Bearer ${token}` })
        setHasToken(true)
      } else {
        setAuthHeaders({})
        setHasToken(false)
      }
    }

    void syncAuth()

    return () => {
      cancelled = true
    }
  }, [getToken, isLoaded, isSignedIn])

  const selfManagedAgents = useMemo(() => {
    if (!hasToken) {
      return undefined
    }

    const agentUrl = `${getBackendUrl()}${EVENT_MANAGER_AG_UI_PATH}`
    return {
      [EVENT_MANAGER_AGENT_ID]: createCoachHttpAgent(agentUrl, () =>
        getToken({ skipCache: true }),
      ),
    }
  }, [getToken, hasToken])

  if (!isLoaded || !userId) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-slate-950 text-slate-400">
        Loading…
      </div>
    )
  }

  if (!hasToken || !selfManagedAgents) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-slate-950 text-slate-400">
        Connecting to event assistant…
      </div>
    )
  }

  return (
    <CopilotKit
      publicLicenseKey={COPILOT_PUBLIC_LICENSE_KEY}
      runtimeUrl={`${getBackendUrl()}${EVENT_MANAGER_AG_UI_PATH}`}
      useSingleEndpoint={false}
      agent={EVENT_MANAGER_AGENT_ID}
      selfManagedAgents={
        selfManagedAgents as unknown as Parameters<
          typeof CopilotKit
        >[0]['selfManagedAgents']
      }
      threadId={`${userId}:event-manager-v1`}
      headers={authHeaders}
    >
      <div className="flex h-svh max-h-svh flex-col overflow-hidden bg-slate-950 text-slate-100">
        <header className="flex shrink-0 items-center justify-between gap-3 border-b border-slate-800 px-4 py-3">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-semibold tracking-tight">Event manager</h1>
            <Link
              to="/measurements"
              className="text-sm text-slate-400 transition hover:text-slate-200"
            >
              Back to weight loss app
            </Link>
          </div>
          <UserButton />
        </header>

        <main className="eventManagerChat min-h-0 flex-1">
          <CopilotChat
            className="flex h-full min-h-0 flex-col"
            labels={{
              title: 'Event discovery',
              initial:
                "Hi! I can help you find events and things to do.\n\nTell me your city, dates, and what you're in the mood for (music, food, sports, etc.).",
              placeholder: 'What kind of events are you looking for?',
            }}
          />
        </main>
      </div>
    </CopilotKit>
  )
}
