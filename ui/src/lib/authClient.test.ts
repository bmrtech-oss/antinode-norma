import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from './api'
import {
  fetchCurrentUser,
  initiateLogin,
  performLogout,
  validateAuthMeResponse,
} from './authClient'

vi.mock('./api', async () => {
  const actual = await vi.importActual<typeof import('./api')>('./api')
  return {
    ...actual,
    getJson: vi.fn(),
    postJson: vi.fn(),
  }
})

import { getJson, postJson } from './api'

describe('authClient', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('validateAuthMeResponse', () => {
    it('validates a correct AuthMeResponse payload', () => {
      const valid = {
        user: {
          id: 'u-1',
          username: 'alice',
          email: 'alice@norma.local',
          roles: ['admin'],
          is_active: true,
          created_at: '2026-01-01',
          updated_at: '2026-01-01',
        },
        permissions: ['feature:read', 'admin:write'],
        session_expires_at: '2026-12-31T23:59:59Z',
      }
      expect(validateAuthMeResponse(valid)).toEqual(valid)
    })

    it('throws error for non-object payload', () => {
      expect(() => validateAuthMeResponse('not-an-object')).toThrow('payload must be an object')
    })

    it('throws error for payload missing user', () => {
      expect(() => validateAuthMeResponse({ permissions: [] })).toThrow('missing or invalid user object')
    })

    it('throws error for user object missing required fields', () => {
      expect(() => validateAuthMeResponse({ user: { id: 'u1' } })).toThrow('user object missing required fields')
    })

    it('throws error for non-array permissions', () => {
      expect(() =>
        validateAuthMeResponse({
          user: { id: 'u1', username: 'a', roles: [] },
          permissions: 'not-an-array',
        }),
      ).toThrow('permissions must be an array')
    })

    it('throws error for missing session_expires_at', () => {
      expect(() =>
        validateAuthMeResponse({
          user: { id: 'u1', username: 'a', roles: [] },
          permissions: [],
        }),
      ).toThrow('missing or invalid session_expires_at')
    })
  })

  describe('fetchCurrentUser', () => {
    it('returns AuthMeResponse on 200 OK', async () => {
      const mockResponse = {
        user: {
          id: 'user-123',
          username: 'test_user',
          email: 'user@example.com',
          roles: ['viewer'],
          is_active: true,
          created_at: '2026-01-01',
          updated_at: '2026-01-01',
        },
        permissions: ['feature:read'],
        session_expires_at: '2026-12-31T23:59:59Z',
      }
      vi.mocked(getJson).mockResolvedValueOnce(mockResponse)

      const result = await fetchCurrentUser()
      expect(getJson).toHaveBeenCalledWith('/api/auth/me', undefined)
      expect(result).toEqual(mockResponse)
    })

    it('returns null on 401 Unauthorized', async () => {
      vi.mocked(getJson).mockRejectedValueOnce(
        new ApiError({
          status: 401,
          statusText: 'Unauthorized',
          detail: 'Authentication required',
        }),
      )

      const result = await fetchCurrentUser()
      expect(result).toBeNull()
    })

    it('re-throws ApiError on 500 Internal Server Error', async () => {
      const error500 = new ApiError({
        status: 500,
        statusText: 'Internal Server Error',
        detail: 'Database failure',
      })
      vi.mocked(getJson).mockRejectedValueOnce(error500)

      await expect(fetchCurrentUser()).rejects.toThrow(error500)
    })

    it('throws Error on malformed response', async () => {
      vi.mocked(getJson).mockResolvedValueOnce({ user: { id: 'bad' } })

      await expect(fetchCurrentUser()).rejects.toThrow('user object missing required fields')
    })
  })

  describe('initiateLogin', () => {
    it('fetches authorization URL and redirects location', async () => {
      const originalLocation = window.location
      const mockLocation = { href: '' } as Location
      Object.defineProperty(window, 'location', {
        configurable: true,
        writable: true,
        value: mockLocation,
      })

      vi.mocked(getJson).mockResolvedValueOnce({
        authorization_url: 'https://auth.example.com/oidc/auth?state=xyz',
        state: 'xyz',
      })

      await initiateLogin('/dashboard')
      expect(getJson).toHaveBeenCalledWith('/api/auth/oidc/login?return_to=%2Fdashboard', undefined)
      expect(window.location.href).toBe('https://auth.example.com/oidc/auth?state=xyz')

      Object.defineProperty(window, 'location', {
        configurable: true,
        writable: true,
        value: originalLocation,
      })
    })
  })

  describe('performLogout', () => {
    it('calls /api/auth/logout endpoint', async () => {
      vi.mocked(postJson).mockResolvedValueOnce({ status: 'logged_out' })

      await performLogout()
      expect(postJson).toHaveBeenCalledWith('/api/auth/logout', {}, undefined)
    })
  })
})
