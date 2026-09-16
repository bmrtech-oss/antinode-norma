import React, { useEffect, useState } from 'react'
import { FileText, CheckCircle2, XCircle, ShieldCheck, ListChecks, Code, Loader2 } from 'lucide-react'

interface FeatureSummary {
  filename: string
  path: string
  scenario_count: number
  modified_at: string
}

interface FeatureDetail {
  filename: string
  path: string
  content: string
  scenarios: string[]
  gate_results?: {
    summary?: string
    hard_pass?: boolean
    soft_score?: number
    sem_score?: number
  }
}

export default function FeatureReview() {
  const [features, setFeatures] = useState<FeatureSummary[]>([])
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [detail, setDetail] = useState<FeatureDetail | null>(null)
  const [loadingList, setLoadingList] = useState<boolean>(true)
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false)

  useEffect(() => {
    fetch('/api/features')
      .then((res) => res.json())
      .then((data: FeatureSummary[]) => {
        setFeatures(data)
        setLoadingList(false)
        if (data.length > 0) {
          setSelectedFile(data[0].filename)
        }
      })
      .catch(() => setLoadingList(false))
  }, [])

  useEffect(() => {
    if (!selectedFile) return
    setLoadingDetail(true)
    fetch(`/api/features/${selectedFile}?run_gates=true`)
      .then((res) => res.json())
      .then((data: FeatureDetail) => {
        setDetail(data)
        setLoadingDetail(false)
      })
      .catch(() => setLoadingDetail(false))
  }, [selectedFile])

  return (
    <div className="flex flex-col md:flex-row gap-6 h-full">
      {/* Sidebar - Feature List */}
      <div className="w-full md:w-80 bg-slate-800/40 border border-slate-700/60 rounded-xl p-4 flex flex-col space-y-3">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
          <FileText className="h-4 w-4 text-indigo-400" />
          <span>Feature Files ({features.length})</span>
        </h3>

        {loadingList ? (
          <div className="flex items-center justify-center py-8 text-slate-400">
            <Loader2 className="h-5 w-5 animate-spin mr-2 text-indigo-400" />
            <span>Loading features...</span>
          </div>
        ) : features.length === 0 ? (
          <p className="text-slate-400 text-xs italic py-4">No .feature files found.</p>
        ) : (
          <div className="space-y-1 overflow-y-auto max-h-[600px] pr-1">
            {features.map((item) => (
              <button
                key={item.filename}
                onClick={() => setSelectedFile(item.filename)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-xs transition flex items-center justify-between ${
                  selectedFile === item.filename
                    ? 'bg-indigo-600/30 border border-indigo-500/50 text-indigo-200 font-medium'
                    : 'bg-slate-800/20 hover:bg-slate-800/60 text-slate-300 border border-transparent'
                }`}
              >
                <div className="truncate pr-2">
                  <p className="truncate font-mono">{item.filename}</p>
                </div>
                <span className="text-[10px] bg-slate-700/60 px-2 py-0.5 rounded-full text-slate-300">
                  {item.scenario_count} sc
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Main Feature Viewer & Review */}
      <div className="flex-1 bg-slate-800/40 border border-slate-700/60 rounded-xl p-6 flex flex-col space-y-6">
        {loadingDetail ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-400">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-400 mb-3" />
            <p className="text-sm">Evaluating Quality Gates & Loading Feature...</p>
          </div>
        ) : detail ? (
          <>
            {/* Header / Summary */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-700/50 gap-4">
              <div>
                <h2 className="text-lg font-bold text-slate-100 font-mono">{detail.filename}</h2>
                <p className="text-xs text-slate-400 font-mono mt-0.5">{detail.path}</p>
              </div>

              {/* Gate Results Badges */}
              {detail.gate_results && (
                <div className="flex items-center space-x-3 bg-slate-900/60 border border-slate-700/60 px-3 py-2 rounded-lg text-xs">
                  <ShieldCheck className="h-4 w-4 text-indigo-400" />
                  <div className="flex items-center space-x-2">
                    <span className="text-slate-400">Hard Gates:</span>
                    {detail.gate_results.hard_pass ? (
                      <span className="flex items-center text-emerald-400 font-semibold">
                        <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> PASS
                      </span>
                    ) : (
                      <span className="flex items-center text-rose-400 font-semibold">
                        <XCircle className="h-3.5 w-3.5 mr-1" /> FAIL
                      </span>
                    )}
                  </div>
                  {detail.gate_results.soft_score !== undefined && (
                    <div className="text-slate-300 border-l border-slate-700 pl-2">
                      Soft: <span className="text-indigo-300 font-mono">{(detail.gate_results.soft_score * 100).toFixed(0)}%</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Parsed Scenarios */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
                <ListChecks className="h-4 w-4 text-emerald-400" />
                <span>Scenarios ({detail.scenarios.length})</span>
              </h4>
              <div className="flex flex-wrap gap-2">
                {detail.scenarios.map((sc, idx) => (
                  <span key={idx} className="bg-slate-800 text-slate-200 text-xs px-2.5 py-1 rounded-md border border-slate-700/50">
                    {sc}
                  </span>
                ))}
              </div>
            </div>

            {/* Gherkin Source Content */}
            <div className="space-y-2 flex-1">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
                <Code className="h-4 w-4 text-blue-400" />
                <span>Gherkin Source Text</span>
              </h4>
              <pre className="bg-slate-950/80 border border-slate-800 rounded-lg p-4 font-mono text-xs text-slate-200 overflow-x-auto leading-relaxed max-h-[500px]">
                {detail.content}
              </pre>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center py-16 text-slate-400 italic text-sm">
            Select a feature file from the list to review.
          </div>
        )}
      </div>
    </div>
  )
}
