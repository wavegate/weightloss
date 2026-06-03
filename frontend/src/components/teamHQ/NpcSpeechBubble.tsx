import { CoachVoicePlayButton } from '../CoachVoicePlayButton'

export type NpcSpeechBubbleVoiceControls = {
  canPlay: boolean
  onPlay: () => void
  onStop: () => void
  isLoading: boolean
  isPlaying: boolean
}

type NpcSpeechBubbleProps = {
  text: string | null
  isTyping: boolean
  isSpeaking: boolean
  voice?: NpcSpeechBubbleVoiceControls
}

export function NpcSpeechBubble({
  text,
  isTyping,
  isSpeaking,
  voice,
}: NpcSpeechBubbleProps) {
  if (!text && !isTyping) {
    return null
  }

  return (
    <div
      className={`relative w-[min(26rem,calc(100vw-6rem))] max-w-none rounded-2xl border px-3 py-2 shadow-lg ${
        isSpeaking
          ? 'border-violet-500/50 bg-slate-800/95 shadow-violet-950/30'
          : 'border-slate-600/80 bg-slate-800/90'
      }`}
    >
      {!isTyping && text && voice ? (
        <div className="absolute right-2 top-2">
          <CoachVoicePlayButton
            variant="compact"
            canPlay={voice.canPlay}
            onPlay={voice.onPlay}
            onStop={voice.onStop}
            isLoading={voice.isLoading}
            isPlaying={voice.isPlaying}
          />
        </div>
      ) : null}
      {isTyping ? (
        <p className="text-[10px] leading-relaxed text-slate-300">
          <span className="inline-flex gap-0.5" aria-label="Thinking">
            <span className="animate-pulse">·</span>
            <span className="animate-pulse [animation-delay:120ms]">·</span>
            <span className="animate-pulse [animation-delay:240ms]">·</span>
          </span>
        </p>
      ) : (
        <p className="max-h-52 overflow-y-auto whitespace-pre-wrap pr-7 text-[10px] leading-snug text-slate-100 sm:text-[11px]">
          {text}
        </p>
      )}
      <div
        aria-hidden
        className="absolute -bottom-1.5 left-1/2 h-3 w-3 -translate-x-1/2 rotate-45 border-b border-r border-slate-600/80 bg-slate-800/90"
      />
    </div>
  )
}
