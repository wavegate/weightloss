import { useCoAgent, useCopilotChatInternal } from '@copilotkit/react-core'
import { useCallback, useState } from 'react'

import {
  COACH_NPC_ROSTER,
  resolveActiveCoachAgent,
  type ActiveCoachAgent,
} from '../lib/coachNpcRoster'
import { WEIGHT_LOSS_COACH_AGENT_ID } from '../lib/coachAgent'

type AssistantState = {
  active_agent?: ActiveCoachAgent
}

export function useCoachHandoff() {
  const { state, running } = useCoAgent<AssistantState>({
    name: WEIGHT_LOSS_COACH_AGENT_ID,
  })
  const { sendMessage, isLoading } = useCopilotChatInternal()
  const [handoffTarget, setHandoffTarget] = useState<ActiveCoachAgent | null>(
    null,
  )

  const active = resolveActiveCoachAgent(state)
  const isBusy = running || isLoading || handoffTarget !== null

  const requestHandoff = useCallback(
    async (target: ActiveCoachAgent) => {
      if (target === active || isBusy) {
        return
      }

      const agent = COACH_NPC_ROSTER.find((entry) => entry.id === target)
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

  return {
    roster: COACH_NPC_ROSTER,
    active,
    handoffTarget,
    isBusy,
    requestHandoff,
  }
}
