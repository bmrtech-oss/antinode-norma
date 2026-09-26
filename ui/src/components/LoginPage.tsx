import React, { useState } from 'react'
import { useAuth } from '../lib/AuthContext'
import { validateLocalReturnPath } from '../lib/returnPath'
import { Button } from './ui/Button'

export interface LoginPageProps {
  returnTo?: string
}

export const LoginPage: React.FC<LoginPageProps> = ({ returnTo }) => {
  const { login } = useAuth()
  const [submitting, setSubmitting] = useState(false)
  const [loginError, setLoginError] = useState<string | null>(null)

  const handleSignIn = async () => {
    setSubmitting(true)
    setLoginError(null)
    try {
      const rawTarget =
        returnTo ||
        (typeof window !== 'undefined'
          ? `${window.location.pathname}${window.location.search}`
          : '/')
      const sanitizedTarget = validateLocalReturnPath(rawTarget)
      await login(sanitizedTarget)
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : 'Unable to initiate sign-in')
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-[60vh] flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white dark:bg-slate-800 p-8 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-400 mb-4">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Sign in to Antinode Norma
          </h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Enterprise BDD Feature Generation, Quality Gates, and Governance Platform
          </p>
        </div>

        {loginError && (
          <div
            role="alert"
            className="p-4 rounded-md bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 text-sm text-red-700 dark:text-red-300"
          >
            {loginError}
          </div>
        )}

        <div className="mt-8 space-y-6">
          <Button
            type="button"
            className="w-full justify-center text-base py-3"
            onClick={handleSignIn}
            disabled={submitting}
          >
            {submitting ? 'Redirecting to Identity Provider...' : 'Sign in with Identity Provider'}
          </Button>

          <p className="text-xs text-center text-slate-500 dark:text-slate-400">
            Norma delegates authentication to your configured enterprise OIDC Identity Provider (Authentik). No passwords are stored locally.
          </p>
        </div>
      </div>
    </div>
  )
}
