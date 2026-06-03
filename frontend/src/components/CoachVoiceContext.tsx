import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  type ReactNode,
} from 'react'

import { useCoachSpeechBubble } from '../hooks/useCoachSpeechBubble'
import { useCoachVoicePlayback } from '../hooks/useCoachVoicePlayback'
import type { ActiveCoachAgent } from '../lib/coachNpcRoster'

export type CoachVoicePlaybackStatus = 'idle' | 'loading' | 'playing' | 'error'

export type CoachVoiceContextValue = {
  active: ActiveCoachAgent
  showBubble: boolean
  isSpeaking: boolean
  displayText: string | null
  isTyping: boolean
  canPlay: boolean
  playReply: () => void
  stopReply: () => void
  status: CoachVoicePlaybackStatus
  errorMessage: string | null
  isLoading: boolean
  isPlaying: boolean
}

export const CoachVoiceContext = createContext<CoachVoiceContextValue | null>(
  null,
)

export function CoachVoiceProvider({ children }: { children: ReactNode }) {
  const speech = useCoachSpeechBubble()
  const {
    play,
    stop,
    status,
    errorMessage,
    isLoading,
    isPlaying,
  } = useCoachVoicePlayback()

  const canPlay = Boolean(speech.displayText?.trim()) && !speech.isTyping

  useEffect(() => {
    if (speech.isTyping) {
      stop()
    }
  }, [speech.isTyping, stop])

  const value = useMemo<CoachVoiceContextValue>(
    () => ({
      active: speech.active,
      showBubble: speech.showBubble,
      isSpeaking: speech.isSpeaking,
      displayText: speech.displayText,
      isTyping: speech.isTyping,
      canPlay,
      playReply: () => {
        if (speech.displayText) {
          void play(speech.displayText)
        }
      },
      stopReply: stop,
      status,
      errorMessage,
      isLoading,
      isPlaying,
    }),
    [canPlay, errorMessage, isLoading, isPlaying, play, speech, status, stop],
  )

  return (
    <CoachVoiceContext.Provider value={value}>{children}</CoachVoiceContext.Provider>
  )
}

export function useCoachVoice() {
  const context = useContext(CoachVoiceContext)
  if (!context) {
    throw new Error('useCoachVoice must be used within CoachVoiceProvider')
  }
  return context
}
