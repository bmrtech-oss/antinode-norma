export function validateLocalReturnPath(input?: string | null, fallback: string = '/'): string {
  if (!input) return fallback
  const trimmed = input.trim()
  if (!trimmed || trimmed.length > 2048) return fallback
  // Reject backslashes or unprintable control characters
  if (trimmed.includes('\\')) return fallback
  for (let i = 0; i < trimmed.length; i++) {
    const code = trimmed.charCodeAt(i)
    if (code < 32 || code === 127) return fallback
  }
  // Reject protocol-relative URLs or absolute URLs with scheme
  if (trimmed.startsWith('//') || /^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(trimmed)) {
    return fallback
  }
  // Require leading single slash
  if (!trimmed.startsWith('/')) return fallback
  // Avoid loops back to authentication pages or callback endpoints
  const lower = trimmed.toLowerCase()
  if (lower.startsWith('/login') || lower.startsWith('/api/auth')) {
    return fallback
  }
  return trimmed
}
