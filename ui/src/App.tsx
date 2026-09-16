import React, { useEffect, useState } from 'react'
import { Activity, FileText, CheckCircle2, ShieldAlert, Cpu } from 'lucide-react'

interface HealthStatus {
  status: string
  version: string
  timestamp: string
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

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
        <div className="flex items-center space-x-3">
          <Cpu className="h-7 w-7 text-indigo-400" />
          <h1 className="text-xl font-bold tracking-tight">Antinode Norma BDD Platform</h1>
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

      {/* Main Content */}
      <main className="flex-1 p-8 max-w-7xl w-full mx-auto space-y-8">
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 shadow-xl">
          <h2 className="text-lg font-semibold mb-2 flex items-center space-x-2">
            <CheckCircle2 className="h-5 w-5 text-indigo-400" />
            <span>Platform Scaffold Ready</span>
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            Welcome to the Antinode Norma BDD Platform Web UI dashboard. The frontend scaffold is powered by React 18, Vite, TypeScript, and Tailwind CSS.
          </p>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-800/30 border border-slate-800 rounded-lg p-5 hover:border-slate-700 transition">
            <div className="flex items-center space-x-3 mb-3">
              <FileText className="h-5 w-5 text-blue-400" />
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
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 px-6 py-4 text-center text-xs text-slate-500">
        Antinode Norma BDD Platform v0.1.0 &copy; 2026 Antinode Labs
      </footer>
    </div>
  )
}
