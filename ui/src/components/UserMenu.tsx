import React, { useState } from 'react'
import { useAuth } from '../lib/AuthContext'
import { Button } from './ui/Button'

export const UserMenu: React.FC = () => {
  const { user, status, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)

  if (status !== 'authenticated' || !user) {
    return null
  }

  const handleLogout = async () => {
    setLoggingOut(true)
    try {
      await logout()
    } finally {
      setLoggingOut(false)
      setOpen(false)
    }
  }

  const displayName = user.display_name || user.username
  const roles = user.roles || []

  return (
    <div className="relative inline-block text-left">
      <button
        type="button"
        id="user-menu-button"
        aria-expanded={open}
        aria-haspopup="true"
        aria-label={`User menu for ${displayName}`}
        onClick={() => setOpen((prev) => !prev)}
        className="flex items-center space-x-2 p-1.5 rounded-lg text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold text-sm">
          {displayName.charAt(0).toUpperCase()}
        </div>
        <span className="hidden md:inline-block text-sm font-medium max-w-[120px] truncate">
          {displayName}
        </span>
        <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div
          role="menu"
          aria-orientation="vertical"
          aria-labelledby="user-menu-button"
          className="origin-top-right absolute right-0 mt-2 w-64 rounded-xl shadow-lg bg-white dark:bg-slate-800 ring-1 ring-black/5 dark:ring-slate-700 p-4 z-50 space-y-3"
        >
          <div className="border-b border-slate-100 dark:border-slate-700 pb-3">
            <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">
              {displayName}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{user.email}</p>
            {roles.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {roles.map((role) => (
                  <span
                    key={role}
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300 capitalize"
                  >
                    {role}
                  </span>
                ))}
              </div>
            )}
          </div>

          <Button
            type="button"
            variant="secondary"
            className="w-full justify-center text-sm"
            onClick={handleLogout}
            disabled={loggingOut}
            role="menuitem"
          >
            {loggingOut ? 'Signing out...' : 'Sign Out'}
          </Button>
        </div>
      )}
    </div>
  )
}
