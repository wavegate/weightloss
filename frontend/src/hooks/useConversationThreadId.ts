import { useState } from 'react'

/**
 * One thread id for the lifetime of the mounted CopilotKit provider.
 * Remounting (e.g. page refresh) starts a fresh conversation instead of
 * reloading a prior LangGraph checkpoint.
 */
export function useConversationThreadId(
  userId: string | null | undefined,
  namespace: string,
): string {
  const [sessionId] = useState(() => crypto.randomUUID())
  return `${userId ?? ''}:${namespace}:${sessionId}`
}
