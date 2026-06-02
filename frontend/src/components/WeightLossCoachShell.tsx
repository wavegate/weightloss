import { useAuth } from '@clerk/react'
import { CopilotKit } from '@copilotkit/react-core'
import { CopilotChat } from '@copilotkit/react-ui'
import '@copilotkit/react-ui/styles.css'
import { useEffect, useMemo, useState, type ReactNode } from 'react'

import { getBearerToken } from '../lib/authToken'
import {
  createCoachHttpAgent,
  WEIGHT_LOSS_COACH_AGENT_ID,
} from '../lib/coachAgent'
import { CoachNavigationTools } from './CoachNavigationTools'
import { CoachQuerySync } from './CoachQuerySync'

const API_BASE_URL =
  import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? 'http://127.0.0.1:8000'

const COACH_AGENT_URL = `${API_BASE_URL}/copilotkit/ag-ui`

const COPILOT_PUBLIC_LICENSE_KEY = import.meta.env
  .VITE_COPILOT_PUBLIC_LICENSE_KEY as string | undefined

type WeightLossCoachShellProps = {
  children: ReactNode
}

export function WeightLossCoachShell({ children }: WeightLossCoachShellProps) {
  const { userId, isLoaded, isSignedIn } = useAuth()
  const [authHeaders, setAuthHeaders] = useState<Record<string, string>>({})
  const [hasToken, setHasToken] = useState(false)

  useEffect(() => {
    if (!isLoaded || !isSignedIn) {
      setHasToken(false)
      setAuthHeaders({})
      return
    }

    let cancelled = false

    async function syncAuth() {
      const token = await getBearerToken()
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
    const intervalId = window.setInterval(syncAuth, 45_000)

    return () => {
      cancelled = true
      window.clearInterval(intervalId)
    }
  }, [isLoaded, isSignedIn])

  const selfManagedAgents = useMemo(() => {
    if (!hasToken) {
      return undefined
    }

    return {
      [WEIGHT_LOSS_COACH_AGENT_ID]: createCoachHttpAgent(COACH_AGENT_URL),
    }
  }, [hasToken])

  if (!isLoaded || !userId) {
    return <>{children}</>
  }

  if (!hasToken || !selfManagedAgents) {
    return (
      <div className="flex min-h-svh items-center justify-center bg-slate-950 text-slate-400">
        Connecting to your weight loss assistant…
      </div>
    )
  }

  return (
    <CopilotKit
      publicLicenseKey={COPILOT_PUBLIC_LICENSE_KEY}
      runtimeUrl={COACH_AGENT_URL}
      useSingleEndpoint={false}
      agent={WEIGHT_LOSS_COACH_AGENT_ID}
      selfManagedAgents={
        selfManagedAgents as unknown as Parameters<
          typeof CopilotKit
        >[0]['selfManagedAgents']
      }
      threadId={`${userId}:coach-v3`}
      headers={authHeaders}
    >
      <CoachNavigationTools />
      <CoachQuerySync />
      <div className="flex h-svh max-h-svh overflow-hidden bg-slate-950 text-slate-100">
        <aside className="weightLossCoachPanel flex h-full max-h-svh w-[min(100%,28rem)] shrink-0 flex-col overflow-hidden border-r border-slate-800 bg-slate-900">
          <CopilotChat
            className="flex h-full min-h-0 flex-1 flex-col"
            labels={{
              title: 'Weight loss coach',
              initial:
                "Hi! I'm your weight loss assistant. I can help you log weight and food, check your metabolism, and set calorie targets.\n\nHow can I help today?",
              placeholder: 'Ask me anything…',
            }}
          />
        </aside>
        <main className="min-h-0 flex-1 overflow-y-auto">{children}</main>
      </div>
    </CopilotKit>
  )
}
