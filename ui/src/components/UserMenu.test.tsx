import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { UserMenu } from './UserMenu'
import { AuthProvider } from '../lib/AuthContext'
import * as authClient from '../lib/authClient'

vi.mock('../lib/authClient', async () => {
  const actual = await vi.importActual<typeof import('../lib/authClient')>('../lib/authClient')
  return {
    ...actual,
    fetchCurrentUser: vi.fn(),
    initiateLogin: vi.fn(),
    performLogout: vi.fn(),
  }
})

describe('UserMenu Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders null when status is not authenticated', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockResolvedValueOnce(null)

    const { container } = render(
      <AuthProvider>
        <UserMenu />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(container.firstChild).toBeNull()
    })
  })

  it('renders authenticated user button and opens user menu on click', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockResolvedValueOnce({
      user: {
        id: 'u-admin',
        username: 'admin_user',
        email: 'admin@norma.local',
        roles: ['admin', 'reviewer'],
        display_name: 'Admin User',
        is_active: true,
        created_at: '2026-01-01',
        updated_at: '2026-01-01',
      },
      permissions: ['feature:read', 'admin:write'],
      session_expires_at: '2026-12-31T23:59:59Z',
    })

    render(
      <AuthProvider>
        <UserMenu />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText('Admin User')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /User menu for Admin User/ }))

    expect(screen.getByRole('menu')).toBeInTheDocument()
    expect(screen.getByText('admin@norma.local')).toBeInTheDocument()
    expect(screen.getByText('admin')).toBeInTheDocument()
    expect(screen.getByText('reviewer')).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Sign Out' })).toBeInTheDocument()
  })

  it('calls performLogout when Sign Out is clicked', async () => {
    vi.mocked(authClient.fetchCurrentUser).mockResolvedValueOnce({
      user: {
        id: 'u-user',
        username: 'john_doe',
        email: 'john@norma.local',
        roles: ['viewer'],
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
        <UserMenu />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByText('john_doe')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /User menu for john_doe/ }))

    await act(async () => {
      fireEvent.click(screen.getByRole('menuitem', { name: 'Sign Out' }))
    })

    expect(authClient.performLogout).toHaveBeenCalledTimes(1)
  })
})
