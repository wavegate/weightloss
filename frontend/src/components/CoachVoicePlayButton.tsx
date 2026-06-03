import { useContext } from 'react'

import { CoachVoiceContext } from './CoachVoiceContext'

function SpeakerIcon() {
  return (
    <svg aria-hidden className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
      <path d="M9.383 3.076A1 1 0 0 1 10 4v12a1 1 0 0 1-1.617.793L5.293 13H3a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1h2.293l3.09-3.793a1 1 0 0 1 1 .869Z" />
      <path d="M12.293 7.293a1 1 0 0 1 1.414 0L15 8.586l1.293-1.293a1 1 0 1 1 1.414 1.414L16.414 10l1.293 1.293a1 1 0 0 1-1.414 1.414L15 11.414l-1.293 1.293a1 1 0 0 1-1.414-1.414L13.586 10l-1.293-1.293a1 1 0 0 1 0-1.414Z" />
    </svg>
  )
}

export type CoachVoicePlayButtonProps = {
  variant?: 'compact' | 'default'
  className?: string
  canPlay?: boolean
  onPlay?: () => void
  onStop?: () => void
  isLoading?: boolean
  isPlaying?: boolean
  errorMessage?: string | null
}

export function CoachVoicePlayButton({
  variant = 'default',
  className = '',
  canPlay: canPlayProp,
  onPlay,
  onStop,
  isLoading: isLoadingProp,
  isPlaying: isPlayingProp,
  errorMessage: errorMessageProp,
}: CoachVoicePlayButtonProps) {
  const context = useContext(CoachVoiceContext)

  const canPlay = canPlayProp ?? context?.canPlay ?? false
  const playReply = onPlay ?? context?.playReply
  const stopReply = onStop ?? context?.stopReply
  const isLoading = isLoadingProp ?? context?.isLoading ?? false
  const isPlaying = isPlayingProp ?? context?.isPlaying ?? false
  const errorMessage = errorMessageProp ?? context?.errorMessage ?? null

  const compact = variant === 'compact'

  const label = isLoading
    ? 'Generating voice…'
    : isPlaying
      ? 'Stop voice'
      : 'Play voice'

  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      <button
        type="button"
        disabled={!canPlay && !isPlaying && !isLoading}
        onClick={() => {
          if (isPlaying || isLoading) {
            stopReply?.()
            return
          }
          playReply?.()
        }}
        title={label}
        aria-label={label}
        className={`inline-flex items-center justify-center gap-1.5 rounded-lg border font-medium transition disabled:cursor-not-allowed disabled:opacity-40 ${
          compact
            ? 'h-7 min-w-7 border-slate-600 bg-slate-800/90 px-2 text-[10px] text-slate-200 hover:border-violet-500/60 hover:bg-slate-700'
            : 'border-slate-600 bg-slate-800 px-3 py-1.5 text-xs text-slate-200 hover:border-violet-500/60 hover:bg-slate-700'
        } ${isPlaying ? 'border-violet-500/70 text-violet-200' : ''}`}
      >
        <SpeakerIcon />
        {!compact ? (
          <span>{isLoading ? 'Loading…' : isPlaying ? 'Stop' : 'Listen'}</span>
        ) : null}
      </button>
      {errorMessage && !compact ? (
        <p className="text-[10px] text-red-400" role="alert">
          {errorMessage}
        </p>
      ) : null}
    </div>
  )
}
