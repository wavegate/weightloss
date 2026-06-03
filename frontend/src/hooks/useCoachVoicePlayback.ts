import { useCallback, useEffect, useRef, useState } from 'react'

import { synthesizeCoachSpeech } from '../services/voiceService'
import { ApiError } from '../services/api'

export type CoachVoicePlaybackStatus = 'idle' | 'loading' | 'playing' | 'error'

export function useCoachVoicePlayback() {
  const [status, setStatus] = useState<CoachVoicePlaybackStatus>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const objectUrlRef = useRef<string | null>(null)
  const fetchAbortRef = useRef<AbortController | null>(null)

  const cleanupAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.onended = null
      audioRef.current.onerror = null
      audioRef.current = null
    }
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current)
      objectUrlRef.current = null
    }
  }, [])

  const stop = useCallback(() => {
    fetchAbortRef.current?.abort()
    fetchAbortRef.current = null
    cleanupAudio()
    setStatus('idle')
    setErrorMessage(null)
  }, [cleanupAudio])

  const play = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed) {
        return
      }

      if (status === 'playing') {
        stop()
        return
      }

      stop()
      setStatus('loading')
      setErrorMessage(null)

      const abort = new AbortController()
      fetchAbortRef.current = abort

      try {
        const blob = await synthesizeCoachSpeech(trimmed, abort.signal)
        if (abort.signal.aborted) {
          return
        }

        const url = URL.createObjectURL(blob)
        objectUrlRef.current = url
        const audio = new Audio(url)
        audioRef.current = audio

        audio.onended = () => {
          cleanupAudio()
          setStatus('idle')
        }
        audio.onerror = () => {
          cleanupAudio()
          setStatus('error')
          setErrorMessage('Could not play audio.')
        }

        await audio.play()
        setStatus('playing')
      } catch (error) {
        if (abort.signal.aborted) {
          return
        }
        cleanupAudio()
        setStatus('error')
        if (error instanceof ApiError) {
          setErrorMessage(error.message)
        } else if (error instanceof Error) {
          setErrorMessage(error.message)
        } else {
          setErrorMessage('Voice playback failed.')
        }
      } finally {
        if (fetchAbortRef.current === abort) {
          fetchAbortRef.current = null
        }
      }
    },
    [cleanupAudio, status, stop],
  )

  useEffect(() => () => stop(), [stop])

  return {
    status,
    errorMessage,
    play,
    stop,
    isLoading: status === 'loading',
    isPlaying: status === 'playing',
  }
}
