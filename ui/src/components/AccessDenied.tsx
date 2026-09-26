import React from 'react'
import { Button } from './ui/Button'

export interface AccessDeniedProps {
  message?: string
  requiredPermission?: string
  onBack?: () => void
}

export const AccessDenied: React.FC<AccessDeniedProps> = ({
  message = 'You do not have permission to access this resource or perform this action.',
  requiredPermission,
  onBack,
}) => {
  return (
    <div
      role="alert"
      aria-live="assertive"
      className="p-6 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 rounded-xl shadow-sm space-y-4"
    >
      <div className="flex items-start space-x-3">
        <div className="p-2 bg-amber-100 dark:bg-amber-900/60 text-amber-600 dark:text-amber-400 rounded-lg">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-amber-900 dark:text-amber-200">
            Access Denied (403 Forbidden)
          </h3>
          <p className="mt-1 text-sm text-amber-800 dark:text-amber-300">{message}</p>
          {requiredPermission && (
            <p className="mt-2 text-xs font-mono text-amber-700 dark:text-amber-400 bg-amber-100/60 dark:bg-amber-900/80 px-2 py-1 rounded inline-block">
              Required Permission: {requiredPermission}
            </p>
          )}
        </div>
      </div>

      {onBack && (
        <div className="flex justify-end pt-2">
          <Button type="button" variant="secondary" onClick={onBack}>
            Return
          </Button>
        </div>
      )}
    </div>
  )
}
