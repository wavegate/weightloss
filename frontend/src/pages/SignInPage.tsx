import { SignIn, useAuth } from '@clerk/react'
import { Navigate } from 'react-router-dom'

export function SignInPage() {
  const { isSignedIn } = useAuth()

  if (isSignedIn) {
    return <Navigate to="/measurements" replace />
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-slate-950 px-4">
      <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" />
    </div>
  )
}
