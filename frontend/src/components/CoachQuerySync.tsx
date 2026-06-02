import { useCoAgent } from '@copilotkit/react-core'
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'

import { foodKeys } from '../hooks/useFoods'
import { measurementKeys } from '../hooks/useMeasurements'
import { metabolismKeys } from '../hooks/metabolismKeys'
import { WEIGHT_LOSS_COACH_AGENT_ID } from '../lib/coachAgent'

/** Refetch page data after the coach agent finishes a turn (e.g. saved plan). */
export function CoachQuerySync() {
  const queryClient = useQueryClient()
  const { running } = useCoAgent({ name: WEIGHT_LOSS_COACH_AGENT_ID })
  const wasRunning = useRef(false)

  useEffect(() => {
    if (wasRunning.current && !running) {
      void queryClient.invalidateQueries({ queryKey: metabolismKeys.profile })
      void queryClient.invalidateQueries({ queryKey: metabolismKeys.plan })
      void queryClient.invalidateQueries({ queryKey: foodKeys.all })
      void queryClient.invalidateQueries({ queryKey: measurementKeys.all })
    }
    wasRunning.current = running
  }, [running, queryClient])

  return null
}
