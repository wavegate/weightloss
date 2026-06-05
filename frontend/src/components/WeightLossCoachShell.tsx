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
import { CollapsibleSidebar } from './CollapsibleSidebar'
import { CoachTeamStage } from './teamHQ/CoachTeamStage'
import { CoachVoiceProvider } from './CoachVoiceContext'
import { CoachVoicePlayButton } from './CoachVoicePlayButton'
import { CoachNavigationTools } from './CoachNavigationTools'
import { CoachQuerySync } from './CoachQuerySync'
import { useConversationThreadId } from '../hooks/useConversationThreadId'

const COPILOT_PUBLIC_LICENSE_KEY = import.meta.env
  .VITE_COPILOT_PUBLIC_LICENSE_KEY as string | undefined

const CHAT_PANEL_KEY = 'weightloss:panel-chat-open'
const APP_PANEL_KEY = 'weightloss:panel-app-open'

type WeightLossCoachShellProps = {
  children: ReactNode
}

function ThreeColumnChrome({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-svh max-h-svh overflow-hidden bg-slate-950 text-slate-100">
      {children}
    </div>
  )
}

function CoachTeamStagePlaceholder() {
  return (
    <section
      aria-hidden
      className="flex h-full min-h-0 flex-1 items-center justify-center bg-slate-950 text-sm text-slate-500"
    >
      Loading your team…
    </section>
  )
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

  const threadId = useConversationThreadId(userId, 'coach-v3')

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
      <ThreeColumnChrome>
        <aside className="weightLossCoachPanel flex h-full w-80 max-w-[min(100vw,28rem)] shrink-0 flex-col overflow-hidden border-r border-slate-800 bg-slate-900">
          <div className="flex h-full min-h-0 flex-col items-center justify-center gap-3 p-6 text-slate-400">
            Connecting to your weight loss assistant…
          </div>
        </aside>
        <CoachTeamStagePlaceholder />
        <aside className="flex h-full w-80 max-w-[min(100vw,28rem)] shrink-0 flex-col overflow-hidden border-l border-slate-800 bg-slate-900">
          <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
        </aside>
      </ThreeColumnChrome>
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
      threadId={threadId}
      headers={authHeaders}
    >
      <CoachNavigationTools />
      <CoachQuerySync />
      <CoachVoiceProvider>
      <ThreeColumnChrome>
        <CollapsibleSidebar
          side="left"
          label="Chat"
          storageKey={CHAT_PANEL_KEY}
          expandedWidthClass="w-[min(100vw,26rem)] sm:w-96"
        >
          <aside className="weightLossCoachPanel flex h-full min-h-0 flex-1 flex-col overflow-hidden">
            <div className="flex shrink-0 items-center justify-between gap-2 border-b border-slate-800 px-3 py-2">
              <span className="text-xs text-slate-400">Latest reply</span>
              <CoachVoicePlayButton />
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
        </CollapsibleSidebar>

        <main className="relative min-h-0 min-w-0 flex-1">
          <CoachTeamStage />
        </main>

        <CollapsibleSidebar
          side="right"
          label="App"
          storageKey={APP_PANEL_KEY}
          expandedWidthClass="w-[min(100vw,26rem)] sm:w-[28rem]"
        >
          <div className="flex h-full min-h-0 flex-col overflow-hidden">{children}</div>
        </CollapsibleSidebar>
      </ThreeColumnChrome>
      </CoachVoiceProvider>
    </CopilotKit>
  )
}
