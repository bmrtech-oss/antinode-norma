import { useEffect, useMemo, useState } from 'react'
import { GitMerge, CheckCircle2, Tag, AlertTriangle } from 'lucide-react'
import { getJson } from '../lib/api'
import { EmptyState, ErrorState, LoadingState } from './ui/AsyncState'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'

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
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedRequirement, setSelectedRequirement] = useState<string | null>(null)

  const fetchMatrix = () => {
    setLoading(true)
    setError(null)
    getJson<TraceabilityMatrix>('/api/traceability')
      .then((data: TraceabilityMatrix) => {
        setMatrix(data)
      })
      .catch(() => setError('Traceability data is unavailable.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchMatrix()
  }, [])

  const statuses = useMemo(
    () => ['all', ...Array.from(new Set(matrix?.items.map((item) => item.status) || [])).sort()],
    [matrix],
  )
  const visibleItems = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    return (matrix?.items || []).filter((item) => {
      const matchesStatus = statusFilter === 'all' || item.status === statusFilter
      const searchable = `${item.requirement_id} ${item.requirement_title} ${item.scenario_title} ${item.tags.join(' ')}`.toLowerCase()
      const matchesRequirement = !selectedRequirement || item.requirement_id === selectedRequirement
      return matchesStatus && matchesRequirement && (!normalizedQuery || searchable.includes(normalizedQuery))
    })
  }, [matrix, query, selectedRequirement, statusFilter])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border pb-4">
        <div>
          <h2 className="flex items-center space-x-2 text-lg font-bold text-foreground">
            <GitMerge className="h-5 w-5 text-primary" />
            <span>Requirement-to-Scenario Traceability Matrix</span>
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Map generated Gherkin test scenarios back to input requirement IDs and tags.
          </p>
        </div>
      </div>

      {loading ? (
        <LoadingState label="Building traceability matrix..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchMatrix} />
      ) : !matrix || matrix.items.length === 0 ? (
        <EmptyState title="No traceability mappings" description="Requirement-to-scenario mappings will appear when feature scenarios are available." />
      ) : (
        <div className="space-y-6">
          <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-card p-4">
            <label className="min-w-56 flex-1 text-xs font-medium text-muted-foreground">
              Search mappings
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Requirement, scenario, or tag" className="mt-1 block h-9 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground" />
            </label>
            <label className="text-xs font-medium text-muted-foreground">
              Status
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="mt-1 block h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground">
                {statuses.map((status) => <option key={status} value={status}>{status === 'all' ? 'All statuses' : status}</option>)}
              </select>
            </label>
            <Button variant="ghost" size="sm" onClick={() => { setQuery(''); setStatusFilter('all'); setSelectedRequirement(null) }}>
              Reset
            </Button>
            <span className="pb-2 text-xs text-muted-foreground" aria-live="polite">{visibleItems.length} of {matrix.items.length} mappings</span>
          </div>

          {/* Table */}
          <div className="hidden overflow-hidden rounded-xl border border-border bg-card shadow-xl md:block">
            <table className="w-full text-left text-xs text-foreground">
              <thead className="border-b border-border bg-muted font-semibold uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Requirement ID</th>
                  <th className="px-4 py-3">Requirement / Case Title</th>
                  <th className="px-4 py-3">Covered Scenario</th>
                  <th className="px-4 py-3">Tags</th>
                  <th className="px-4 py-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {visibleItems.map((item, idx) => (
                  <tr key={idx} className="transition hover:bg-accent">
                    <td className="px-4 py-3 font-mono font-semibold text-primary">{item.requirement_id}</td>
                    <td className="px-4 py-3 text-foreground">{item.requirement_title}</td>
                    <td className="px-4 py-3 font-mono text-muted-foreground">{item.scenario_title}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {item.tags.length > 0 ? (
                          item.tags.map((t, i) => (
                            <span key={i} className="flex items-center rounded border border-border bg-background px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                              <Tag className="mr-1 h-2.5 w-2.5 text-muted-foreground" /> {t}
                            </span>
                          ))
                        ) : (
                          <span className="italic text-muted-foreground">-</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="bg-success/10 border border-success/30 text-success px-2.5 py-0.5 rounded-full font-semibold text-[10px] inline-flex items-center">
                        <CheckCircle2 className="h-3 w-3 mr-1" aria-hidden="true" /> {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="space-y-3 md:hidden" aria-label="Traceability mappings">
            {visibleItems.map((item, idx) => (
              <article key={`${item.requirement_id}-${idx}`} className="rounded-xl border border-border bg-card p-4 text-sm">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-mono text-xs font-semibold text-primary">{item.requirement_id}</p>
                    <h3 className="mt-1 font-medium text-foreground">{item.requirement_title}</h3>
                  </div>
                  <Badge variant="success">{item.status}</Badge>
                </div>
                <p className="mt-3 font-mono text-xs text-muted-foreground">{item.scenario_title}</p>
                <div className="mt-3 flex flex-wrap gap-1">
                  {item.tags.map((tag) => <span key={tag} className="rounded border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground">{tag}</span>)}
                </div>
              </article>
            ))}
          </div>

          {visibleItems.length === 0 && (
            <EmptyState title="No matching mappings" description="Try a different requirement, scenario, tag, or status filter." />
          )}

          {/* Uncovered Requirements Warnings */}
          {matrix.uncovered_requirements.length > 0 && (
            <div className="space-y-2 rounded-xl border border-warning/30 bg-warning/10 p-4">
              <h4 className="flex items-center space-x-2 text-xs font-semibold text-warning">
                <AlertTriangle className="h-4 w-4" />
                <span>Uncovered Requirements ({matrix.uncovered_requirements.length})</span>
              </h4>
              <ul className="list-inside list-disc space-y-1 text-xs text-warning">
                {matrix.uncovered_requirements.map((unreq, i) => (
                  <li key={i}>
                    <Button variant="ghost" size="sm" className="h-auto p-0 text-left text-warning" onClick={() => setSelectedRequirement(unreq)}>
                      {unreq}
                    </Button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
