import React from 'react'
import { useAuth } from '../lib/AuthContext'
import { LoginPage } from './LoginPage'
import { AccessDenied } from './AccessDenied'
import { Button } from './ui/Button'

export interface AuthGuardProps {
  requiredPermission?: string
  requiredRole?: string
  children: React.ReactNode
}

export const AuthGuard: React.FC<AuthGuardProps> = ({
  requiredPermission,
  requiredRole,
  children,
}) => {
  const { status, error, refetch, hasPermission, hasRole } = useAuth()

  if (status === 'loading') {
    return (
      <div
        role="status"
        aria-live="polite"
        className="min-h-[50vh] flex flex-col justify-center items-center p-8 space-y-4 text-slate-600 dark:text-slate-400"
      >
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-medium">Resolving authentication session...</p>
      </div>
    )
  }

  if (status === 'anonymous') {
    return <LoginPage />
  }

  if (status === 'error') {
    return (
      <div className="min-h-[50vh] flex flex-col justify-center items-center p-4">
        <div className="max-w-md w-full bg-white dark:bg-slate-800 p-6 rounded-xl shadow border border-red-200 dark:border-red-900 space-y-4">
          <div className="flex items-center space-x-3 text-red-600 dark:text-red-400">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
              Authentication Error
            </h3>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {error?.message || 'Unable to resolve your authentication session.'}
          </p>
          <div className="pt-2 flex justify-end">
            <Button type="button" onClick={() => refetch()}>
              Retry Session Check
            </Button>
          </div>
        </div>
      </div>
    )
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <AccessDenied message={`You do not have the required permission (${requiredPermission}) to access this view.`} />
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return <AccessDenied message={`You do not have the required role (${requiredRole}) to access this view.`} />
  }

  return <>{children}</>
}
