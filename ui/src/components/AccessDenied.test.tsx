import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AccessDenied } from './AccessDenied'

describe('AccessDenied Component', () => {
  it('renders 403 access denied message and permission badge', () => {
    render(
      <AccessDenied
        message="Insufficient permissions for write action"
        requiredPermission="feature:write"
      />,
    )

    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText('Access Denied (403 Forbidden)')).toBeInTheDocument()
    expect(screen.getByText('Insufficient permissions for write action')).toBeInTheDocument()
    expect(screen.getByText('Required Permission: feature:write')).toBeInTheDocument()
  })

  it('triggers onBack callback when Return button is clicked', () => {
    const handleBack = vi.fn()
    render(<AccessDenied onBack={handleBack} />)

    fireEvent.click(screen.getByText('Return'))
    expect(handleBack).toHaveBeenCalledTimes(1)
  })
})
