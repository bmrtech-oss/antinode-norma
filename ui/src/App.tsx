import { useEffect, useState } from 'react'
import { Activity, FileText, Cpu, LayoutDashboard, ShieldCheck, GitMerge } from 'lucide-react'
import { Dashboard } from './components/Dashboard'
import FeatureReview from './components/FeatureReview'
import ApprovalQueue from './components/ApprovalQueue'
import TraceabilityView from './components/TraceabilityView'
import AuditTrailView from './components/AuditTrailView'

interface HealthStatus {
  status: string
  version: string
  timestamp: string
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [activeTab, setActiveTab] = useState<'dashboard' | 'review' | 'approvals' | 'traceability' | 'audit'>('dashboard')

  useEffect(() => {
    fetch('/health')
      .then((res) => res.json())
      .then((data) => {
        setHealth(data)
        setLoading(false)
      })
      .catch(() => {
        setHealth(null)
        setLoading(false)
      })
  }, [])

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-3">
            <Cpu className="h-7 w-7 text-indigo-400" />
            <h1 className="text-xl font-bold tracking-tight">Antinode Norma BDD Platform</h1>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-2 bg-slate-900/80 border border-slate-800 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center space-x-1.5 ${
                activeTab === 'dashboard'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <LayoutDashboard className="h-3.5 w-3.5" />
              <span>Dashboard</span>
            </button>
            <button
              onClick={() => setActiveTab('review')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center space-x-1.5 ${
                activeTab === 'review'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              <span>Feature Review</span>
            </button>
            <button
              onClick={() => setActiveTab('approvals')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center space-x-1.5 ${
                activeTab === 'approvals'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Approval Queue</span>
            </button>
            <button
              onClick={() => setActiveTab('traceability')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center space-x-1.5 ${
                activeTab === 'traceability'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <GitMerge className="h-3.5 w-3.5" />
              <span>Traceability</span>
            </button>
            <button
              onClick={() => setActiveTab('audit')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center space-x-1.5 ${
                activeTab === 'audit'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Activity className="h-3.5 w-3.5" />
              <span>Audit Log</span>
            </button>
          </nav>
        </div>

        <div className="flex items-center space-x-2 text-sm">
          <Activity className="h-4 w-4 text-emerald-400" />
          <span>API Status: </span>
          {loading ? (
            <span className="text-slate-400">Connecting...</span>
          ) : health ? (
            <span className="text-emerald-400 font-medium">Online (v{health.version})</span>
          ) : (
            <span className="text-rose-400 font-medium">Offline</span>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-8 max-w-7xl w-full mx-auto space-y-8">
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
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 px-6 py-4 text-center text-xs text-slate-500">
        Antinode Norma BDD Platform v0.1.0 &copy; 2026 Antinode Labs
      </footer>
    </div>
  )
}
