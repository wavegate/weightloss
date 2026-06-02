import { useAuth } from '@clerk/react'
import { CopilotKit } from '@copilotkit/react-core'
import { CopilotChat } from '@copilotkit/react-ui'
import '@copilotkit/react-ui/styles.css'
import { useEffect, useMemo, useState, type ReactNode } from 'react'

import { getBackendUrl } from '../lib/backendUrl'
import {
  createCoachHttpAgent,
  WEIGHT_LOSS_COACH_AGENT_ID,
} from '../lib/coachAgent'
import { CoachAgentRoster } from './CoachAgentRoster'
import { CoachNavigationTools } from './CoachNavigationTools'
import { CoachQuerySync } from './CoachQuerySync'

const COPILOT_PUBLIC_LICENSE_KEY = import.meta.env
  .VITE_COPILOT_PUBLIC_LICENSE_KEY as string | undefined

type WeightLossCoachShellProps = {
  children: ReactNode
}

export function WeightLossCoachShell({ children }: WeightLossCoachShellProps) {
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

    const coachAgentUrl = `${getBackendUrl()}/copilotkit/ag-ui`
    return {
      [WEIGHT_LOSS_COACH_AGENT_ID]: createCoachHttpAgent(coachAgentUrl, () =>
        getToken({ skipCache: true }),
      ),
    }
  }, [getToken, hasToken])

  if (!isLoaded || !userId) {
    return <>{children}</>
  }

  if (!hasToken || !selfManagedAgents) {
    return (
      <div className="flex h-svh max-h-svh overflow-hidden bg-slate-950 text-slate-100">
        <aside className="weightLossCoachPanel flex h-full max-h-svh w-[min(100%,28rem)] shrink-0 flex-col overflow-hidden border-r border-slate-800 bg-slate-900">
          <div className="flex h-full min-h-0 flex-col items-center justify-center gap-3 p-6 text-slate-400">
            Connecting to your weight loss assistant…
          </div>
        </aside>
        <main className="min-h-0 flex-1 overflow-y-auto">{children}</main>
      </div>
    )
  }

  return (
    <CopilotKit
      publicLicenseKey={COPILOT_PUBLIC_LICENSE_KEY}
      runtimeUrl={`${getBackendUrl()}/copilotkit/ag-ui`}
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
          <div className="border-b border-slate-800 px-4 py-4">
            <CoachAgentRoster />
          </div>
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
