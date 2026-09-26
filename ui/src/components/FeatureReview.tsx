import { useEffect, useMemo, useState } from 'react'
import { FileText } from 'lucide-react'
import { getJson, postJson } from '../lib/api'
import { useAuth } from '../lib/AuthContext'
import { EmptyState, ErrorState, LoadingState } from './ui/AsyncState'
import { Badge } from './ui/Badge'
import { Button } from './ui/Button'
import { Tooltip } from './ui/Tooltip'
import { Alert } from './ui/Alert'

interface Feature {
  id: string
  title?: string
  gherkin?: string
  status: string
  created_at?: string
  source_job_id?: string | null
  source_result_id?: string | null
  approval_id?: string | null
}

export default function FeatureReview() {
  const [features, setFeatures] = useState<Feature[]>([])
  const [selectedFeature, setSelectedFeature] = useState<Feature | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest' | 'name'>('newest')
  const [actionLoading, setActionLoading] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)
  const { hasPermission } = useAuth()
  const canApprove = hasPermission('approval:action')

  const fetchFeatures = () => {
    setLoading(true)
    setError(null)
    getJson<Feature[]>('/api/features')
      .then((data) => {
        if (Array.isArray(data)) {
          setFeatures(data)
          if (data.length > 0) setSelectedFeature(data[0])
        }
      })
      .catch(() => setError('Generated features are unavailable.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchFeatures()
  }, [])

  const statuses = useMemo(
    () => ['all', ...Array.from(new Set(features.map((feature) => feature.status))).sort()],
    [features],
  )

  const visibleFeatures = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    return features
      .filter((feature) => {
        const matchesStatus = statusFilter === 'all' || feature.status === statusFilter
        const searchable = `${feature.id} ${feature.title} ${feature.status}`.toLowerCase()
        return matchesStatus && (!normalizedQuery || searchable.includes(normalizedQuery))
      })
      .sort((left, right) => {
        if (sortOrder === 'name') {
          return (left.title || left.id).localeCompare(right.title || right.id)
        }
        const leftDate = new Date(left.created_at || 0).getTime()
        const rightDate = new Date(right.created_at || 0).getTime()
        return sortOrder === 'newest' ? rightDate - leftDate : leftDate - rightDate
      })
  }, [features, query, sortOrder, statusFilter])

  useEffect(() => {
    if (selectedFeature && !visibleFeatures.some((feature) => feature.id === selectedFeature.id)) {
      setSelectedFeature(visibleFeatures[0] || null)
    }
  }, [selectedFeature, visibleFeatures])

  const updateApproval = async (action: 'approve' | 'reject') => {
    if (!selectedFeature?.approval_id) return
    setActionLoading(true)
    setFeedback(null)
    try {
      await postJson(`/api/approvals/${selectedFeature.approval_id}/${action}`, {
        reason: action === 'approve' ? 'Approved from Feature Review' : 'Requires revision',
      })
      setFeedback(`Feature ${action === 'approve' ? 'approved' : 'rejected'} successfully.`)
      fetchFeatures()
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : `Unable to ${action} feature.`)
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h2 className="flex items-center space-x-2 text-xl font-bold text-foreground">
            <FileText className="h-5 w-5 text-primary" />
            <Tooltip content="Review generated Gherkin features and their quality gate evaluations.">
              <span>Feature Review</span>
            </Tooltip>
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Review generated Gherkin feature files and quality gate evaluations.
          </p>
        </div>
      </div>

      {loading ? (
        <LoadingState label="Loading features..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchFeatures} />
      ) : features.length === 0 ? (
        <EmptyState title="No generated features" description="Generated Gherkin features will appear here when they are available for review." />
      ) : (
        <div className="space-y-4">
          {feedback && <Alert variant="success" aria-live="polite">{feedback}</Alert>}
          <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-card p-4">
            <label className="min-w-56 flex-1 text-xs font-medium text-muted-foreground">
              <Tooltip content="Search by feature title, ID, or status.">
                Search features
              </Tooltip>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search by title, ID, or status"
                className="mt-1 block h-9 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground"
              />
            </label>
            <label className="text-xs font-medium text-muted-foreground">
              <Tooltip content="Filter features by their current workflow status.">Status</Tooltip>
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="mt-1 block h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground"
              >
                {statuses.map((status) => (
                  <option key={status} value={status}>
                    {status === 'all' ? 'All statuses' : status}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-xs font-medium text-muted-foreground">
              <Tooltip content="Choose the order used for the feature list.">Sort</Tooltip>
              <select
                value={sortOrder}
                onChange={(event) => setSortOrder(event.target.value as typeof sortOrder)}
                className="mt-1 block h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground"
              >
                <option value="newest">Newest first</option>
                <option value="oldest">Oldest first</option>
                <option value="name">Name</option>
              </select>
            </label>
            <Button variant="ghost" size="sm" onClick={() => {
              setQuery('')
              setStatusFilter('all')
              setSortOrder('newest')
            }}>
              Reset
            </Button>
          </div>

          <div className="flex items-center justify-between text-xs text-muted-foreground" aria-live="polite">
            <span>Showing {visibleFeatures.length} of {features.length} features</span>
            {visibleFeatures.length === 0 && <span>Adjust the search or status filter.</span>}
          </div>

          {visibleFeatures.length === 0 ? (
            <EmptyState title="No matching features" description="Try a different search term or clear the status filter." />
          ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Features List</h3>
            <div className="space-y-2">
              {visibleFeatures.map((f) => (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => setSelectedFeature(f)}
                  className={`w-full text-left p-3 rounded-lg border text-sm transition ${
                    selectedFeature?.id === f.id
                      ? 'border-primary/50 bg-primary/10 text-foreground'
                      : 'border-border bg-background text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <div className="font-medium truncate">{f.title || f.id}</div>
                  <div className="mt-1 text-xs uppercase text-muted-foreground">{f.status}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="md:col-span-2 space-y-4 rounded-xl border border-border bg-card p-6">
            {selectedFeature ? (
              <>
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <h3 className="font-semibold text-foreground">{selectedFeature.title || selectedFeature.id}</h3>
                  <div className="flex items-center gap-2">
                    <Badge variant={selectedFeature.status === 'PENDING' ? 'warning' : 'success'}>{selectedFeature.status}</Badge>
                    {selectedFeature.approval_id && selectedFeature.status === 'PENDING' && (
                      <>
                        <Button size="sm" onClick={() => void updateApproval('approve')} disabled={actionLoading || !canApprove} title={canApprove ? undefined : 'Requires approval:action permission'}>Approve</Button>
                        <Button variant="destructive" size="sm" onClick={() => void updateApproval('reject')} disabled={actionLoading || !canApprove} title={canApprove ? undefined : 'Requires approval:action permission'}>Reject</Button>
                      </>
                    )}
                  </div>
                </div>
                <dl className="grid grid-cols-1 gap-3 border-b border-border pb-3 text-xs sm:grid-cols-3">
                  <div>
                    <dt className="text-muted-foreground">Feature ID</dt>
                    <dd className="mt-1 font-mono text-foreground">{selectedFeature.id}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Created</dt>
                    <dd className="mt-1 text-foreground">{selectedFeature.created_at ? new Date(selectedFeature.created_at).toLocaleString() : 'Unknown'}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Content size</dt>
                    <dd className="mt-1 text-foreground">{(selectedFeature.gherkin ?? '').length.toLocaleString()} characters</dd>
                  </div>
                </dl>
                {(selectedFeature.source_job_id || selectedFeature.source_result_id) && (
                  <dl className="grid grid-cols-1 gap-3 border-b border-border pb-3 text-xs sm:grid-cols-2">
                    <div>
                      <dt className="text-muted-foreground">Generation job</dt>
                      <dd className="mt-1 font-mono text-foreground">{selectedFeature.source_job_id ?? 'Unknown'}</dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Generation result</dt>
                      <dd className="mt-1 font-mono text-foreground">{selectedFeature.source_result_id ?? 'Unknown'}</dd>
                    </div>
                  </dl>
                )}
                <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg border border-border bg-background p-4 font-mono text-xs text-primary">
                  {selectedFeature.gherkin || '# No Gherkin feature text available.'}
                </pre>
              </>
            ) : (
              <div className="text-sm text-muted-foreground">Select a feature from the list to review.</div>
            )}
          </div>
          </div>
          )}
        </div>
      )}
    </div>
  )
}
