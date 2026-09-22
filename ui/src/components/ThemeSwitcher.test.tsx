import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, beforeEach } from 'vitest'
import { ThemeSwitcher } from './ThemeSwitcher'
import { ThemeProvider } from '../theme'

describe('ThemeSwitcher', () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.className = ''
  })

  it('cycles theme modes and persists the selected mode', async () => {
    const user = userEvent.setup()
    render(
      <ThemeProvider>
        <ThemeSwitcher />
      </ThemeProvider>,
    )

    const switcher = screen.getByRole('button', { name: /theme: system theme/i })
    await user.click(switcher)
    expect(window.localStorage.getItem('norma-ui-theme')).toBe('light')
    expect(document.documentElement).toHaveClass('light')
    expect(switcher).toHaveAccessibleName(/theme: light theme/i)
  })
})
