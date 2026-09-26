import { ApiError, getJson, postJson } from './api'

export interface User {
  id: string
  username: string
  email: string
  roles: string[]
  is_active: boolean
  tenant_id?: string
  display_name?: string
  created_at: string
  updated_at: string
}

export interface AuthMeResponse {
  user: User
  permissions: string[]
  session_expires_at: string
}

export interface LoginInitiateResponse {
  authorization_url: string
  state: string
}

export function validateAuthMeResponse(data: unknown): AuthMeResponse {
  if (!data || typeof data !== 'object') {
    throw new Error('Malformed response from /api/auth/me: payload must be an object.')
  }
  const obj = data as Record<string, unknown>
  if (!obj.user || typeof obj.user !== 'object') {
    throw new Error('Malformed response from /api/auth/me: missing or invalid user object.')
  }
  const user = obj.user as Record<string, unknown>
  if (typeof user.id !== 'string' || typeof user.username !== 'string' || !Array.isArray(user.roles)) {
    throw new Error('Malformed response from /api/auth/me: user object missing required fields.')
  }
  if (!Array.isArray(obj.permissions)) {
    throw new Error('Malformed response from /api/auth/me: permissions must be an array.')
  }
  if (typeof obj.session_expires_at !== 'string') {
    throw new Error('Malformed response from /api/auth/me: missing or invalid session_expires_at.')
  }
  return data as AuthMeResponse
}

export async function fetchCurrentUser(signal?: AbortSignal): Promise<AuthMeResponse | null> {
  try {
    const data = await getJson<unknown>('/api/auth/me', signal)
    return validateAuthMeResponse(data)
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null
    }
    throw error
  }
}

export async function initiateLogin(returnTo?: string, signal?: AbortSignal): Promise<void> {
  const endpoint = returnTo
    ? `/api/auth/oidc/login?return_to=${encodeURIComponent(returnTo)}`
    : '/api/auth/oidc/login'
  const data = await getJson<LoginInitiateResponse>(endpoint, signal)
  if (data && typeof data.authorization_url === 'string') {
    window.location.href = data.authorization_url
  } else {
    throw new Error('Malformed response from /api/auth/oidc/login.')
  }
}

export async function performLogout(signal?: AbortSignal): Promise<void> {
  await postJson<{ status: string }, Record<string, never>>('/api/auth/logout', {}, signal)
}
