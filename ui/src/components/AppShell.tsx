import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { Activity, Cpu, FileText, GitMerge, LayoutDashboard, Menu, PanelLeftClose, PanelLeftOpen, RefreshCw, Settings, ShieldCheck, X } from 'lucide-react'
import { ThemeSwitcher } from './ThemeSwitcher'
import { getApiBaseUrl, resetApiBaseUrl, setApiBaseUrl } from '../lib/api'
import { Button } from './ui/Button'
import { Tooltip } from './ui/Tooltip'

export type AppTab = 'dashboard' | 'review' | 'approvals' | 'traceability' | 'audit'

interface HealthStatus {
  version: string
}

interface AppShellProps {
  activeTab: AppTab
  health: HealthStatus | null
  loading: boolean
  apiBaseUrl: string
  onApiBaseUrlChange: (apiBaseUrl: string | null) => void
  onHealthCheck: () => Promise<void>
  onTabChange: (tab: AppTab) => void
  children: ReactNode
}

const navigationItems: Array<{
  id: AppTab
  label: string
  icon: typeof LayoutDashboard
}> = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'review', label: 'Feature Review', icon: FileText },
  { id: 'approvals', label: 'Approval Queue', icon: ShieldCheck },
  { id: 'traceability', label: 'Traceability', icon: GitMerge },
  { id: 'audit', label: 'Audit Log', icon: Activity },
]

const SIDEBAR_STORAGE_KEY = 'norma-ui-sidebar-collapsed'

