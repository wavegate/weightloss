import { useAuth } from '@clerk/react'
import { CopilotKit } from '@copilotkit/react-core'
import { CopilotChat } from '@copilotkit/react-ui'
import '@copilotkit/react-ui/styles.css'
import { useMemo } from 'react'

import { useMetabolicProfile } from '../hooks/useMetabolicProfile'
import { createMetabolismHttpAgent } from '../lib/metabolismAgent'

const API_BASE_URL =
  import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? 'http://127.0.0.1:8000'

const METABOLISM_AGENT_URL = `${API_BASE_URL}/copilotkit/ag-ui`

function ProfileSummary() {
  const { data: profile, isLoading } = useMetabolicProfile()

  if (isLoading) {
    return (
      <p className="text-sm text-slate-400">Loading saved profile…</p>
    )
  }

  if (!profile) {
    return (
      <p className="text-sm text-slate-400">
        No saved profile yet. Chat with the coach to estimate BMR and TDEE,
        then save when you are ready.
      </p>
    )
  }

  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-4">
      <div>
        <dt className="text-slate-500">BMR</dt>
        <dd className="font-medium text-slate-100">
          {profile.bmr_kcal != null ? `${Math.round(profile.bmr_kcal)} kcal` : '—'}
        </dd>
      </div>
      <div>
        <dt className="text-slate-500">TDEE</dt>
        <dd className="font-medium text-slate-100">
          {profile.tdee_kcal != null
            ? `${Math.round(profile.tdee_kcal)} kcal`
            : '—'}
        </dd>
      </div>
      <div>
        <dt className="text-slate-500">Activity</dt>
        <dd className="font-medium capitalize text-slate-100">
          {profile.activity_level.replace('_', ' ')}
        </dd>
      </div>
      <div>
        <dt className="text-slate-500">Age / height</dt>
        <dd className="font-medium text-slate-100">
          {profile.age_years} yr · {Math.round(profile.height_cm)} cm
        </dd>
      </div>
    </dl>
  )
}

function MetabolismChat({ threadId }: { threadId: string }) {
  const { getToken, isLoaded } = useAuth()

  const selfManagedAgents = useMemo(() => {
    if (!isLoaded) {
      return undefined
    }

    return {
      metabolism_coach: createMetabolismHttpAgent(METABOLISM_AGENT_URL, () =>
        getToken(),
      ),
    }
  }, [getToken, isLoaded])

  if (!selfManagedAgents) {
    return (
      <p className="text-sm text-slate-400">Connecting to metabolism coach…</p>
    )
  }

  return (
    <CopilotKit
      runtimeUrl={METABOLISM_AGENT_URL}
      useSingleEndpoint={false}
      agent="metabolism_coach"
      selfManagedAgents={
        selfManagedAgents as unknown as Parameters<
          typeof CopilotKit
        >[0]['selfManagedAgents']
      }
      threadId={threadId}
    >
      <div className="flex min-h-[28rem] flex-col overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
        <CopilotChat
          className="flex-1"
          labels={{
            title: 'Metabolism coach',
            initial:
              "I'll estimate your BMR (calories at rest) and TDEE (daily burn with activity) using the Mifflin–St Jeor equation.\n\nFirst question: are you male or female?",
            placeholder: 'e.g. male',
          }}
        />
      </div>
    </CopilotKit>
  )
}

export function MetabolismPage() {
  const { userId, isLoaded } = useAuth()

  if (!isLoaded) {
    return <p className="text-sm text-slate-400">Loading…</p>
  }

  if (!userId) {
    return <p className="text-sm text-slate-400">Sign in to use the metabolism coach.</p>
  }

  return (
    <section className="flex flex-col gap-6">
      <div className="space-y-2">
        <h2 className="text-xl font-medium text-slate-100">Metabolism coach</h2>
        <p className="text-sm text-slate-400">
          Estimate basal metabolic rate (BMR) and total daily energy expenditure
          (TDEE) with guided questions. Calculations use the Mifflin–St Jeor
          equation.
        </p>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
        <h3 className="mb-3 text-sm font-medium text-slate-300">Saved profile</h3>
        <ProfileSummary />
      </div>

      <MetabolismChat threadId={userId} />
    </section>
  )
}
