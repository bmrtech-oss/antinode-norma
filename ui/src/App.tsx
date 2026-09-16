import React, { useEffect, useState } from 'react'
import { Activity, FileText, CheckCircle2, ShieldAlert, Cpu, LayoutDashboard } from 'lucide-react'
import FeatureReview from './components/FeatureReview'

interface HealthStatus {
  status: string
  version: string
  timestamp: string
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [activeTab, setActiveTab] = useState<'dashboard' | 'review'>('dashboard')

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
          <>
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 shadow-xl">
              <h2 className="text-lg font-semibold mb-2 flex items-center space-x-2">
                <CheckCircle2 className="h-5 w-5 text-indigo-400" />
                <span>Platform Dashboard</span>
              </h2>
              <p className="text-slate-300 text-sm leading-relaxed">
                Welcome to the Antinode Norma BDD Platform Web UI dashboard. Switch to the <strong className="text-indigo-300">Feature Review</strong> tab to inspect generated Gherkin feature files, scenario counts, and Quality Gate metrics.
              </p>
            </div>

            {/* Feature Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div
                onClick={() => setActiveTab('review')}
                className="bg-slate-800/30 border border-slate-800 rounded-lg p-5 hover:border-indigo-500/50 transition cursor-pointer group"
              >
                <div className="flex items-center space-x-3 mb-3">
                  <FileText className="h-5 w-5 text-blue-400 group-hover:text-indigo-400 transition" />
                  <h3 className="font-medium text-slate-200">Feature Viewer</h3>
                </div>
                <p className="text-slate-400 text-xs">Browse and inspect generated Gherkin feature files and scenario structures.</p>
              </div>

              <div className="bg-slate-800/30 border border-slate-800 rounded-lg p-5 hover:border-slate-700 transition">
                <div className="flex items-center space-x-3 mb-3">
                  <ShieldAlert className="h-5 w-5 text-amber-400" />
                  <h3 className="font-medium text-slate-200">Quality Gates</h3>
                </div>
                <p className="text-slate-400 text-xs">Evaluate hard (Q0–Q5) and soft (Q6–Q10) INVEST quality gates and verdicts.</p>
              </div>

              <div className="bg-slate-800/30 border border-slate-800 rounded-lg p-5 hover:border-slate-700 transition">
                <div className="flex items-center space-x-3 mb-3">
                  <Activity className="h-5 w-5 text-emerald-400" />
                  <h3 className="font-medium text-slate-200">Execution Maturity</h3>
                </div>
                <p className="text-slate-400 text-xs">Monitor parallel test runs, flake detection, and artifact captures.</p>
              </div>
            </div>
          </>
        ) : (
          <FeatureReview />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 px-6 py-4 text-center text-xs text-slate-500">
        Antinode Norma BDD Platform v0.1.0 &copy; 2026 Antinode Labs
      </footer>
    </div>
  )
}