export function AppShell({
  activeTab,
  health,
  loading,
  apiBaseUrl,
  onApiBaseUrlChange,
  onHealthCheck,
  onTabChange,
  children,
}: AppShellProps) {
  const mainRef = useRef<HTMLElement>(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    return window.localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true'
  })
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [apiUrlDraft, setApiUrlDraft] = useState(apiBaseUrl)
  const [apiUrlError, setApiUrlError] = useState<string | null>(null)
  const settingsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    mainRef.current?.focus()
    setMobileMenuOpen(false)
  }, [activeTab])

  useEffect(() => {
    window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(sidebarCollapsed))
  }, [sidebarCollapsed])

  useEffect(() => {
    setApiUrlDraft(apiBaseUrl)
  }, [apiBaseUrl])

  useEffect(() => {
    if (!settingsOpen) return
    const handlePointerDown = (event: PointerEvent) => {
      if (!settingsRef.current?.contains(event.target as Node)) setSettingsOpen(false)
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setSettingsOpen(false)
    }
    document.addEventListener('pointerdown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [settingsOpen])

  const selectTab = (tab: AppTab) => {
    onTabChange(tab)
    setMobileMenuOpen(false)
  }

  const saveApiUrl = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    try {
      const normalizedUrl = setApiBaseUrl(apiUrlDraft)
      onApiBaseUrlChange(normalizedUrl)
      setApiUrlError(null)
    } catch (error) {
      setApiUrlError(error instanceof Error ? error.message : 'Enter a valid API URL.')
    }
  }

  const resetApiUrl = () => {
    resetApiBaseUrl()
    const defaultUrl = getApiBaseUrl()
    setApiUrlDraft(defaultUrl)
    setApiUrlError(null)
    onApiBaseUrlChange(null)
  }

  const navigation = (collapsed: boolean) => (
    <nav
      className="flex flex-col gap-1"
      aria-label="Primary navigation"
      role="tablist"
      aria-orientation="vertical"
    >
      {navigationItems.map(({ id, label, icon: Icon }) => {
        const isActive = activeTab === id
        return (
          <Button
            key={id}
            variant={isActive ? 'default' : 'ghost'}
            size={collapsed ? 'icon' : 'default'}
            onClick={() => selectTab(id)}
            aria-current={isActive ? 'page' : undefined}
            aria-selected={isActive}
            aria-label={collapsed ? label : undefined}
            role="tab"
            title={collapsed ? label : undefined}
            className={collapsed ? 'mx-auto' : 'w-full !justify-start text-left'}
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            {!collapsed && <span>{label}</span>}
          </Button>
        )
      })}
    </nav>
  )

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <a
        href="#main-content"
        className="sr-only z-50 rounded-md bg-primary px-4 py-2 text-primary-foreground focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
      >
        Skip to main content
      </a>
      <aside
        className={`hidden shrink-0 flex-col border-r border-border bg-card p-4 transition-[width] duration-200 md:flex ${
          sidebarCollapsed ? 'w-20' : 'w-64'
        }`}
        aria-label="Sidebar navigation"
      >
        <Button
          variant="ghost"
          size={sidebarCollapsed ? 'icon' : 'default'}
          onClick={() => selectTab('dashboard')}
          aria-label="Go to dashboard"
          title="Go to dashboard"
          className={sidebarCollapsed ? 'mx-auto mb-8' : 'mb-8 w-full !justify-start text-left'}
        >
          <Cpu className="h-7 w-7 shrink-0 text-primary" aria-hidden="true" />
          {!sidebarCollapsed && <span className="text-lg font-bold tracking-tight">Antinode Norma</span>}
        </Button>
        {navigation(sidebarCollapsed)}
        <Button
          variant="ghost"
          size={sidebarCollapsed ? 'icon' : 'default'}
          onClick={() => setSidebarCollapsed((collapsed) => !collapsed)}
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className={sidebarCollapsed ? 'mx-auto mt-auto' : 'mt-auto w-full !justify-start text-left'}
        >
          {sidebarCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          {!sidebarCollapsed && <span>Collapse menu</span>}
        </Button>
      </aside>

      {mobileMenuOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/60"
            aria-label="Close navigation menu"
            onClick={() => setMobileMenuOpen(false)}
          />
          <aside id="mobile-navigation" className="relative flex h-full w-72 flex-col border-r border-border bg-card p-4 shadow-xl" aria-label="Mobile sidebar navigation">
            <div className="mb-8 flex items-center justify-between">
              <Button
                variant="ghost"
                onClick={() => selectTab('dashboard')}
                aria-label="Go to dashboard"
                className="!justify-start px-0 text-left"
              >
                <Cpu className="h-7 w-7 text-primary" aria-hidden="true" />
                <span className="text-lg font-bold tracking-tight">Antinode Norma</span>
              </Button>
              <Button variant="ghost" size="icon" aria-label="Close navigation menu" onClick={() => setMobileMenuOpen(false)}>
                <X className="h-5 w-5" />
              </Button>
            </div>
            {navigation(false)}
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-b border-border bg-card px-4 py-4 sm:px-6">
          <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4">
            <div className="flex min-w-0 items-center gap-3">
              <Button
                variant="outline"
                size="icon"
                className="md:hidden"
                aria-label="Open navigation menu"
                aria-expanded={mobileMenuOpen}
                aria-controls="mobile-navigation"
                onClick={() => setMobileMenuOpen(true)}
              >
                <Menu className="h-5 w-5" />
              </Button>
              <h1 className="truncate text-lg font-bold tracking-tight text-card-foreground sm:text-xl">
                Antinode Norma BDD Platform
              </h1>
            </div>

            <div className="flex shrink-0 items-center gap-3 text-sm">
              <div ref={settingsRef} className="relative">
                <Button
                  variant="outline"
                  size="icon"
                  aria-label="Open settings"
                  aria-expanded={settingsOpen}
                  aria-haspopup="menu"
                  onClick={() => setSettingsOpen((open) => !open)}
                >
                  <Settings className="h-4 w-4" />
                </Button>
                {settingsOpen && (
                  <div className="absolute right-0 top-12 z-30 w-56 rounded-lg border border-border bg-card p-3 shadow-lg" role="menu" aria-label="Settings">
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      <Tooltip content="Choose the interface color theme.">Appearance</Tooltip>
                    </p>
                    <ThemeSwitcher />
                    <form className="mt-4 border-t border-border pt-3" onSubmit={saveApiUrl}>
                      <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground" htmlFor="api-base-url">
                        <Tooltip content="Backend URL used by every UI API request.">API endpoint</Tooltip>
                      </label>
                      <input
                        id="api-base-url"
                        type="url"
                        value={apiUrlDraft}
                        onChange={(event) => setApiUrlDraft(event.target.value)}
                        className="mt-2 w-full rounded-md border border-input bg-background px-2 py-1.5 text-xs text-foreground outline-none ring-offset-background focus:ring-2 focus:ring-ring"
                        placeholder="https://api.example.com"
                        aria-describedby={apiUrlError ? 'api-url-error' : 'api-url-help'}
                      />
                      <p id="api-url-help" className="mt-1 text-[11px] text-muted-foreground">Used by all UI requests.</p>
                      {apiUrlError && <p id="api-url-error" className="mt-1 text-[11px] text-destructive">{apiUrlError}</p>}
                      <div className="mt-2 flex justify-end gap-2">
                        <Button type="button" size="sm" variant="ghost" onClick={resetApiUrl}>Reset</Button>
                        <Button type="submit" size="sm">Save</Button>
                      </div>
                    </form>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        <main
          ref={mainRef}
          id="main-content"
          tabIndex={-1}
          className="mx-auto w-full flex-1 space-y-8 p-4 outline-none sm:p-8"
          aria-busy={loading}
        >
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>

        <div
          className="border-t border-border bg-muted/40 px-4 py-2 text-xs text-muted-foreground sm:px-6"
          role="status"
          aria-live="polite"
          aria-busy={loading}
        >
          <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-2">
            <div className="flex min-w-0 items-center gap-2">
              <Activity className={health ? 'h-4 w-4 text-success' : 'h-4 w-4 text-destructive'} aria-hidden="true" />
              <span className="font-medium text-foreground">API:</span>
              {loading ? (
                <span>Checking connection...</span>
              ) : health ? (
                <span className="font-medium text-success">Online{health.version ? ` (v${health.version})` : ''}</span>
              ) : (
                <span className="font-medium text-destructive">Offline</span>
              )}
              <span className="hidden text-muted-foreground sm:inline">·</span>
              <span className="max-w-[14rem] truncate" title={apiBaseUrl}>URL: {apiBaseUrl}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 shrink-0"
                onClick={() => void onHealthCheck()}
                disabled={loading}
                aria-label={health ? 'Refresh API status' : 'Retry API connection'}
                title={loading ? 'Checking API connection' : health ? 'Refresh API status' : 'Retry API connection'}
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
              </Button>
            </div>
            <div className="flex flex-wrap items-center justify-end gap-2">
              <span className="hidden text-muted-foreground lg:inline">
                Antinode Norma BDD Platform v0.1.0 &copy; 2026 Antinode Labs
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
