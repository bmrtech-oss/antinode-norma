import React, { useState } from 'react'
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, FORBIDDEN_EVENT, requestJson } from './api'
import { AuthProvider, useAuth } from './AuthContext'
import { AuthGuard } from '../components/AuthGuard'
import { AccessDenied } from '../components/AccessDenied'
import * as authClient from './authClient'

vi.mock('./authClient', async () => {
  const actual = await vi.importActual<typeof import('./authClient')>('./authClient')
  return {
    ...actual,
    fetchCurrentUser: vi.fn(),
    initiateLogin: vi.fn(),
    performLogout: vi.fn(),
  }
})

const ProtectedView: React.FC = () => {
  const { user, status } = useAuth()
  const [forbiddenError, setForbiddenError] = useState<ApiError | null>(null)

  const trigger401 = async () => {
    // Mock fetch returning 401
    vi.spyOn(window, 'fetch').mockImplementationOnce(async () => {
      return new Response(JSON.stringify({ detail: 'Session expired' }), {
        status: 401,
        statusText: 'Unauthorized',
        headers: { 'Content-Type': 'application/json' },
      })
    })
    try {
      await requestJson('/api/protected/action')
    } catch {
      // Handled by event listener
    }
  }

  const trigger403 = async () => {
    vi.spyOn(window, 'fetch').mockImplementationOnce(async () => {
      return new Response(JSON.stringify({ detail: 'Permission feature:write required' }), {
        status: 403,
        statusText: 'Forbidden',
        headers: { 'Content-Type': 'application/json' },
      })
    })
    try {
      await requestJson('/api/protected/action')
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setForbiddenError(err)
      }
    }
  }

  if (forbiddenError) {
    return (
      <AccessDenied
        message={forbiddenError.message}
        requiredPermission="feature:write"
        onBack={() => setForbiddenError(null)}
      />
    )
  }

  return (
    <div>
      <div data-testid="user-id">{user?.id}</div>
      <div data-testid="auth-status">{status}</div>
      <button onClick={trigger401}>Trigger 401</button>
      <button onClick={trigger403}>Trigger 403</button>
    </div>
  )
}

describe('Central 401 Session Expiry & 403 Access Denied Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.restoreAllMocks()
  })

  it('handles 401 session expiry by clearing stale user state and offering login return path', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockResolvedValueOnce({
      user: {
        id: 'user-401',
        username: 'bob',
        email: 'bob@norma.local',
        roles: ['viewer'],
        is_active: true,
        created_at: '2026-01-01',
        updated_at: '2026-01-01',
      },
      permissions: ['feature:read'],
      session_expires_at: '2026-12-31T23:59:59Z',
    })

    render(
      <AuthProvider>
        <AuthGuard>
          <ProtectedView />
        </AuthGuard>
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('user-id')).toHaveTextContent('user-401')
    })

    await act(async () => {
      fireEvent.click(screen.getByText('Trigger 401'))
    })

    await waitFor(() => {
      expect(screen.getByText('Sign in to Antinode Norma')).toBeInTheDocument()
    })

    expect(screen.queryByTestId('user-id')).not.toBeInTheDocument()
    expect(screen.getByText('Sign in with Identity Provider')).toBeInTheDocument()
  })

  it('handles 403 Forbidden by retaining user identity and rendering AccessDenied', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockResolvedValueOnce({
      user: {
        id: 'user-403',
        username: 'charlie',
        email: 'charlie@norma.local',
        roles: ['viewer'],
        is_active: true,
        created_at: '2026-01-01',
        updated_at: '2026-01-01',
      },
      permissions: ['feature:read'],
      session_expires_at: '2026-12-31T23:59:59Z',
    })

    const forbiddenSpy = vi.fn()
    window.addEventListener(FORBIDDEN_EVENT, forbiddenSpy)

    render(
      <AuthProvider>
        <AuthGuard>
          <ProtectedView />
        </AuthGuard>
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('user-id')).toHaveTextContent('user-403')
    })

    await act(async () => {
      fireEvent.click(screen.getByText('Trigger 403'))
    })

    expect(forbiddenSpy).toHaveBeenCalledTimes(1)

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    expect(screen.getByText('Access Denied (403 Forbidden)')).toBeInTheDocument()
    expect(screen.getByText('Permission feature:write required')).toBeInTheDocument()
    expect(screen.getByText('Required Permission: feature:write')).toBeInTheDocument()

    // Clicking Return recovers back to protected view without re-authenticating
    fireEvent.click(screen.getByText('Return'))

    await waitFor(() => {
      expect(screen.getByTestId('user-id')).toHaveTextContent('user-403')
    })

    window.removeEventListener(FORBIDDEN_EVENT, forbiddenSpy)
  })
})
