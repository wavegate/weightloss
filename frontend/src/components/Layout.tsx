import { UserButton } from '@clerk/react'
import { NavLink, Outlet } from 'react-router-dom'

import { WeightLossCoachShell } from './WeightLossCoachShell'

function navLinkClass({ isActive }: { isActive: boolean }) {
  return `rounded-lg px-4 py-2 text-sm font-medium transition ${
    isActive
      ? 'bg-violet-600 text-white'
      : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
  }`
}

export function Layout() {
  return (
    <WeightLossCoachShell>
      <div className="flex flex-1 flex-col px-4 py-8">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-8">
          <header className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <h1 className="text-3xl font-semibold tracking-tight">Weightloss</h1>
              <UserButton />
            </div>

            <nav className="flex flex-wrap gap-2">
              <NavLink to="/measurements" className={navLinkClass}>
                Body measurements
              </NavLink>
              <NavLink to="/food" className={navLinkClass}>
                Food log
              </NavLink>
              <NavLink to="/metabolism" className={navLinkClass}>
                Metabolism
              </NavLink>
            </nav>
          </header>

          <Outlet />
        </div>
      </div>
    </WeightLossCoachShell>
  )
}
