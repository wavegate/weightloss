import { useEffect, useState } from 'react'

export function usePanelOpen(storageKey: string, defaultOpen = true) {
  const [open, setOpen] = useState(() => {
    try {
      const stored = localStorage.getItem(storageKey)
      if (stored === null) {
        return defaultOpen
      }
      return stored === 'true'
    } catch {
      return defaultOpen
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, String(open))
    } catch {
      // ignore quota / private mode
    }
  }, [open, storageKey])

  return [open, setOpen] as const
}
