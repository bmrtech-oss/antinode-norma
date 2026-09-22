import { useEffect, useMemo, useState } from 'react'
import { AlertCircle, CheckCircle2, Loader2, ShieldCheck, XCircle } from 'lucide-react'
import { getJson, postJson } from '../lib/api'
import { EmptyState, ErrorState, LoadingState } from './ui/AsyncState'
import { Alert } from './ui/Alert'
import { Button } from './ui/Button'
import { Tooltip } from './ui/Tooltip'
import { ConfirmationDialog } from './ui/ConfirmationDialog'

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
  const [error, setError] = useState<string | null>(null)
  const [mutation, setMutation] = useState<{ id: string; action: 'approve' | 'reject' } | null>(null)
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [pendingAction, setPendingAction] = useState<{ request: ApprovalRequest; action: 'approve' | 'reject' } | null>(null)

  const fetchApprovals = () => {
    setLoading(true)
    setError(null)
    getJson<ApprovalRequest[]>('/api/approvals')
      .then((data) => {
        setRequests(data)
        setLoading(false)
      })
      .catch(() => setError('The approval queue is unavailable.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchApprovals()
  }, [])

  const executeAction = (request: ApprovalRequest, action: 'approve' | 'reject') => {
    const label = action === 'approve' ? 'approve' : 'reject'
    const reason = action === 'approve' ? 'Verified via UI' : 'Requires revision'
    setPendingAction(null)
    setMutation({ id: request.id, action })
    setFeedback(null)
    postJson<ApprovalRequest, { reviewer: string; reason: string }>(
      `/api/approvals/${request.id}/${action}`,
      { reviewer: 'lead_reviewer', reason },
    )
      .then(() => {
        setFeedback({
          type: 'success',
          message: `${request.feature_id} was ${action === 'approve' ? 'approved' : 'rejected'}.`,
        })
        return fetchApprovals()
      })
      .catch(() => {
        setFeedback({
          type: 'error',
          message: `Could not ${label} ${request.feature_id}. No change was applied.`,
        })
      })
      .finally(() => setMutation(null))
  }

  const statuses = useMemo(
    () => ['all', ...Array.from(new Set(requests.map((request) => request.status))).sort()],
    [requests],
  )
  const visibleRequests = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    return requests.filter((request) => {
      const matchesStatus = statusFilter === 'all' || request.status === statusFilter
      const searchable = `${request.feature_id} ${request.requested_by} ${request.reviewer || ''}`.toLowerCase()
      return matchesStatus && (!normalizedQuery || searchable.includes(normalizedQuery))
    })
  }, [query, requests, statusFilter])

  if (loading) {
    return <LoadingState label="Loading approval queue..." />
  }

  return (
    <>
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <ShieldCheck className="h-5 w-5 text-primary" aria-hidden="true" />
          <Tooltip content="Review, approve, or reject generated features awaiting governance sign-off.">
            <span>Governance Approval Queue</span>
          </Tooltip>
        </h2>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={fetchApprovals}
        >
          Refresh Queue
        </Button>
      </div>

      {feedback && (
        <Alert variant={feedback.type === 'success' ? 'success' : 'destructive'}>
          <div className="flex items-center gap-2">
            {feedback.type === 'success' && <CheckCircle2 className="h-4 w-4" aria-hidden="true" />}
            <span>{feedback.message}</span>
          </div>
        </Alert>
      )}

      {error ? (
        <ErrorState message={error} onRetry={fetchApprovals} />
      ) : requests.length === 0 ? (
        <EmptyState title="Approval queue is clear" description="New feature approval requests will appear here." />
      ) : (
        <>
        <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-card p-4">
          <label className="min-w-56 flex-1 text-xs font-medium text-muted-foreground">
            <Tooltip content="Search by feature, requester, or reviewer.">Search requests</Tooltip>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Feature, requester, or reviewer" className="mt-1 block h-9 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground" />
          </label>
          <label className="text-xs font-medium text-muted-foreground">
            <Tooltip content="Filter approval requests by workflow status.">Status</Tooltip>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="mt-1 block h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground">
              {statuses.map((status) => <option key={status} value={status}>{status === 'all' ? 'All statuses' : status}</option>)}
            </select>
          </label>
          <span className="pb-2 text-xs text-muted-foreground" aria-live="polite">{visibleRequests.length} of {requests.length} requests</span>
        </div>
        {visibleRequests.length === 0 ? (
          <EmptyState title="No matching requests" description="Try a different search term or status filter." />
        ) : (
        <div className="space-y-4" aria-label="Approval requests">
          {visibleRequests.map((req) => (
            <div key={req.id} className="space-y-3 rounded-xl border border-border bg-card p-5">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-primary">{req.feature_id}</h3>
                  <p className="mt-0.5 text-xs text-muted-foreground">Requested by {req.requested_by} on {new Date(req.created_at).toLocaleString()}</p>
                </div>
                <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${
                  req.status === 'APPROVED'
                    ? 'border-success/30 bg-success/10 text-success'
                    : req.status === 'REJECTED'
                    ? 'border-destructive/30 bg-destructive/10 text-destructive'
                    : 'border-warning/30 bg-warning/10 text-warning'
                }`}>
                  {req.status === 'APPROVED' ? <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" /> : req.status === 'REJECTED' ? <XCircle className="h-3.5 w-3.5" aria-hidden="true" /> : <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />}
                  <span>{req.status}</span>
                </span>
              </div>

              {req.status === 'PENDING' && (
                <div className="flex space-x-3 pt-2">
                  <Button
                    variant="default"
                    size="sm"
                    disabled={mutation !== null}
                    onClick={() => setPendingAction({ request: req, action: 'approve' })}
                  >
                    {mutation?.id === req.id && mutation.action === 'approve' && (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                    )}
                    Approve Feature
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    disabled={mutation !== null}
                    onClick={() => setPendingAction({ request: req, action: 'reject' })}
                  >
                    {mutation?.id === req.id && mutation.action === 'reject' && (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                    )}
                    Reject Feature
                  </Button>
                </div>
              )}
              {req.status !== 'PENDING' && (
                <div className="border-t border-border pt-3 text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">Action history:</span>{' '}
                  {req.reviewer || 'Unknown reviewer'} {req.status.toLowerCase()} this request
                  {req.reason ? ` — ${req.reason}` : ''}
                </div>
              )}
            </div>
          ))}
        </div>
        )}
        </>
      )}
    </div>
    <ConfirmationDialog
      open={pendingAction !== null}
      title={pendingAction?.action === 'approve' ? 'Approve feature?' : 'Reject feature?'}
      description={pendingAction ? <>This will {pendingAction.action} <strong>{pendingAction.request.feature_id}</strong> as <strong>lead_reviewer</strong>.</> : ''}
      confirmLabel={pendingAction?.action === 'approve' ? 'Approve feature' : 'Reject feature'}
      confirmVariant={pendingAction?.action === 'reject' ? 'destructive' : 'default'}
      onCancel={() => setPendingAction(null)}
      onConfirm={() => pendingAction && executeAction(pendingAction.request, pendingAction.action)}
    />
    </>
  )
}
