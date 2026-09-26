import { describe, expect, it } from 'vitest'
import { validateLocalReturnPath } from './returnPath'

describe('validateLocalReturnPath', () => {
  it('allows valid local deep links', () => {
    expect(validateLocalReturnPath('/approvals?filter=pending')).toBe('/approvals?filter=pending')
    expect(validateLocalReturnPath('/dashboard')).toBe('/dashboard')
    expect(validateLocalReturnPath('/')).toBe('/')
  })

  it('returns default fallback for null, undefined, or empty strings', () => {
    expect(validateLocalReturnPath(null)).toBe('/')
    expect(validateLocalReturnPath(undefined)).toBe('/')
    expect(validateLocalReturnPath('')).toBe('/')
    expect(validateLocalReturnPath('   ')).toBe('/')
  })

  it('rejects external absolute URLs (open redirect prevention)', () => {
    expect(validateLocalReturnPath('https://attacker.example.test/steal')).toBe('/')
    expect(validateLocalReturnPath('http://attacker.example.test')).toBe('/')
  })

  it('rejects protocol-relative URLs', () => {
    expect(validateLocalReturnPath('//attacker.example.test/phish')).toBe('/')
  })

  it('rejects URI schemes like javascript: or data:', () => {
    expect(validateLocalReturnPath('javascript:alert(1)')).toBe('/')
    expect(validateLocalReturnPath('data:text/html,hack')).toBe('/')
  })

  it('rejects control characters and backslashes', () => {
    expect(validateLocalReturnPath('/path\\with\\backslash')).toBe('/')
    expect(validateLocalReturnPath('/path\nwith\nnewline')).toBe('/')
  })

  it('rejects auth redirect loops', () => {
    expect(validateLocalReturnPath('/login')).toBe('/')
    expect(validateLocalReturnPath('/api/auth/oidc/login')).toBe('/')
    expect(validateLocalReturnPath('/api/auth/oidc/callback')).toBe('/')
  })

  it('uses custom fallback when supplied', () => {
    expect(validateLocalReturnPath('https://external.test', '/dashboard')).toBe('/dashboard')
  })
})
