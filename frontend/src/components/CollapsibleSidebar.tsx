import type { ReactNode } from 'react'

import { usePanelOpen } from '../hooks/usePanelOpen'

type CollapsibleSidebarProps = {
  side: 'left' | 'right'
  label: string
  storageKey: string
  defaultOpen?: boolean
  expandedWidthClass?: string
  children: ReactNode
}

function ChevronIcon({ direction }: { direction: 'left' | 'right' }) {
  return (
    <svg
      aria-hidden
      className="h-4 w-4"
      viewBox="0 0 20 20"
      fill="currentColor"
    >
      {direction === 'left' ? (
        <path
          fillRule="evenodd"
          d="M12.79 5.23a.75.75 0 0 1-.02 1.06L8.832 10l3.938 3.71a.75.75 0 1 1-1.04 1.08l-4.5-4.25a.75.75 0 0 1 0-1.08l4.5-4.25a.75.75 0 0 1 1.06.02Z"
          clipRule="evenodd"
        />
      ) : (
        <path
          fillRule="evenodd"
          d="M7.21 14.77a.75.75 0 0 1 .02-1.06L11.168 10 7.23 6.29a.75.75 0 1 1 1.04-1.08l4.5 4.25a.75.75 0 0 1 0 1.08l-4.5 4.25a.75.75 0 0 1-1.06-.02Z"
          clipRule="evenodd"
        />
      )}
    </svg>
  )
}

export function CollapsibleSidebar({
  side,
  label,
  storageKey,
  defaultOpen = true,
  expandedWidthClass = 'w-80',
  children,
}: CollapsibleSidebarProps) {
  const [open, setOpen] = usePanelOpen(storageKey, defaultOpen)
  const borderClass = side === 'left' ? 'border-r' : 'border-l'
  const collapseDirection = side === 'left' ? 'left' : 'right'
  const expandDirection = side === 'left' ? 'right' : 'left'

  if (!open) {
    return (
      <aside
        className={`flex w-11 shrink-0 flex-col items-center border-slate-800 bg-slate-900 py-3 ${borderClass}`}
      >
        <button
          type="button"
          onClick={() => setOpen(true)}
          title={`Open ${label}`}
          aria-label={`Open ${label}`}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-slate-100"
        >
          <ChevronIcon direction={expandDirection} />
        </button>
        <span
          className="mt-3 text-[10px] font-medium uppercase tracking-wider text-slate-500 [writing-mode:vertical-rl]"
          aria-hidden
        >
          {label}
        </span>
      </aside>
    )
  }

  return (
    <aside
      className={`flex h-full min-h-0 shrink-0 flex-col overflow-hidden border-slate-800 bg-slate-900 ${borderClass} ${expandedWidthClass} max-w-[min(100vw,28rem)]`}
    >
      <div className="flex shrink-0 items-center justify-between gap-2 border-b border-slate-800 px-3 py-2">
        <span className="truncate text-sm font-medium text-slate-200">{label}</span>
        <button
          type="button"
          onClick={() => setOpen(false)}
          title={`Collapse ${label}`}
          aria-label={`Collapse ${label}`}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-slate-100"
        >
          <ChevronIcon direction={collapseDirection} />
        </button>
      </div>
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">{children}</div>
    </aside>
  )
}
