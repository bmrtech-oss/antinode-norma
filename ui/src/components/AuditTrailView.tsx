import { useEffect, useMemo, useState } from 'react'
import { FileText, ShieldCheck, ShieldAlert, KeyRound, User } from 'lucide-react'
import { getJson } from '../lib/api'
import { EmptyState, ErrorState, LoadingState } from './ui/AsyncState'
import { Button } from './ui/Button'
import { Tooltip } from './ui/Tooltip'
import { Badge } from './ui/Badge'

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
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [actionFilter, setActionFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const pageSize = 10

  const fetchAudit = () => {
    setLoading(true)
    setError(null)
    Promise.all([
      getJson<AuditRecord[]>('/api/audit'),
      getJson<IntegrityInfo>('/api/audit/verify'),
    ])
      .then(([auditData, verifyData]) => {
        setRecords(auditData)
        setIntegrity(verifyData)
      })
      .catch(() => setError('The audit trail is unavailable.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchAudit()
  }, [])

  const actions = useMemo(
    () => ['all', ...Array.from(new Set(records.map((record) => record.action))).sort()],
    [records],
  )
  const filteredRecords = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    return records.filter((record) => {
      const matchesAction = actionFilter === 'all' || record.action === actionFilter
      const searchable = `${record.action} ${record.resource} ${record.actor}`.toLowerCase()
      return matchesAction && (!normalizedQuery || searchable.includes(normalizedQuery))
    })
  }, [actionFilter, query, records])
  const pageCount = Math.max(1, Math.ceil(filteredRecords.length / pageSize))
  const visibleRecords = filteredRecords.slice((page - 1) * pageSize, page * pageSize)

  useEffect(() => {
    setPage(1)
  }, [actionFilter, query])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h2 className="flex items-center space-x-2 text-lg font-bold text-foreground">
            <FileText className="h-5 w-5 text-primary" />
            <Tooltip content="Review the cryptographically chained record of governance and execution events.">
              <span>Immutable Audit Trail</span>
            </Tooltip>
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Cryptographically chained SHA-256 event stream logging all governance and execution actions.
          </p>
        </div>

        {/* Verification Status Badge */}
        {integrity && (
          <div className="flex items-center space-x-2 rounded-lg border border-border bg-card px-3 py-1.5 text-xs">
            <KeyRound className="h-4 w-4 text-primary" />
            <span className="text-muted-foreground">Chain Integrity:</span>
            {integrity.is_valid ? (
              <span className="text-success font-semibold flex items-center">
                <ShieldCheck className="h-4 w-4 mr-1 text-success" aria-hidden="true" /> VERIFIED
              </span>
            ) : (
              <span className="text-destructive font-semibold flex items-center">
                <ShieldAlert className="h-4 w-4 mr-1 text-destructive" aria-hidden="true" /> TAMPERED
              </span>
            )}
          </div>
        )}
      </div>

      {loading ? (
        <LoadingState label="Loading audit log..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchAudit} />
      ) : records.length === 0 ? (
        <EmptyState title="No audit events" description="Governance and execution events will appear here as the platform is used." />
      ) : (
        <>
        <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-card p-4">
          <label className="min-w-56 flex-1 text-xs font-medium text-muted-foreground">
            <Tooltip content="Search by action, resource, or actor.">Search audit events</Tooltip>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Action, resource, or actor" className="mt-1 block h-9 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground" />
          </label>
          <label className="text-xs font-medium text-muted-foreground">
            <Tooltip content="Filter events by the recorded action.">Action</Tooltip>
            <select value={actionFilter} onChange={(event) => setActionFilter(event.target.value)} className="mt-1 block h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground">
              {actions.map((action) => <option key={action} value={action}>{action === 'all' ? 'All actions' : action}</option>)}
            </select>
          </label>
          <Button variant="ghost" size="sm" onClick={() => { setQuery(''); setActionFilter('all') }}>Reset</Button>
          <span className="pb-2 text-xs text-muted-foreground" aria-live="polite">{filteredRecords.length} of {records.length} events</span>
        </div>
        {filteredRecords.length === 0 ? (
          <EmptyState title="No matching audit events" description="Try a different action, resource, or actor search." />
        ) : (
        <div className="space-y-3" aria-label="Audit events">
          {visibleRecords.map((rec) => (
            <div key={rec.id} className="space-y-2 rounded-xl border border-border bg-card p-4 text-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Badge variant="outline">{rec.action}</Badge>
                  <span className="font-medium text-foreground">{rec.resource}</span>
                </div>
                <span className="font-mono text-[11px] text-muted-foreground">
                  {new Date(rec.timestamp).toLocaleString()}
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-border pt-1 text-muted-foreground">
                <div className="flex items-center space-x-1.5 text-foreground">
                  <User className="h-3.5 w-3.5 text-muted-foreground" />
                  <span>Actor: <strong>{rec.actor}</strong></span>
                </div>
                <Button variant="ghost" size="sm" className="h-auto px-1 py-0 text-[10px]" onClick={() => setExpandedId(expandedId === rec.id ? null : rec.id)} aria-expanded={expandedId === rec.id}>
                  {expandedId === rec.id ? 'Hide details' : 'Show details'}
                </Button>
              </div>
              {expandedId === rec.id && (
                <div className="space-y-2 border-t border-border pt-3">
                  <div>
                    <span className="font-medium text-foreground">Payload</span>
                    <pre className="mt-1 max-h-48 overflow-auto rounded border border-border bg-background p-2 font-mono text-[10px] text-muted-foreground">{JSON.stringify(rec.payload, null, 2)}</pre>
                  </div>
                  <div className="grid gap-2 font-mono text-[10px] text-muted-foreground sm:grid-cols-2">
                    <span className="break-all">Previous hash: {rec.previous_hash || '—'}</span>
                    <span className="break-all">Content hash: {rec.content_hash}</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        )}
        {pageCount > 1 && (
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Page {page} of {pageCount}</span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage((current) => current - 1)}>Previous</Button>
              <Button variant="outline" size="sm" disabled={page === pageCount} onClick={() => setPage((current) => current + 1)}>Next</Button>
            </div>
          </div>
        )}
        </>
      )}
    </div>
  )
}
