import { UserButton } from '@clerk/react'
import { NavLink, Outlet } from 'react-router-dom'

import { WeightLossCoachShell } from './WeightLossCoachShell'

function navLinkClass({ isActive }: { isActive: boolean }) {
  return `block rounded-lg px-3 py-2 text-sm font-medium transition ${
    isActive
      ? 'bg-violet-600 text-white'
      : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
  }`
}

export function Layout() {
  return (
    <WeightLossCoachShell>
      <div className="flex h-full min-h-0 flex-col">
        <header className="shrink-0 space-y-3 border-b border-slate-800 px-4 py-4">
          <div className="flex items-center justify-between gap-3">
            <h1 className="text-lg font-semibold tracking-tight">Weightloss</h1>
            <UserButton />
          </div>

          <nav className="flex flex-col gap-1" aria-label="App sections">
            <NavLink to="/measurements" className={navLinkClass}>
              Body measurements
            </NavLink>
            <NavLink to="/food" className={navLinkClass}>
              Food log
            </NavLink>
            <NavLink to="/metabolism" className={navLinkClass}>
              Metabolism
            </NavLink>
            <NavLink to="/vision" className={navLinkClass}>
              Goal preview
            </NavLink>
          </nav>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
          <Outlet />
        </div>
      </div>
    </WeightLossCoachShell>
  )
}
