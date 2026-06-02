import { useAuth } from '@clerk/react'

import { useMetabolicProfile } from '../hooks/useMetabolicProfile'

function ProfileSummary() {
  const { data: profile, isLoading } = useMetabolicProfile()

  if (isLoading) {
    return <p className="text-sm text-slate-400">Loading saved profile…</p>
  }

  if (!profile) {
    return (
      <p className="text-sm text-slate-400">
        No saved profile yet. Ask the weight loss coach in the sidebar to
        estimate BMR and TDEE, then save when you are ready.
      </p>
    )
  }

  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-4">
      <div>
        <dt className="text-slate-500">BMR</dt>
        <dd className="font-medium text-slate-100">
          {profile.bmr_kcal != null ? `${Math.round(profile.bmr_kcal)} kcal` : '—'}
        </dd>
      </div>
      <div>
        <dt className="text-slate-500">TDEE</dt>
        <dd className="font-medium text-slate-100">
          {profile.tdee_kcal != null
            ? `${Math.round(profile.tdee_kcal)} kcal`
            : '—'}
        </dd>
      </div>
      <div>
        <dt className="text-slate-500">Activity</dt>
        <dd className="font-medium capitalize text-slate-100">
          {profile.activity_level.replace('_', ' ')}
        </dd>
      </div>
      <div>
        <dt className="text-slate-500">Age / height</dt>
        <dd className="font-medium text-slate-100">
          {profile.age_years} yr · {Math.round(profile.height_cm)} cm
        </dd>
      </div>
    </dl>
  )
}

export function MetabolismPage() {
  const { userId, isLoaded } = useAuth()

  if (!isLoaded) {
    return <p className="text-sm text-slate-400">Loading…</p>
  }

  if (!userId) {
    return <p className="text-sm text-slate-400">Sign in to view your profile.</p>
  }

  return (
    <section className="flex flex-col gap-6">
      <div className="space-y-2">
        <h2 className="text-xl font-medium text-slate-100">Metabolic profile</h2>
        <p className="text-sm text-slate-400">
          BMR and TDEE from the Mifflin–St Jeor equation. Use the coach in the
          left sidebar to update your profile.
        </p>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
        <h3 className="mb-3 text-sm font-medium text-slate-300">Saved profile</h3>
        <ProfileSummary />
      </div>
    </section>
  )
}
