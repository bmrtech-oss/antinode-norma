import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  API_BASE_URL_STORAGE_KEY,
  getApiBaseUrl,
  getJson,
  postJson,
  resetApiBaseUrl,
  setApiBaseUrl,
} from './lib/api'

describe('API endpoint configuration', () => {
  beforeEach(() => {
    window.localStorage.clear()
    vi.restoreAllMocks()
  })

  it('persists and normalizes a selected integration endpoint', () => {
    expect(setApiBaseUrl('https://qa.example.test/platform/')).toBe('https://qa.example.test/platform')
    expect(getApiBaseUrl()).toBe('https://qa.example.test/platform')
    expect(window.localStorage.getItem(API_BASE_URL_STORAGE_KEY)).toBe('https://qa.example.test/platform')
  })

  it('uses the persisted endpoint for relative requests', async () => {
    setApiBaseUrl('https://uat.example.test')
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok' }), { status: 200 }),
    )

    await expect(getJson<{ status: string }>('/health')).resolves.toEqual({ status: 'ok' })
    expect(fetchMock).toHaveBeenCalledWith(
      'https://uat.example.test/health',
      expect.objectContaining({ method: 'GET', credentials: 'include' }),
    )
  })

  it('sends the session cookie and session-bound CSRF token to the configured API origin', async () => {
    setApiBaseUrl('https://api.example.test')
    document.cookie = 'norma_csrf=csrf-token-123; path=/'
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    )

    await expect(postJson('/api/auth/logout', {})).resolves.toEqual({ ok: true })

    const [, request] = fetchMock.mock.calls[0]
    expect(request?.credentials).toBe('include')
    expect(new Headers(request?.headers).get('X-CSRF-Token')).toBe('csrf-token-123')
  })

  it('does not send cookies or CSRF tokens to an unconfigured origin', async () => {
    setApiBaseUrl('https://api.example.test')
    document.cookie = 'norma_csrf=csrf-token-123; path=/'
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    )

    await getJson('https://other.example.test/data')

    const [, request] = fetchMock.mock.calls[0]
    expect(request?.credentials).toBe('omit')
    expect(new Headers(request?.headers).has('X-CSRF-Token')).toBe(false)
  })

  it('resets to the build-time default endpoint', () => {
    setApiBaseUrl('https://dev.example.test')
    resetApiBaseUrl()
    expect(getApiBaseUrl()).not.toBe('https://dev.example.test')
  })
})
