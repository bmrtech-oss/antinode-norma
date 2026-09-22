import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { EmptyState, ErrorState, LoadingState } from './AsyncState'

describe('async states', () => {
  it('announces loading content', () => {
    render(<LoadingState label="Loading approvals..." />)
    expect(screen.getByRole('status')).toHaveTextContent('Loading approvals...')
  })

  it('renders an empty state with explanatory text', () => {
    render(<EmptyState title="No approvals" description="Nothing needs review." />)
    expect(screen.getByRole('heading', { name: 'No approvals' })).toBeVisible()
    expect(screen.getByText('Nothing needs review.')).toBeVisible()
  })

  it('supports retry from an error state', async () => {
    const user = userEvent.setup()
    const retry = vi.fn()
    render(<ErrorState message="Request failed" onRetry={retry} />)

    await user.click(screen.getByRole('button', { name: 'Retry' }))
    expect(retry).toHaveBeenCalledOnce()
    expect(screen.getByRole('alert')).toHaveTextContent('Request failed')
  })
})
