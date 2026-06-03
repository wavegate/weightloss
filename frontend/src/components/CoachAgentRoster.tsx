import { useCoAgent, useCopilotChatInternal } from '@copilotkit/react-core'
import { useCallback, useState } from 'react'

import { WEIGHT_LOSS_COACH_AGENT_ID } from '../lib/coachAgent'

export type ActiveCoachAgent =
  | 'weight_loss_coach'
  | 'metabolism_coach'
  | 'dietician_coach'

type AssistantState = {
  active_agent?: ActiveCoachAgent
}

const ROSTER: {
  id: ActiveCoachAgent
  name: string
  role: string
  avatar: string
  handoffMessage: string
}[] = [
  {
    id: 'weight_loss_coach',
    name: 'Coach',
    role: 'Weight & app',
    avatar: '🎯',
    handoffMessage:
      'Please hand me back to the main weight loss coach using transfer_to_weight_loss_coach.',
  },
  {
    id: 'dietician_coach',
    name: 'Dietician',
    role: 'Food log & diet',
    avatar: '🥗',
    handoffMessage:
      'Please transfer me to the dietician coach using transfer_to_dietician_coach. I want help with my food log, meals, or nutrition.',
  },
  {
    id: 'metabolism_coach',
    name: 'Metabolism',
    role: 'BMR, TDEE & plans',
    avatar: '⚡',
    handoffMessage:
      'Please transfer me to the metabolism coach using transfer_to_metabolism_coach. I want help with BMR, TDEE, or my weight-loss plan.',
  },
]

function resolveActiveAgent(state: AssistantState | undefined): ActiveCoachAgent {
  if (state?.active_agent === 'metabolism_coach') {
    return 'metabolism_coach'
  }
  if (state?.active_agent === 'dietician_coach') {
    return 'dietician_coach'
  }
  return 'weight_loss_coach'
}

export function CoachAgentRoster() {
  const { state, running } = useCoAgent<AssistantState>({
    name: WEIGHT_LOSS_COACH_AGENT_ID,
  })
  const { sendMessage, isLoading } = useCopilotChatInternal()
  const [handoffTarget, setHandoffTarget] = useState<ActiveCoachAgent | null>(
    null,
  )

  const active = resolveActiveAgent(state)

  const isBusy = running || isLoading || handoffTarget !== null

  const requestHandoff = useCallback(
    async (target: ActiveCoachAgent) => {
      if (target === active || isBusy) {
        return
      }

      const agent = ROSTER.find((entry) => entry.id === target)
      if (!agent) {
        return
      }

      setHandoffTarget(target)
      try {
        await sendMessage({
          id: crypto.randomUUID(),
          role: 'user',
          content: agent.handoffMessage,
        })
      } finally {
        setHandoffTarget(null)
      }
    },
    [active, isBusy, sendMessage],
  )

  return (
    <div
      className="flex items-end justify-center gap-4 sm:gap-8"
      aria-label="Assistant agents"
    >
      {ROSTER.map((agent) => {
        const isActive = agent.id === active
        const isPending = handoffTarget === agent.id
        const isClickable = !isActive && !isBusy

        return (
          <div
            key={agent.id}
            className="flex flex-col items-center gap-1.5"
            aria-current={isActive ? 'true' : undefined}
          >
            <button
              type="button"
              disabled={!isClickable}
              onClick={() => void requestHandoff(agent.id)}
              title={
                isActive
                  ? `Talking to ${agent.name}`
                  : isBusy
                    ? 'Switching…'
                    : `Switch to ${agent.name}`
              }
              className={`flex h-14 w-14 items-center justify-center rounded-2xl border-2 text-2xl transition-all sm:h-16 sm:w-16 sm:text-3xl ${
                isActive
                  ? 'scale-105 border-violet-400 bg-violet-600/25 shadow-lg shadow-violet-900/40'
                  : isPending
                    ? 'scale-100 border-violet-500/70 bg-violet-900/30 opacity-80 animate-pulse'
                    : isClickable
                      ? 'scale-95 border-slate-600 bg-slate-800/80 opacity-70 hover:scale-100 hover:border-violet-500/60 hover:opacity-100 hover:grayscale-0'
                      : 'scale-95 cursor-not-allowed border-slate-700 bg-slate-800/60 opacity-45 grayscale'
              }`}
            >
              <span aria-hidden>{agent.avatar}</span>
            </button>
            <span
              className={`text-xs font-medium sm:text-sm ${
                isActive ? 'text-violet-300' : 'text-slate-500'
              }`}
            >
              {agent.name}
            </span>
            {isActive || isPending ? (
              <span className="text-[10px] text-slate-500 sm:text-xs">
                {isPending ? 'Connecting…' : agent.role}
              </span>
            ) : null}
          </div>
        )
      })}
    </div>
  )
}
