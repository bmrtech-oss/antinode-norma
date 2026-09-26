import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthGuard } from './AuthGuard'
import * as authClient from '../lib/authClient'
import { AuthProvider } from '../lib/AuthContext'

vi.mock('../lib/authClient', async () => {
  const actual = await vi.importActual<typeof import('../lib/authClient')>('../lib/authClient')
  return {
    ...actual,
    fetchCurrentUser: vi.fn(),
    initiateLogin: vi.fn(),
    performLogout: vi.fn(),
  }
})

describe('AuthGuard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading indicator while resolving authentication session', () => {
    vi.mocked(authClient.fetchCurrentUser).mockReturnValue(new Promise(() => {}))

    const childApiCallSpy = vi.fn()
    const ProtectedComponent = () => {
      childApiCallSpy()
      return <div>Protected Content</div>
    }

    render(
      <AuthProvider>
        <AuthGuard>
          <ProtectedComponent />
        </AuthGuard>
      </AuthProvider>,
    )

    expect(screen.getByRole('status')).toHaveTextContent('Resolving authentication session...')
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    expect(childApiCallSpy).not.toHaveBeenCalled()
  })

  it('renders LoginPage and blocks protected children when status is anonymous', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockResolvedValueOnce(null)

    const childApiCallSpy = vi.fn()
    const ProtectedComponent = () => {
      childApiCallSpy()
      return <div>Protected Content</div>
    }

    render(
      <AuthProvider>
        <AuthGuard>
          <ProtectedComponent />
        </AuthGuard>
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText('Sign in to Antinode Norma')).toBeInTheDocument()
    })

    expect(screen.getByText('Sign in with Identity Provider')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    expect(childApiCallSpy).not.toHaveBeenCalled()
  })

  it('calls initiateLogin when sign in button is clicked in LoginPage', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockResolvedValueOnce(null)
    vi.mocked(authClient.initiateLogin).mockResolvedValueOnce(undefined)

    render(
      <AuthProvider>
        <AuthGuard>
          <div>Protected Content</div>
        </AuthGuard>
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText('Sign in with Identity Provider')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Sign in with Identity Provider'))

    expect(authClient.initiateLogin).toHaveBeenCalledTimes(1)
  })

  it('renders error state on session resolution failure', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockRejectedValueOnce(new Error('Network offline'))

    render(
      <AuthProvider>
        <AuthGuard>
          <div>Protected Content</div>
        </AuthGuard>
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText('Authentication Error')).toBeInTheDocument()
    })

    expect(screen.getByText('Network offline')).toBeInTheDocument()
    expect(screen.getByText('Retry Session Check')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('renders protected children when status is authenticated', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockResolvedValueOnce({
      user: {
        id: 'u1',
        username: 'alice',
        email: 'alice@norma.local',
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
          <div>Protected Dashboard Content</div>
        </AuthGuard>
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText('Protected Dashboard Content')).toBeInTheDocument()
    })
  })

  it('renders AccessDenied when user lacks required permission', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockResolvedValueOnce({
      user: {
        id: 'u1',
        username: 'alice',
        email: 'alice@norma.local',
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
        <AuthGuard requiredPermission="approval:action">
          <div>Protected Content</div>
        </AuthGuard>
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText(/Access Denied/i)).toBeInTheDocument()
    })

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })
})
