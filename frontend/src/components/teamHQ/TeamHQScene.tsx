import { Html } from '@react-three/drei'
import { Canvas } from '@react-three/fiber'

import { useCoachHandoff } from '../../hooks/useCoachHandoff'
import { useCoachSpeechBubble } from '../../hooks/useCoachSpeechBubble'
import {
  getNpcWorldPosition,
  type CoachNpc,
  type CoachNpcLayout,
} from '../../lib/coachNpcRoster'
import { CameraFocusControls } from './CameraFocusControls'
import { NpcCharacter } from './NpcCharacter'
import { NpcSpeechBubble } from './NpcSpeechBubble'

type TeamHQSceneProps = {
  layout?: 'strip' | 'room'
}

type NpcLabelProps = {
  npc: CoachNpc
  isActive: boolean
  isPending: boolean
  compact: boolean
}

type NpcSpeechBubbleAnchorProps = {
  isActive: boolean
  speech: {
    showBubble: boolean
    displayText: string | null
    isTyping: boolean
    isSpeaking: boolean
  }
  compact: boolean
}

function NpcSpeechBubbleAnchor({
  isActive,
  speech,
  compact,
}: NpcSpeechBubbleAnchorProps) {
  if (!isActive || !speech.showBubble) {
    return null
  }

  return (
    <Html
      position={[0, compact ? 2.05 : 2.35, 0]}
      center
      distanceFactor={compact ? 11 : 8}
      style={{ pointerEvents: 'auto', userSelect: 'text' }}
    >
      <NpcSpeechBubble
        text={speech.displayText}
        isTyping={speech.isTyping}
        isSpeaking={speech.isSpeaking}
      />
    </Html>
  )
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
        {isPending ? (
          <span className="text-[10px] font-medium text-violet-400">Connecting…</span>
        ) : null}
      </div>
    </Html>
  )
}

function SceneContent({ layout }: { layout: CoachNpcLayout }) {
  const { roster, active, handoffTarget, isBusy, requestHandoff } = useCoachHandoff()
  const speech = useCoachSpeechBubble()
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
          <group key={npc.id} position={getNpcWorldPosition(npc.id, layout)}>
            <NpcCharacter
              shape={npc.shape}
              color={npc.color}
              isActive={isActive}
              isPending={isPending}
              isClickable={isClickable}
              onSelect={() => void requestHandoff(npc.id)}
            />
            <NpcSpeechBubbleAnchor
              isActive={isActive}
              speech={speech}
              compact={compact}
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

      <CameraFocusControls layout={layout} compact={compact} />
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
