import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import type { EventSchedule } from '../lib/eventSchedule'

type EventScheduleContextValue = {
  schedule: EventSchedule | null
  setSchedule: (schedule: EventSchedule | null) => void
}

const EventScheduleContext = createContext<EventScheduleContextValue | null>(null)

export function EventScheduleProvider({ children }: { children: ReactNode }) {
  const [schedule, setSchedule] = useState<EventSchedule | null>(null)
  const value = useMemo(
    () => ({
      schedule,
      setSchedule,
    }),
    [schedule],
  )

  return (
    <EventScheduleContext.Provider value={value}>
      {children}
    </EventScheduleContext.Provider>
  )
}

export function useEventSchedule() {
  const context = useContext(EventScheduleContext)
  if (!context) {
    throw new Error('useEventSchedule must be used within EventScheduleProvider')
  }
  return context
}
