import { useEffect, useState } from 'react'

interface ApprovalRequest {
  id: string
  feature_id: string
  gherkin_text: string
  status: string
  requested_by: string
  reviewer?: string
  reason?: string
  created_at: string
}

export default function ApprovalQueue() {
  const [requests, setRequests] = useState<ApprovalRequest[]>([])
  const [loading, setLoading] = useState<boolean>(true)

  const fetchApprovals = () => {
    setLoading(true)
    fetch('/api/approvals')
      .then((res) => res.json())
      .then((data) => {
        setRequests(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    fetchApprovals()
  }, [])

  const handleApprove = (id: string) => {
    fetch(`/api/approvals/${id}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer: 'lead_reviewer', reason: 'Verified via UI' }),
    }).then(() => fetchApprovals())
  }

  const handleReject = (id: string) => {
    fetch(`/api/approvals/${id}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer: 'lead_reviewer', reason: 'Requires revision' }),
    }).then(() => fetchApprovals())
  }

  if (loading) {
    return <div className="p-8 text-center text-slate-400">Loading approval queue...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-slate-200">Governance Approval Queue</h2>
        <button
          onClick={fetchApprovals}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg border border-slate-700 transition"
        >
          Refresh Queue
        </button>
      </div>

      {requests.length === 0 ? (
        <div className="bg-slate-800/30 border border-slate-800 rounded-xl p-8 text-center text-slate-500">
          No approval requests in queue.
        </div>
      ) : (
        <div className="space-y-4">
          {requests.map((req) => (
            <div key={req.id} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5 space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-indigo-300">{req.feature_id}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">Requested by {req.requested_by} on {new Date(req.created_at).toLocaleString()}</p>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                  req.status === 'APPROVED'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : req.status === 'REJECTED'
                    ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                }`}>
                  {req.status}
                </span>
              </div>

              {req.status === 'PENDING' && (
                <div className="flex space-x-3 pt-2">
                  <button
                    onClick={() => handleApprove(req.id)}
                    className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium rounded-lg transition"
                  >
                    Approve Feature
                  </button>
                  <button
                    onClick={() => handleReject(req.id)}
                    className="px-4 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium rounded-lg transition"
                  >
                    Reject Feature
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
