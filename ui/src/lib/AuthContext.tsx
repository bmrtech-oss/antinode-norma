import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { UNAUTHORIZED_EVENT } from './api'
import {
  fetchCurrentUser,
  initiateLogin,
  performLogout,
  User,
} from './authClient'

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous' | 'error'

export interface AuthContextValue {
  status: AuthStatus
  user: User | null
  permissions: string[]
  sessionExpiresAt: string | null
  error: Error | null
  login: (returnTo?: string) => Promise<void>
  logout: () => Promise<void>
  refetch: () => Promise<void>
  hasPermission: (permission: string) => boolean
  hasRole: (role: string) => boolean
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export interface AuthProviderProps {
  children: React.ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [status, setStatus] = useState<AuthStatus>('loading')
  const [user, setUser] = useState<User | null>(null)
  const [permissions, setPermissions] = useState<string[]>([])
  const [sessionExpiresAt, setSessionExpiresAt] = useState<string | null>(null)
  const [error, setError] = useState<Error | null>(null)

  const bootstrap = useCallback(async () => {
    setStatus('loading')
    setError(null)
    try {
      const res = await fetchCurrentUser()
      if (res) {
        setUser(res.user)
        setPermissions(res.permissions)
        setSessionExpiresAt(res.session_expires_at)
        setStatus('authenticated')
      } else {
        setUser(null)
        setPermissions([])
        setSessionExpiresAt(null)
        setStatus('anonymous')
      }
    } catch (err) {
      setUser(null)
      setPermissions([])
      setSessionExpiresAt(null)
      setError(err instanceof Error ? err : new Error(String(err)))
      setStatus('error')
    }
  }, [])

  useEffect(() => {
    bootstrap()
  }, [bootstrap])

  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null)
      setPermissions([])
      setSessionExpiresAt(null)
      setError(null)
      setStatus('anonymous')
    }

    if (typeof window !== 'undefined') {
      window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized)
      return () => {
        window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized)
      }
    }
  }, [])

  const login = useCallback(async (returnTo?: string) => {
    await initiateLogin(returnTo)
  }, [])

  const logout = useCallback(async () => {
    try {
      await performLogout()
    } finally {
      setUser(null)
      setPermissions([])
      setSessionExpiresAt(null)
      setError(null)
      setStatus('anonymous')
    }
  }, [])

  const hasPermission = useCallback(
    (permission: string) => permissions.includes(permission),
    [permissions],
  )

  const hasRole = useCallback(
    (role: string) => Boolean(user?.roles?.includes(role)),
    [user],
  )

  const value: AuthContextValue = {
    status,
    user,
    permissions,
    sessionExpiresAt,
    error,
    login,
    logout,
    refetch: bootstrap,
    hasPermission,
    hasRole,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
