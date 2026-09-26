// @vitest-environment jsdom
import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AppShell } from './AppShell'
import { AuthContextValue } from '../lib/AuthContext'

const mockAuthContext = vi.hoisted(() => {
  const dummyUser = {
    id: 'v1',
    username: 'viewer',
    email: 'v@norma.local',
    roles: ['viewer'],
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  }
  return {
    dummyUser,
    value: {
      status: 'authenticated',
      user: dummyUser,
      permissions: ['feature:read', 'audit:read'],
      sessionExpiresAt: null,
      error: null,
      login: vi.fn(),
      logout: vi.fn(),
      refetch: vi.fn(),
      hasPermission: (perm: string) => ['feature:read', 'audit:read'].includes(perm),
      hasRole: (role: string) => role === 'viewer',
    } as unknown as AuthContextValue,
  }
})

vi.mock('../lib/AuthContext', () => ({
  useAuth: () => mockAuthContext.value,
}))

describe('AppShell navigation filtering', () => {
  const defaultProps = {
    activeTab: 'dashboard' as const,
    health: { version: '1.0.0' },
    loading: false,
    apiBaseUrl: 'http://localhost:8000',
    onApiBaseUrlChange: vi.fn(),
    onHealthCheck: vi.fn(),
    onTabChange: vi.fn(),
  }

  it('renders only permitted navigation tabs for Viewer role', () => {
    mockAuthContext.value = {
      ...mockAuthContext.value,
      user: { ...mockAuthContext.dummyUser, id: 'v1', username: 'viewer', roles: ['viewer'] },
      permissions: ['feature:read', 'audit:read'],
      hasPermission: (perm: string) => ['feature:read', 'audit:read'].includes(perm),
    }

    render(<AppShell {...defaultProps}><div>Test content</div></AppShell>)

    expect(screen.getByRole('tab', { name: /dashboard/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /feature review/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /traceability/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /audit log/i })).toBeInTheDocument()

    // Viewer should NOT see Generation (feature:write) or Approval Queue (approval:action)
    expect(screen.queryByRole('tab', { name: /generation/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: /approval queue/i })).not.toBeInTheDocument()
  })

  it('renders all tabs for Admin / Reviewer with write and approval permissions', () => {
    mockAuthContext.value = {
      ...mockAuthContext.value,
      user: { ...mockAuthContext.dummyUser, id: 'a1', username: 'admin', roles: ['admin'] },
      permissions: ['feature:read', 'feature:write', 'approval:action', 'audit:read', 'admin:write'],
      hasPermission: () => true,
    }

    render(<AppShell {...defaultProps}><div>Test content</div></AppShell>)

    expect(screen.getByRole('tab', { name: /dashboard/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /generation/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /feature review/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /approval queue/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /traceability/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /audit log/i })).toBeInTheDocument()
  })
})
