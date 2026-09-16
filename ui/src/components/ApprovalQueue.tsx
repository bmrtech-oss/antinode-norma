import React, { useEffect, useState } from 'react'
import { ShieldCheck, CheckCircle2, XCircle, Clock, UserCheck, MessageSquare, Loader2 } from 'lucide-react'

interface ApprovalRequest {
  id: string
  feature_id: string
  gherkin_text: string
  status: 'PENDING' | 'APPROVED' | 'REJECTED'
  requested_by: string
  reviewer?: string
  reason?: string
  created_at: string
  updated_at: string
}

export default function ApprovalQueue() {
  const [requests, setRequests] = useState<ApprovalRequest[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [activeModal, setActiveTabModal] = useState<{ id: string; action: 'approve' | 'reject' } | null>(null)
  const [reviewer, setReviewer] = useState<string>('qa_lead')
  const [reason, setReason] = useState<string>('')
  const [processing, setProcessing] = useState<boolean>(false)

  const fetchRequests = () => {
    setLoading(true)
    fetch('/api/approvals')
      .then((res) => res.json())
      .then((data: ApprovalRequest[]) => {
        setRequests(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    fetchRequests()
  }, [])

  const handleAction = async () => {
    if (!activeModal) return
    setProcessing(true)

    const endpoint = `/api/approvals/${activeModal.id}/${activeModal.action}`
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reviewer, reason }),
      })
      if (res.ok) {
        setActiveTabModal(null)
        setReason('')
        fetchRequests()
      }
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex items-center justify-between border-b border-slate-700/60 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <ShieldCheck className="h-5 w-5 text-indigo-400" />
            <span>Governance Approval Queue</span>
          </h2>
          <p className="text-slate-400 text-xs mt-1">Review pending feature requests and enforce approval policy state transitions.</p>
        </div>
        <button
          onClick={fetchRequests}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition"
        >
          Refresh Queue
        </button>
      </div>

      {/* Requests List */}
      {loading ? (
        <div className="flex items-center justify-center py-16 text-slate-400">
          <Loader2 className="h-6 w-6 animate-spin mr-2 text-indigo-400" />
          <span>Loading approval queue...</span>
        </div>
      ) : requests.length === 0 ? (
        <div className="bg-slate-800/30 border border-slate-800 rounded-xl p-8 text-center text-slate-400 text-xs">
          No approval requests in the queue.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {requests.map((req) => (
            <div key={req.id} className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <span className="text-xs font-mono bg-indigo-900/40 text-indigo-300 border border-indigo-700/40 px-2 py-0.5 rounded">
                    {req.feature_id}
                  </span>
                  <div className="text-xs text-slate-400 flex items-center space-x-2 mt-1">
                    <span>Requested by: <strong className="text-slate-300">{req.requested_by}</strong></span>
                    <span>&bull;</span>
                    <span className="flex items-center"><Clock className="h-3 w-3 mr-1" /> {new Date(req.created_at).toLocaleString()}</span>
                  </div>
                </div>

                {/* Status Badges & Action Buttons */}
                <div className="flex items-center space-x-3">
                  {req.status === 'PENDING' ? (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setActiveTabModal({ id: req.id, action: 'approve' })}
                        className="px-3 py-1.5 bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/50 text-emerald-200 text-xs rounded-lg font-medium transition flex items-center"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Approve
                      </button>
                      <button
                        onClick={() => setActiveTabModal({ id: req.id, action: 'reject' })}
                        className="px-3 py-1.5 bg-rose-600/30 hover:bg-rose-600/50 border border-rose-500/50 text-rose-200 text-xs rounded-lg font-medium transition flex items-center"
                      >
                        <XCircle className="h-3.5 w-3.5 mr-1" /> Reject
                      </button>
                    </div>
                  ) : req.status === 'APPROVED' ? (
                    <span className="bg-emerald-900/40 border border-emerald-700/60 text-emerald-300 px-3 py-1 rounded-full text-xs font-semibold flex items-center">
                      <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> APPROVED
                    </span>
                  ) : (
                    <span className="bg-rose-900/40 border border-rose-700/60 text-rose-300 px-3 py-1 rounded-full text-xs font-semibold flex items-center">
                      <XCircle className="h-3.5 w-3.5 mr-1" /> REJECTED
                    </span>
                  )}
                </div>
              </div>

              {/* Gherkin Preview snippet if provided */}
              {req.gherkin_text && (
                <pre className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-32">
                  {req.gherkin_text}
                </pre>
              )}

              {/* Reviewer / Reason footer */}
              {req.reviewer && (
                <div className="text-xs bg-slate-900/50 border border-slate-800/80 p-2.5 rounded-lg flex items-center space-x-3 text-slate-300">
                  <UserCheck className="h-4 w-4 text-indigo-400 shrink-0" />
                  <div>
                    <span>Reviewed by <strong>{req.reviewer}</strong></span>
                    {req.reason && <span className="text-slate-400"> &mdash; "{req.reason}"</span>}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Action Modal */}
      {activeModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-md w-full space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <MessageSquare className="h-5 w-5 text-indigo-400" />
              <span>Confirm {activeModal.action === 'approve' ? 'Approval' : 'Rejection'}</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 mb-1 font-medium">Reviewer Name</label>
                <input
                  type="text"
                  value={reviewer}
                  onChange={(e) => setReviewer(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">Reason / Comments</label>
                <textarea
                  rows={3}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Enter reason for approval or rejection..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setActiveTabModal(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg font-medium transition"
              >
                Cancel
              </button>
              <button
                onClick={handleAction}
                disabled={processing}
                className={`px-4 py-2 text-white text-xs rounded-lg font-medium transition flex items-center ${
                  activeModal.action === 'approve' ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-rose-600 hover:bg-rose-500'
                }`}
              >
                {processing && <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />}
                Confirm {activeModal.action === 'approve' ? 'Approve' : 'Reject'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
