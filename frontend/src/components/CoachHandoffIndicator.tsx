import { useCoAgent } from '@copilotkit/react-core'

import { WEIGHT_LOSS_COACH_AGENT_ID } from '../lib/coachAgent'

type AssistantState = {
  active_agent?: 'weight_loss_coach' | 'metabolism_coach'
}

export function CoachHandoffIndicator() {
  const { state } = useCoAgent<AssistantState>({
    name: WEIGHT_LOSS_COACH_AGENT_ID,
  })

  if (state?.active_agent !== 'metabolism_coach') {
    return null
  }

  return (
    <p className="shrink-0 border-b border-violet-800/60 bg-violet-950/50 px-3 py-1.5 text-xs text-violet-200">
      Metabolism coach — BMR, TDEE, and weight-loss plan
    </p>
  )
}
