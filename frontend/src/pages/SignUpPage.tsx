import { SignUp, useAuth } from '@clerk/react'
import { Navigate } from 'react-router-dom'

export function SignUpPage() {
  const { isSignedIn } = useAuth()

  if (isSignedIn) {
    return <Navigate to="/measurements" replace />
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-slate-950 px-4">
      <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" />
    </div>
  )
}
