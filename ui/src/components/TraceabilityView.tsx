import React, { useEffect, useState } from 'react'
import { GitMerge, CheckCircle2, Tag, Loader2, AlertTriangle } from 'lucide-react'

interface TraceableItem {
  requirement_id: string
  requirement_title: string
  scenario_title: string
  tags: string[]
  status: string
}

interface TraceabilityMatrix {
  feature_title: string
  items: TraceableItem[]
  uncovered_requirements: string[]
  metadata: Record<string, any>
}

export default function TraceabilityView() {
  const [matrix, setMatrix] = useState<TraceabilityMatrix | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    fetch('/api/traceability')
      .then((res) => res.json())
      .then((data: TraceabilityMatrix) => {
        setMatrix(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-700/60 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <GitMerge className="h-5 w-5 text-indigo-400" />
            <span>Requirement-to-Scenario Traceability Matrix</span>
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Map generated Gherkin test scenarios back to input requirement IDs and tags.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-slate-400">
          <Loader2 className="h-6 w-6 animate-spin mr-2 text-indigo-400" />
          <span>Building traceability matrix...</span>
        </div>
      ) : !matrix || matrix.items.length === 0 ? (
        <div className="bg-slate-800/30 border border-slate-800 rounded-xl p-8 text-center text-slate-400 text-xs">
          No feature scenarios or requirement mappings found.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Table */}
          <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl overflow-hidden shadow-xl">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/80 border-b border-slate-700/60 text-slate-400 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Requirement ID</th>
                  <th className="px-4 py-3">Requirement / Case Title</th>
                  <th className="px-4 py-3">Covered Scenario</th>
                  <th className="px-4 py-3">Tags</th>
                  <th className="px-4 py-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {matrix.items.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3 font-mono text-indigo-300 font-semibold">{item.requirement_id}</td>
                    <td className="px-4 py-3 text-slate-200">{item.requirement_title}</td>
                    <td className="px-4 py-3 font-mono text-slate-300">{item.scenario_title}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {item.tags.length > 0 ? (
                          item.tags.map((t, i) => (
                            <span key={i} className="bg-slate-900 border border-slate-700 px-1.5 py-0.5 rounded font-mono text-[10px] text-slate-400 flex items-center">
                              <Tag className="h-2.5 w-2.5 mr-1 text-slate-500" /> {t}
                            </span>
                          ))
                        ) : (
                          <span className="text-slate-500 italic">-</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="bg-emerald-900/40 border border-emerald-700/60 text-emerald-300 px-2.5 py-0.5 rounded-full font-semibold text-[10px] inline-flex items-center">
                        <CheckCircle2 className="h-3 w-3 mr-1" /> {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Uncovered Requirements Warnings */}
          {matrix.uncovered_requirements.length > 0 && (
            <div className="bg-amber-900/20 border border-amber-700/50 rounded-xl p-4 space-y-2">
              <h4 className="text-xs font-semibold text-amber-300 flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4" />
                <span>Uncovered Requirements ({matrix.uncovered_requirements.length})</span>
              </h4>
              <ul className="list-disc list-inside text-xs text-amber-200/80 space-y-1">
                {matrix.uncovered_requirements.map((unreq, i) => (
                  <li key={i}>{unreq}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
