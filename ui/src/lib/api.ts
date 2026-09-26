export interface ApiErrorOptions {
  status: number
  statusText: string
  detail: string
  code?: string
}

export const API_BASE_URL_STORAGE_KEY = 'norma-ui-api-base-url'
export const UNAUTHORIZED_EVENT = 'norma:unauthorized'
export const FORBIDDEN_EVENT = 'norma:forbidden'
const CSRF_COOKIE_NAME = 'norma_csrf'
const CSRF_HEADER_NAME = 'X-CSRF-Token'
const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

function normalizeApiBaseUrl(value: string): string {
  const trimmedValue = value.trim()
  if (!trimmedValue) {
    throw new Error('API URL is required.')
  }
  const url = new URL(trimmedValue, window.location.origin)
  if (url.protocol !== 'http:' && url.protocol !== 'https:') {
    throw new Error('API URL must use http or https.')
  }
  return `${url.origin}${url.pathname}`.replace(/\/$/, '')
}

export function getApiBaseUrl(): string {
  const storedUrl = window.localStorage.getItem(API_BASE_URL_STORAGE_KEY)
  if (storedUrl) {
    try {
      return normalizeApiBaseUrl(storedUrl)
    } catch {
      window.localStorage.removeItem(API_BASE_URL_STORAGE_KEY)
    }
  }

  const configuredUrl = import.meta.env.VITE_API_BASE_URL
  if (configuredUrl) {
    try {
      return normalizeApiBaseUrl(configuredUrl)
    } catch {
      return configuredUrl.replace(/[?#].*$/, '').replace(/\/$/, '')
    }
  }
  return import.meta.env.DEV ? 'http://localhost:8000' : window.location.origin
}

export function setApiBaseUrl(value: string): string {
  const normalizedUrl = normalizeApiBaseUrl(value)
  window.localStorage.setItem(API_BASE_URL_STORAGE_KEY, normalizedUrl)
  return normalizedUrl
}

export function resetApiBaseUrl(): void {
  window.localStorage.removeItem(API_BASE_URL_STORAGE_KEY)
}

function resolveRequestUrl(input: RequestInfo | URL): string {
  const inputUrl = typeof input === 'string'
    ? input
    : input instanceof URL
      ? input.toString()
      : input.url
  return inputUrl.startsWith('/') ? `${getApiBaseUrl()}${inputUrl}` : inputUrl
}

function isConfiguredApiOrigin(requestUrl: string): boolean {
  try {
    return new URL(requestUrl, window.location.origin).origin
      === new URL(getApiBaseUrl(), window.location.origin).origin
  } catch {
    return false
  }
}

function getCookie(name: string): string | null {
  const prefix = `${name}=`
  const cookie = document.cookie.split(';').map((part) => part.trim()).find((part) => part.startsWith(prefix))
  if (!cookie) return null
  try {
    return decodeURIComponent(cookie.slice(prefix.length))
  } catch {
    return cookie.slice(prefix.length)
  }
}

export class ApiError extends Error {
  readonly status: number
  readonly statusText: string
  readonly code?: string

  constructor({ status, statusText, detail, code }: ApiErrorOptions) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.statusText = statusText
    this.code = code
  }
}

interface ApiErrorPayload {
  detail?: string
  error_code?: string
}

async function parseError(response: Response, requestUrl?: string): Promise<ApiError> {
  let payload: ApiErrorPayload = {}
  try {
    payload = (await response.json()) as ApiErrorPayload
  } catch {
    // Non-JSON responses still become a typed ApiError below.
  }

  const error = new ApiError({
    status: response.status,
    statusText: response.statusText,
    detail: payload.detail || `Request failed with status ${response.status}`,
    code: payload.error_code,
  })

  if (typeof window !== 'undefined') {
    if (response.status === 401 && !requestUrl?.includes('/api/auth/me')) {
      window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT, { detail: error }))
    } else if (response.status === 403) {
      window.dispatchEvent(new CustomEvent(FORBIDDEN_EVENT, { detail: error }))
    }
  }

  return error
}

export async function requestJson<T>(
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<T> {
  const requestUrl = resolveRequestUrl(input)
  const sendsCredentials = isConfiguredApiOrigin(requestUrl)
  const method = (init.method || 'GET').toUpperCase()
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (sendsCredentials && UNSAFE_METHODS.has(method)) {
    const csrfToken = getCookie(CSRF_COOKIE_NAME)
    if (csrfToken) headers.set(CSRF_HEADER_NAME, csrfToken)
  }
  const response = await fetch(requestUrl, {
    ...init,
    credentials: sendsCredentials ? 'include' : 'omit',
    headers,
  })

  if (!response.ok) {
    throw await parseError(response, requestUrl)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export function getJson<T>(input: RequestInfo | URL, signal?: AbortSignal): Promise<T> {
  return requestJson<T>(input, { method: 'GET', signal })
}

export function postJson<TResponse, TBody>(
  input: RequestInfo | URL,
  body: TBody,
  signal?: AbortSignal,
): Promise<TResponse> {
  return requestJson<TResponse>(input, {
    method: 'POST',
    signal,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function postForm<TResponse>(
  input: RequestInfo | URL,
  formData: FormData,
  signal?: AbortSignal,
): Promise<TResponse> {
  return requestJson<TResponse>(input, { method: 'POST', signal, body: formData })
}

export async function getBlob(input: RequestInfo | URL): Promise<Blob> {
  const requestUrl = resolveRequestUrl(input)
  const response = await fetch(requestUrl, {
    method: 'GET',
    credentials: isConfiguredApiOrigin(requestUrl) ? 'include' : 'omit',
    headers: { Accept: 'application/zip' },
  })
  if (!response.ok) {
    throw await parseError(response, requestUrl)
  }
  return response.blob()
}
