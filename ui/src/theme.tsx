import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

export type ThemeMode = 'system' | 'light' | 'dark'

interface ThemeContextValue {
  mode: ThemeMode
  setMode: (mode: ThemeMode) => void
  resolvedMode: Exclude<ThemeMode, 'system'>
}

const THEME_STORAGE_KEY = 'norma-ui-theme'
const ThemeContext = createContext<ThemeContextValue | undefined>(undefined)

function getInitialMode(): ThemeMode {
  const storedMode = window.localStorage.getItem(THEME_STORAGE_KEY)
  return storedMode === 'light' || storedMode === 'dark' || storedMode === 'system'
    ? storedMode
    : 'system'
}

function getSystemMode(): Exclude<ThemeMode, 'system'> {
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

function applyTheme(mode: Exclude<ThemeMode, 'system'>): void {
  document.documentElement.classList.toggle('light', mode === 'light')
  document.documentElement.classList.toggle('dark', mode === 'dark')
  document.documentElement.style.colorScheme = mode
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(getInitialMode)
  const [systemMode, setSystemMode] = useState<Exclude<ThemeMode, 'system'>>(getSystemMode)
  const resolvedMode = mode === 'system' ? systemMode : mode

  useEffect(() => {
    window.localStorage.setItem(THEME_STORAGE_KEY, mode)
    applyTheme(resolvedMode)
  }, [mode, resolvedMode])

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: light)')
    const handleChange = (event: MediaQueryListEvent) => {
      setSystemMode(event.matches ? 'light' : 'dark')
    }

    setSystemMode(mediaQuery.matches ? 'light' : 'dark')
    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  const value = useMemo(
    () => ({ mode, setMode, resolvedMode }),
    [mode, resolvedMode],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
