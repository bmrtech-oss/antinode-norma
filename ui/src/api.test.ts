import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  API_BASE_URL_STORAGE_KEY,
  getApiBaseUrl,
  getJson,
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
      expect.objectContaining({ method: 'GET' }),
    )
  })

  it('resets to the build-time default endpoint', () => {
    setApiBaseUrl('https://dev.example.test')
    resetApiBaseUrl()
    expect(getApiBaseUrl()).not.toBe('https://dev.example.test')
  })
})
