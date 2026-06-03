import { useFrame } from '@react-three/fiber'
import { useRef } from 'react'
import type { Group } from 'three'

import type { CoachNpcShape } from '../../lib/coachNpcRoster'

type NpcCharacterProps = {
  shape: CoachNpcShape
  color: string
  isActive: boolean
  isPending: boolean
  isClickable: boolean
  onSelect: () => void
}

function CoachGeometry({ color, emissiveIntensity }: { color: string; emissiveIntensity: number }) {
  return (
    <group position={[0, 0.9, 0]}>
      <mesh position={[0, 0.35, 0]} castShadow>
        <boxGeometry args={[0.55, 0.7, 0.35]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={emissiveIntensity}
        />
      </mesh>
      <mesh position={[0, 0.95, 0]} castShadow>
        <sphereGeometry args={[0.28, 24, 24]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={emissiveIntensity * 1.2}
        />
      </mesh>
    </group>
  )
}

function DieticianGeometry({
  color,
  emissiveIntensity,
}: {
  color: string
  emissiveIntensity: number
}) {
  return (
    <group position={[0, 0.85, 0]}>
      <mesh position={[0, 0.3, 0]} castShadow>
        <boxGeometry args={[0.75, 0.6, 0.45]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={emissiveIntensity}
        />
      </mesh>
      <mesh position={[0, 0.78, 0]} castShadow>
        <sphereGeometry args={[0.26, 24, 24]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={emissiveIntensity * 1.2}
        />
      </mesh>
    </group>
  )
}

function MetabolismGeometry({
  color,
  emissiveIntensity,
}: {
  color: string
  emissiveIntensity: number
}) {
  return (
    <group position={[0, 0.95, 0]}>
      <mesh position={[0, 0.45, 0]} castShadow>
        <coneGeometry args={[0.38, 0.95, 5]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={emissiveIntensity}
        />
      </mesh>
      <mesh position={[0, 0.15, 0]} rotation={[Math.PI / 2, 0, 0]} castShadow>
        <torusGeometry args={[0.42, 0.07, 12, 24]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={emissiveIntensity * 0.8}
        />
      </mesh>
    </group>
  )
}

export function NpcCharacter({
  shape,
  color,
  isActive,
  isPending,
  isClickable,
  onSelect,
}: NpcCharacterProps) {
  const groupRef = useRef<Group>(null)
  const emissiveIntensity = isActive ? 0.45 : isPending ? 0.3 : 0.12
  const targetScale = isActive ? 1.08 : isPending ? 1.04 : 1

  useFrame((_, delta) => {
    const group = groupRef.current
    if (!group) {
      return
    }

    const pulse = isPending ? 1 + Math.sin(performance.now() * 0.008) * 0.03 : 1
    const nextScale = targetScale * pulse
    const blend = Math.min(1, delta * 8)
    group.scale.x += (nextScale - group.scale.x) * blend
    group.scale.y += (nextScale - group.scale.y) * blend
    group.scale.z += (nextScale - group.scale.z) * blend
  })

  return (
    <group
      ref={groupRef}
      onClick={(event) => {
        event.stopPropagation()
        if (isClickable) {
          onSelect()
        }
      }}
      onPointerOver={(event) => {
        if (isClickable) {
          event.stopPropagation()
          document.body.style.cursor = 'pointer'
        }
      }}
      onPointerOut={() => {
        document.body.style.cursor = 'auto'
      }}
    >
      {shape === 'coach' ? (
        <CoachGeometry color={color} emissiveIntensity={emissiveIntensity} />
      ) : shape === 'dietician' ? (
        <DieticianGeometry color={color} emissiveIntensity={emissiveIntensity} />
      ) : (
        <MetabolismGeometry color={color} emissiveIntensity={emissiveIntensity} />
      )}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, 0]} receiveShadow>
        <circleGeometry args={[0.55, 32]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={isActive ? 0.25 : 0.05}
          transparent
          opacity={0.35}
        />
      </mesh>
    </group>
  )
}
