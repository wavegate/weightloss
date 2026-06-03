import { OrbitControls } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import { Vector3 } from 'three'

import { useCoachHandoff } from '../../hooks/useCoachHandoff'
import {
  getNpcCameraTarget,
  type ActiveCoachAgent,
  type CoachNpcLayout,
} from '../../lib/coachNpcRoster'

type CameraFocusControlsProps = {
  layout: CoachNpcLayout
  compact: boolean
}

export function CameraFocusControls({
  layout,
  compact,
}: CameraFocusControlsProps) {
  const { active, handoffTarget } = useCoachHandoff()
  const controlsRef = useRef<OrbitControlsImpl>(null)
  const focusTarget = useRef(new Vector3())
  const desiredTarget = useRef(new Vector3())

  const focusAgent: ActiveCoachAgent = handoffTarget ?? active

  const desiredCoords = useMemo(
    () => getNpcCameraTarget(focusAgent, layout),
    [focusAgent, layout],
  )

  useEffect(() => {
    desiredTarget.current.set(...desiredCoords)
  }, [desiredCoords])

  useFrame((_, delta) => {
    const controls = controlsRef.current
    if (!controls) {
      return
    }

    const blend = 1 - Math.exp(-6 * delta)
    focusTarget.current.copy(controls.target)
    focusTarget.current.lerp(desiredTarget.current, blend)
    controls.target.copy(focusTarget.current)
    controls.update()
  })

  return (
    <OrbitControls
      ref={controlsRef}
      enablePan
      screenSpacePanning
      panSpeed={0.8}
      minPolarAngle={compact ? Math.PI / 3.2 : Math.PI / 4}
      maxPolarAngle={compact ? Math.PI / 2.05 : Math.PI / 2.2}
      minDistance={compact ? 5.5 : 5}
      maxDistance={compact ? 11 : 10}
    />
  )
}
