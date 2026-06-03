import { useCoAgent, useCopilotChatInternal } from '@copilotkit/react-core'
import { useMemo } from 'react'

import { extractMessageText } from '../lib/coachMessageText'
import {
  resolveActiveCoachAgent,
  type ActiveCoachAgent,
} from '../lib/coachNpcRoster'
import { WEIGHT_LOSS_COACH_AGENT_ID } from '../lib/coachAgent'

type AssistantState = {
  active_agent?: ActiveCoachAgent
}

function lastAssistantText(messages: { role: string; content?: unknown }[]) {
  for (let i = messages.length - 1; i >= 0; i--) {
    const message = messages[i]
    if (message.role !== 'assistant') {
      continue
    }
    const text = extractMessageText(message.content).trim()
    if (text) {
      return text
    }
  }
  return null
}

/** Speech bubble content for the active coaching NPC. */
export function useCoachSpeechBubble() {
  const { state, running } = useCoAgent<AssistantState>({
    name: WEIGHT_LOSS_COACH_AGENT_ID,
  })
  const { messages, isLoading } = useCopilotChatInternal()

  const active = resolveActiveCoachAgent(state)
  const isSpeaking = running || isLoading

  const rawText = useMemo(() => lastAssistantText(messages), [messages])
  const displayText = rawText

  const showBubble = isSpeaking || Boolean(displayText)

  return {
    active,
    showBubble,
    isSpeaking,
    displayText,
    isTyping: isSpeaking && !displayText,
  }
}
