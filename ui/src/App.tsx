import { useCallback, useEffect, useState } from 'react'
import { Dashboard } from './components/Dashboard'
import FeatureReview from './components/FeatureReview'
import ApprovalQueue from './components/ApprovalQueue'
import TraceabilityView from './components/TraceabilityView'
import AuditTrailView from './components/AuditTrailView'
import { AppShell, type AppTab } from './components/AppShell'
import { getApiBaseUrl, getJson } from './lib/api'

interface HealthStatus {
  status: string
  version: string
  timestamp: string
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [activeTab, setActiveTab] = useState<AppTab>('dashboard')
  const checkHealth = useCallback(() => {
    setLoading(true)
    return getJson<HealthStatus>('/health')
      .then((data) => setHealth(data))
      .catch(() => setHealth(null))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    void checkHealth()
  }, [checkHealth])

  return (
    <AppShell
      activeTab={activeTab}
      health={health}
      loading={loading}
      apiBaseUrl={getApiBaseUrl()}
      onHealthCheck={checkHealth}
      onTabChange={setActiveTab}
    >
      {activeTab === 'dashboard' ? (
        <Dashboard />
      ) : activeTab === 'review' ? (
        <FeatureReview />
      ) : activeTab === 'approvals' ? (
        <ApprovalQueue />
      ) : activeTab === 'traceability' ? (
        <TraceabilityView />
      ) : (
        <AuditTrailView />
      )}
    </AppShell>
  )
}
