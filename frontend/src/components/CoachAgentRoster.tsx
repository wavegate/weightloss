import { useCoAgent } from '@copilotkit/react-core'

import { WEIGHT_LOSS_COACH_AGENT_ID } from '../lib/coachAgent'

export type ActiveCoachAgent = 'weight_loss_coach' | 'metabolism_coach'

type AssistantState = {
  active_agent?: ActiveCoachAgent
}

const ROSTER: {
  id: ActiveCoachAgent
  name: string
  role: string
  avatar: string
}[] = [
  {
    id: 'weight_loss_coach',
    name: 'Coach',
    role: 'Food, weight & app',
    avatar: '🎯',
  },
  {
    id: 'metabolism_coach',
    name: 'Metabolism',
    role: 'BMR, TDEE & plans',
    avatar: '⚡',
  },
]

export function CoachAgentRoster() {
  const { state } = useCoAgent<AssistantState>({
    name: WEIGHT_LOSS_COACH_AGENT_ID,
  })

  const active: ActiveCoachAgent =
    state?.active_agent === 'metabolism_coach'
      ? 'metabolism_coach'
      : 'weight_loss_coach'

  return (
    <div
      className="flex items-end justify-center gap-6 sm:gap-10"
      aria-label="Assistant agents"
    >
      {ROSTER.map((agent) => {
        const isActive = agent.id === active
        return (
          <div
            key={agent.id}
            className="flex flex-col items-center gap-1.5"
            aria-current={isActive ? 'true' : undefined}
          >
            <div
              className={`flex h-14 w-14 items-center justify-center rounded-2xl border-2 text-2xl transition-all sm:h-16 sm:w-16 sm:text-3xl ${
                isActive
                  ? 'scale-105 border-violet-400 bg-violet-600/25 shadow-lg shadow-violet-900/40'
                  : 'scale-95 border-slate-700 bg-slate-800/60 opacity-45 grayscale'
              }`}
              title={agent.name}
            >
              <span aria-hidden>{agent.avatar}</span>
            </div>
            <span
              className={`text-xs font-medium sm:text-sm ${
                isActive ? 'text-violet-300' : 'text-slate-500'
              }`}
            >
              {agent.name}
            </span>
            {isActive ? (
              <span className="text-[10px] text-slate-500 sm:text-xs">
                {agent.role}
              </span>
            ) : null}
          </div>
        )
      })}
    </div>
  )
}
