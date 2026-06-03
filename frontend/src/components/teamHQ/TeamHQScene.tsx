import { Html, OrbitControls } from '@react-three/drei'
import { Canvas } from '@react-three/fiber'

import { useCoachHandoff } from '../../hooks/useCoachHandoff'
import type { CoachNpc } from '../../lib/coachNpcRoster'
import { NpcCharacter } from './NpcCharacter'

type TeamHQSceneProps = {
  layout?: 'strip' | 'room'
}

type NpcLabelProps = {
  npc: CoachNpc
  isActive: boolean
  isPending: boolean
  compact: boolean
}

function NpcLabel({ npc, isActive, isPending, compact }: NpcLabelProps) {
  return (
    <Html
      position={[0, compact ? 1.45 : 1.75, 0]}
      center
      distanceFactor={compact ? 10 : 6}
      style={{ pointerEvents: 'none', userSelect: 'none' }}
    >
      <div className="flex flex-col items-center gap-0.5 whitespace-nowrap text-center">
        <span
          className={`font-semibold ${compact ? 'text-xs' : 'text-sm'} ${
            isActive ? 'text-violet-200' : 'text-slate-200'
          }`}
        >
          {npc.name}
        </span>
        {!compact ? (
          <span className="text-xs text-slate-400">{npc.role}</span>
        ) : null}
        {isActive ? (
          <span className="text-[10px] font-medium text-violet-400">Speaking</span>
        ) : isPending ? (
          <span className="text-[10px] font-medium text-violet-400">Connecting…</span>
        ) : null}
      </div>
    </Html>
  )
}

function npcPosition(
  npc: CoachNpc,
  layout: 'strip' | 'room',
): [number, number, number] {
  if (layout === 'room') {
    return npc.position
  }
  const spread: Record<CoachNpc['id'], number> = {
    weight_loss_coach: -3.8,
    dietician_coach: 0,
    metabolism_coach: 3.8,
  }
  return [spread[npc.id], 0, 0]
}

function SceneContent({ layout }: { layout: 'strip' | 'room' }) {
  const { roster, active, handoffTarget, isBusy, requestHandoff } = useCoachHandoff()
  const compact = layout === 'strip'

  return (
    <>
      <color attach="background" args={['#0f172a']} />
      <ambientLight intensity={0.55} />
      <directionalLight position={[4, 8, 4]} intensity={1.1} castShadow={!compact} />
      <directionalLight position={[-3, 4, -2]} intensity={0.35} />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
        <planeGeometry args={layout === 'strip' ? [16, 4] : [12, 8]} />
        <meshStandardMaterial color="#1e293b" />
      </mesh>

      {roster.map((npc) => {
        const isActive = npc.id === active
        const isPending = handoffTarget === npc.id
        const isClickable = !isActive && !isBusy

        return (
          <group key={npc.id} position={npcPosition(npc, layout)}>
            <NpcCharacter
              shape={npc.shape}
              color={npc.color}
              isActive={isActive}
              isPending={isPending}
              isClickable={isClickable}
              onSelect={() => void requestHandoff(npc.id)}
            />
            <NpcLabel
              npc={npc}
              isActive={isActive}
              isPending={isPending}
              compact={compact}
            />
          </group>
        )
      })}

      <OrbitControls
        enablePan={false}
        minPolarAngle={compact ? Math.PI / 3.2 : Math.PI / 4}
        maxPolarAngle={compact ? Math.PI / 2.05 : Math.PI / 2.2}
        minDistance={compact ? 5.5 : 5}
        maxDistance={compact ? 11 : 10}
        target={[0, compact ? 0.75 : 0.8, 0]}
      />
    </>
  )
}

export function TeamHQScene({ layout = 'room' }: TeamHQSceneProps) {
  const strip = layout === 'strip'

  return (
    <Canvas
      shadows={!strip}
      camera={{
        position: strip ? [0, 1.15, 7.5] : [0, 2.2, 6.5],
        fov: strip ? 48 : 42,
      }}
      dpr={[1, 1.5]}
      className="h-full w-full touch-none"
    >
      <SceneContent layout={layout} />
    </Canvas>
  )
}
