import { Monitor, Moon, Sun } from 'lucide-react'
import { useTheme, type ThemeMode } from '../theme'
import { Button } from './ui/Button'

const modes: ThemeMode[] = ['system', 'light', 'dark']

const modeLabels: Record<ThemeMode, string> = {
  system: 'System theme',
  light: 'Light theme',
  dark: 'Dark theme',
}

const modeIcons: Record<ThemeMode, typeof Monitor> = {
  system: Monitor,
  light: Sun,
  dark: Moon,
}

export function ThemeSwitcher() {
  const { mode, setMode } = useTheme()
  const Icon = modeIcons[mode]
  const nextMode = modes[(modes.indexOf(mode) + 1) % modes.length]

  return (
    <Button
      size="sm"
      variant="outline"
      onClick={() => setMode(nextMode)}
      aria-label={`Theme: ${modeLabels[mode]}. Switch to ${modeLabels[nextMode]}`}
      title={`Switch to ${modeLabels[nextMode]}`}
    >
      <Icon className="h-4 w-4" aria-hidden="true" />
      <span className="hidden sm:inline">{modeLabels[mode]}</span>
    </Button>
  )
}
