export type ActiveCoachAgent =
  | 'weight_loss_coach'
  | 'metabolism_coach'
  | 'dietician_coach'

export type CoachNpcShape = 'coach' | 'dietician' | 'metabolism'

export type CoachNpcLayout = 'strip' | 'room'

export type CoachNpc = {
  id: ActiveCoachAgent
  name: string
  role: string
  avatar: string
  handoffMessage: string
  color: string
  position: [number, number, number]
  shape: CoachNpcShape
}

export const COACH_NPC_ROSTER: CoachNpc[] = [
  {
    id: 'weight_loss_coach',
    name: 'Coach',
    role: 'Weight & app',
    avatar: '🎯',
    handoffMessage:
      'Please hand me back to the main weight loss coach using transfer_to_weight_loss_coach.',
    color: '#8b5cf6',
    position: [-2.2, 0, 0],
    shape: 'coach',
  },
  {
    id: 'dietician_coach',
    name: 'Dietician',
    role: 'Food log & diet',
    avatar: '🥗',
    handoffMessage:
      'Please transfer me to the dietician coach using transfer_to_dietician_coach. I want help with my food log, meals, or nutrition.',
    color: '#34d399',
    position: [0, 0, 0],
    shape: 'dietician',
  },
  {
    id: 'metabolism_coach',
    name: 'Metabolism',
    role: 'BMR, TDEE & plans',
    avatar: '⚡',
    handoffMessage:
      'Please transfer me to the metabolism coach using transfer_to_metabolism_coach. I want help with BMR, TDEE, or my weight-loss plan.',
    color: '#fbbf24',
    position: [2.2, 0, 0],
    shape: 'metabolism',
  },
]

const STRIP_SPREAD_X: Record<ActiveCoachAgent, number> = {
  weight_loss_coach: -3.8,
  dietician_coach: 0,
  metabolism_coach: 3.8,
}

/** World position for an NPC root (before character mesh offset). */
export function getNpcWorldPosition(
  npcId: ActiveCoachAgent,
  layout: CoachNpcLayout = 'room',
): [number, number, number] {
  const npc = COACH_NPC_ROSTER.find((entry) => entry.id === npcId)
  if (!npc) {
    return [0, 0, 0]
  }
  if (layout === 'room') {
    return npc.position
  }
  return [STRIP_SPREAD_X[npcId], 0, 0]
}

/** OrbitControls look-at point (chest height). */
export function getNpcCameraTarget(
  npcId: ActiveCoachAgent,
  layout: CoachNpcLayout = 'room',
): [number, number, number] {
  const [x, , z] = getNpcWorldPosition(npcId, layout)
  const focusY = layout === 'strip' ? 0.75 : 0.8
  return [x, focusY, z]
}

type AssistantState = {
  active_agent?: ActiveCoachAgent
}

export function resolveActiveCoachAgent(
  state: AssistantState | undefined,
): ActiveCoachAgent {
  if (state?.active_agent === 'metabolism_coach') {
    return 'metabolism_coach'
  }
  if (state?.active_agent === 'dietician_coach') {
    return 'dietician_coach'
  }
  return 'weight_loss_coach'
}
