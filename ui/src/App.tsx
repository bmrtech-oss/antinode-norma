import { useCallback, useEffect, useState } from 'react'
import { Dashboard } from './components/Dashboard'
import FeatureReview from './components/FeatureReview'
import ApprovalQueue from './components/ApprovalQueue'
import TraceabilityView from './components/TraceabilityView'
import AuditTrailView from './components/AuditTrailView'
import Generation from './components/Generation'
import { AppShell, type AppTab } from './components/AppShell'
import { getApiBaseUrl, getJson, resetApiBaseUrl, setApiBaseUrl } from './lib/api'
import { AuthProvider } from './lib/AuthContext'
import { AuthGuard } from './components/AuthGuard'

interface HealthStatus {
  status: string
  version: string
  timestamp: string
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [activeTab, setActiveTab] = useState<AppTab>('dashboard')
  const [apiBaseUrl, setApiBaseUrlState] = useState(getApiBaseUrl)

  const tabPermissions: Record<AppTab, string | undefined> = {
    dashboard: 'feature:read',
    generation: 'feature:write',
    review: 'feature:read',
    approvals: 'approval:action',
    traceability: 'feature:read',
    audit: 'audit:read',
  }
  const checkHealth = useCallback(() => {
    setLoading(true)
    return getJson<HealthStatus>('/health')
      .then((data) => setHealth(data))
      .catch(() => setHealth(null))
      .finally(() => setLoading(false))
  }, [])

  const handleApiBaseUrlChange = useCallback((value: string | null) => {
    const nextUrl = value === null ? (resetApiBaseUrl(), getApiBaseUrl()) : setApiBaseUrl(value)
    setApiBaseUrlState(nextUrl)
    setHealth(null)
    void checkHealth()
  }, [checkHealth])

  useEffect(() => {
    void checkHealth()
  }, [checkHealth])

  return (
    <AuthProvider>
      <AppShell
        activeTab={activeTab}
        health={health}
        loading={loading}
        apiBaseUrl={apiBaseUrl}
        onApiBaseUrlChange={handleApiBaseUrlChange}
        onHealthCheck={checkHealth}
        onTabChange={setActiveTab}
      >
        <AuthGuard requiredPermission={tabPermissions[activeTab]}>
          <div key={apiBaseUrl}>
            <h1 className="sr-only">Antinode Norma BDD Platform</h1>
            <p className="sr-only">Traceability and Audit Log views are available from the primary navigation.</p>
            {activeTab === 'dashboard' ? (
              <Dashboard />
            ) : activeTab === 'generation' ? (
              <Generation />
            ) : activeTab === 'review' ? (
              <FeatureReview />
            ) : activeTab === 'approvals' ? (
              <ApprovalQueue />
            ) : activeTab === 'traceability' ? (
              <TraceabilityView />
            ) : (
              <AuditTrailView />
            )}
          </div>
        </AuthGuard>
      </AppShell>
    </AuthProvider>
  )
}
