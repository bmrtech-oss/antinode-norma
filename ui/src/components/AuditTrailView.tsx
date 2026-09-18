import React, { useEffect, useState } from 'react'
import { FileText, ShieldCheck, ShieldAlert, KeyRound, Loader2, User } from 'lucide-react'

interface AuditRecord {
  id: string
  timestamp: string
  action: string
  resource: string
  actor: string
  payload: Record<string, any>
  previous_hash: string
  content_hash: string
}

interface IntegrityInfo {
  is_valid: boolean
  record_count: number
}

export default function AuditTrailView() {
  const [records, setRecords] = useState<AuditRecord[]>([])
  const [integrity, setIntegrity] = useState<IntegrityInfo | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    Promise.all([
      fetch('/api/audit').then((r) => r.json()),
      fetch('/api/audit/verify').then((r) => r.json()),
    ])
      .then(([auditData, verifyData]) => {
        setRecords(auditData)
        setIntegrity(verifyData)
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
            <FileText className="h-5 w-5 text-indigo-400" />
            <span>Immutable Audit Trail</span>
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Cryptographically chained SHA-256 event stream logging all governance and execution actions.
          </p>
        </div>

        {/* Verification Status Badge */}
        {integrity && (
          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-700 px-3 py-1.5 rounded-lg text-xs">
            <KeyRound className="h-4 w-4 text-indigo-400" />
            <span className="text-slate-400">Chain Integrity:</span>
            {integrity.is_valid ? (
              <span className="text-emerald-400 font-semibold flex items-center">
                <ShieldCheck className="h-4 w-4 mr-1 text-emerald-400" /> VERIFIED
              </span>
            ) : (
              <span className="text-rose-400 font-semibold flex items-center">
                <ShieldAlert className="h-4 w-4 mr-1 text-rose-400" /> TAMPERED
              </span>
            )}
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-slate-400">
          <Loader2 className="h-6 w-6 animate-spin mr-2 text-indigo-400" />
          <span>Loading audit log...</span>
        </div>
      ) : records.length === 0 ? (
        <div className="bg-slate-800/30 border border-slate-800 rounded-xl p-8 text-center text-slate-400 text-xs">
          No audit log events recorded yet.
        </div>
      ) : (
        <div className="space-y-3">
          {records.map((rec) => (
            <div key={rec.id} className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-4 text-xs space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="bg-indigo-900/40 border border-indigo-700/50 text-indigo-300 px-2 py-0.5 rounded font-mono font-semibold">
                    {rec.action}
                  </span>
                  <span className="text-slate-300 font-medium">{rec.resource}</span>
                </div>
                <span className="text-slate-400 font-mono text-[11px]">
                  {new Date(rec.timestamp).toLocaleString()}
                </span>
              </div>

              <div className="flex items-center justify-between text-slate-400 pt-1 border-t border-slate-800">
                <div className="flex items-center space-x-1.5 text-slate-300">
                  <User className="h-3.5 w-3.5 text-slate-400" />
                  <span>Actor: <strong>{rec.actor}</strong></span>
                </div>
                <div className="font-mono text-[10px] text-slate-500 truncate max-w-md">
                  Hash: {rec.content_hash}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
