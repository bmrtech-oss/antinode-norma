import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, UNAUTHORIZED_EVENT } from './api'
import { AuthProvider, useAuth } from './AuthContext'
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

const TestConsumer: React.FC = () => {
  const { status, user, permissions, error, logout, hasPermission, hasRole } = useAuth()
  return (
    <div>
      <div data-testid="status">{status}</div>
      <div data-testid="username">{user?.username || 'none'}</div>
      <div data-testid="permissions">{permissions.join(',')}</div>
      <div data-testid="error">{error?.message || 'none'}</div>
      <div data-testid="has-read">{hasPermission('feature:read') ? 'yes' : 'no'}</div>
      <div data-testid="has-admin">{hasRole('admin') ? 'yes' : 'no'}</div>
      <button onClick={() => logout()}>Logout</button>
    </div>
  )
}

describe('AuthProvider & useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('throws when useAuth is used outside AuthProvider', () => {
    const ComponentOutside = () => {
      useAuth()
      return null
    }
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<ComponentOutside />)).toThrow('useAuth must be used within an AuthProvider')
    spy.mockRestore()
  })

  it('bootstraps to authenticated state when fetchCurrentUser resolves', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockResolvedValueOnce({
      user: {
        id: 'u1',
        username: 'alice',
        email: 'alice@norma.local',
        roles: ['admin'],
        is_active: true,
        created_at: '2026-01-01',
        updated_at: '2026-01-01',
      },
      permissions: ['feature:read', 'admin:write'],
      session_expires_at: '2026-12-31T23:59:59Z',
    })

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )

    expect(screen.getByTestId('status')).toHaveTextContent('loading')

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('authenticated')
    })

    expect(screen.getByTestId('username')).toHaveTextContent('alice')
    expect(screen.getByTestId('permissions')).toHaveTextContent('feature:read,admin:write')
    expect(screen.getByTestId('has-read')).toHaveTextContent('yes')
    expect(screen.getByTestId('has-admin')).toHaveTextContent('yes')
  })

  it('bootstraps to anonymous state when fetchCurrentUser returns null (401)', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockResolvedValueOnce(null)

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    })

    expect(screen.getByTestId('username')).toHaveTextContent('none')
    expect(screen.getByTestId('has-read')).toHaveTextContent('no')
  })

  it('bootstraps to error state on transient 500 failure', async () => {
    const error500 = new ApiError({
      status: 500,
      statusText: 'Internal Error',
      detail: 'Server overloaded',
    })
    vi.mocked(authClient.fetchCurrentUser).mockRejectedValueOnce(error500)

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('error')
    })

    expect(screen.getByTestId('error')).toHaveTextContent('Server overloaded')
  })

  it('clears session and sets anonymous state on logout', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockResolvedValueOnce({
      user: {
        id: 'u1',
        username: 'alice',
        email: 'alice@norma.local',
        roles: ['admin'],
        is_active: true,
        created_at: '2026-01-01',
        updated_at: '2026-01-01',
      },
      permissions: ['feature:read'],
      session_expires_at: '2026-12-31T23:59:59Z',
    })
    vi.mocked(authClient.performLogout).mockResolvedValueOnce(undefined)

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('authenticated')
    })

    await act(async () => {
      screen.getByText('Logout').click()
    })

    expect(authClient.performLogout).toHaveBeenCalledTimes(1)
    expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    expect(screen.getByTestId('username')).toHaveTextContent('none')
  })

  it('resets state to anonymous on 401 UNAUTHORIZED_EVENT', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockResolvedValueOnce({
      user: {
        id: 'u1',
        username: 'alice',
        email: 'alice@norma.local',
        roles: ['admin'],
        is_active: true,
        created_at: '2026-01-01',
        updated_at: '2026-01-01',
      },
      permissions: ['feature:read'],
      session_expires_at: '2026-12-31T23:59:59Z',
    })

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('status')).toHaveTextContent('authenticated')
    })

    act(() => {
      window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT))
    })

    expect(screen.getByTestId('status')).toHaveTextContent('anonymous')
    expect(screen.getByTestId('username')).toHaveTextContent('none')
  })
})
