import { useCallback, useEffect, useRef, useState } from 'react'
import { Download, Eye, FileSpreadsheet, Loader2, RotateCcw, UploadCloud } from 'lucide-react'
import { getApiBaseUrl, getBlob, getJson, postForm, postJson } from '../lib/api'
import { Alert } from './ui/Alert'
import { Button } from './ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Tooltip } from './ui/Tooltip'

interface ImportResponse {
  id: string
  filename: string
  format: 'csv' | 'xlsx'
  status: string
  row_count: number
  columns: string[]
  worksheet_names: string[]
  worksheet?: string | null
  mapping: Record<string, string>
}

interface ValidationResponse {
  import_id: string
  valid: boolean
  row_count: number
  errors: Array<{ row: number; field: string; message: string }>
}

interface ImportPreview {
  id: string
  filename: string
  format: 'csv' | 'xlsx'
  row_count: number
  columns: string[]
  worksheet_names: string[]
  worksheet?: string | null
  mapping: Record<string, string>
  rows: Array<{ source_row: number; values: Record<string, unknown> }>
}

interface GenerationJobResponse {
  id: string
  import_id: string
  status: string
  result: { errors?: ValidationResponse['errors']; valid?: boolean }
  created_at: string
  total_rows: number
  processed_rows: number
  successful_rows: number
  warning_rows: number
  failed_rows: number
  current_item?: string | null
  progress_percent: number
  error?: string | null
  source_filename?: string
}

interface GenerationJobListResponse {
  items: GenerationJobResponse[]
  total: number
  offset: number
  limit: number
}

interface GenerationResult {
  id: string
  row_number: number
  case_id: string
  status: string
  artifact_name?: string | null
  warnings: string[]
  error?: string | null
  content?: string | null
  approval_id?: string | null
  approval_status?: string | null
}

const ACTIVE_GENERATION_JOB_KEY = 'norma-ui-active-generation-job'

export default function Generation() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [importJob, setImportJob] = useState<ImportResponse | null>(null)
  const [validation, setValidation] = useState<ValidationResponse | null>(null)
  const [preview, setPreview] = useState<ImportPreview | null>(null)
  const [mapping, setMapping] = useState<Record<string, string>>({})
  const [mappingLoading, setMappingLoading] = useState(false)
  const [generationJob, setGenerationJob] = useState<GenerationJobResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<GenerationResult[]>([])
  const [history, setHistory] = useState<GenerationJobListResponse | null>(null)
  const [historyStatus, setHistoryStatus] = useState('')
  const [historyLoading, setHistoryLoading] = useState(false)
  const [selectedResult, setSelectedResult] = useState<GenerationResult | null>(null)
  const [submittedResults, setSubmittedResults] = useState<Set<string>>(new Set())
  const [selectedResults, setSelectedResults] = useState<Set<string>>(new Set())
  const [connectionState, setConnectionState] = useState<'connecting' | 'live' | 'polling'>('connecting')
  const pollTimerRef = useRef<number | null>(null)

  const selectFile = (selectedFile: File | undefined) => {
    setError(null)
    if (!selectedFile) return
    const extension = selectedFile.name.toLowerCase().split('.').pop()
    if (extension !== 'csv' && extension !== 'xlsx') {
      setFile(null)
      setError('Choose a CSV or XLSX file.')
      return
    }

    setFile(selectedFile)
    setImportJob(null)
    setValidation(null)
    setPreview(null)
    setMapping({})
    setGenerationJob(null)
    setResults([])
  }

  const loadHistory = useCallback(async (status = historyStatus) => {
    setHistoryLoading(true)
    try {
      const query = new URLSearchParams({ offset: '0', limit: '20' })
      if (status) query.set('status', status)
      setHistory(await getJson<GenerationJobListResponse>(`/v1/generation-jobs?${query}`))
    } catch (historyError) {
      setError(historyError instanceof Error ? historyError.message : 'Unable to load generation history.')
    } finally {
      setHistoryLoading(false)
    }
  }, [historyStatus])

  const selectHistoryJob = async (job: GenerationJobResponse) => {
    setGenerationJob(job)
    window.localStorage.setItem(ACTIVE_GENERATION_JOB_KEY, job.id)
    try {
      const response = await getJson<{ results: GenerationResult[] }>(`/v1/generation-jobs/${job.id}/results`)
      setResults(response.results)
      setSubmittedResults(new Set(response.results.filter((result) => result.approval_status).map((result) => result.id)))
    } catch (historyError) {
      setError(historyError instanceof Error ? historyError.message : 'Unable to load generation results.')
    }
  }

  const uploadFile = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const imported = await postForm<ImportResponse>('/v1/imports', formData)
      setImportJob(imported)
      const importedPreview = await getJson<ImportPreview>(`/v1/imports/${imported.id}/preview`)
      setPreview(importedPreview)
      setMapping(importedPreview.mapping)
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'The file could not be uploaded.')
    } finally {
      setLoading(false)
    }

  }

  const saveMapping = async () => {
    if (!importJob || !preview) return
    setMappingLoading(true)
    setError(null)
    try {
      await postJson(`/v1/imports/${importJob.id}/mapping`, {
        worksheet: preview.worksheet,
        columns: Object.fromEntries(Object.entries(mapping).filter(([, value]) => value)),
      })
      const nextPreview = await getJson<ImportPreview>(`/v1/imports/${importJob.id}/preview`)
      setPreview(nextPreview)
      setMapping(nextPreview.mapping)
    } catch (mappingError) {
      setError(mappingError instanceof Error ? mappingError.message : 'Unable to save column mapping.')
    } finally {
      setMappingLoading(false)
    }
  }

  const changeWorksheet = async (worksheet: string) => {
    if (!importJob) return
    setMappingLoading(true)
    try {
      await postJson(`/v1/imports/${importJob.id}/mapping`, { worksheet, columns: mapping })
      const nextPreview = await getJson<ImportPreview>(`/v1/imports/${importJob.id}/preview`)
      setPreview(nextPreview)
      setMapping(nextPreview.mapping)
    } catch (worksheetError) {
      setError(worksheetError instanceof Error ? worksheetError.message : 'Unable to select worksheet.')
    } finally {
      setMappingLoading(false)
    }
  }

  const validateImport = async () => {
    if (!importJob) return
    setLoading(true)
    setError(null)
    try {
      setValidation(await postJson<ValidationResponse, Record<string, never>>(`/v1/imports/${importJob.id}/validate`, {}))
    } catch (validationError) {
      setError(validationError instanceof Error ? validationError.message : 'Validation failed.')
    } finally {
      setLoading(false)
    }
  }

  const startGeneration = async () => {
    if (!importJob) return
    setLoading(true)
    setError(null)
    try {
      const job = await postJson<GenerationJobResponse, { import_id: string }>('/v1/generation-jobs', { import_id: importJob.id })
      setGenerationJob(job)
      window.localStorage.setItem(ACTIVE_GENERATION_JOB_KEY, job.id)
    } catch (generationError) {
      setError(generationError instanceof Error ? generationError.message : 'Generation could not be started.')
    } finally {
      setLoading(false)
    }

  }

  useEffect(() => {
    void loadHistory()
    const activeJobId = window.localStorage.getItem(ACTIVE_GENERATION_JOB_KEY)
    if (!activeJobId) return
    void getJson<GenerationJobResponse>(`/v1/generation-jobs/${activeJobId}`)
      .then(setGenerationJob)
      .catch(() => window.localStorage.removeItem(ACTIVE_GENERATION_JOB_KEY))
  }, [loadHistory])

  const activeJobId = generationJob?.id
  const activeJobStatus = generationJob?.status

  useEffect(() => {
    if (!activeJobId || !activeJobStatus || !['queued', 'running'].includes(activeJobStatus)) return
    const jobId = activeJobId
    const poll = () => {
      setConnectionState('polling')
      void getJson<GenerationJobResponse>(`/v1/generation-jobs/${jobId}`)
        .then((job) => {
          setGenerationJob(job)
          if (!['queued', 'running'].includes(job.status) && pollTimerRef.current !== null) {
            window.clearInterval(pollTimerRef.current)
            pollTimerRef.current = null
          }
        })
        .catch((pollError) => setError(pollError instanceof Error ? pollError.message : 'Unable to read generation progress.'))
    }
    const startPolling = () => {
      if (pollTimerRef.current === null) {
        poll()
        pollTimerRef.current = window.setInterval(poll, 1500)
      }
    }
    setConnectionState('connecting')
    const source = new EventSource(`${getApiBaseUrl()}/v1/generation-jobs/${jobId}/events`)
    const handleEvent = (event: MessageEvent<string>) => {
      setConnectionState('live')
      try {
        setGenerationJob(JSON.parse(event.data) as GenerationJobResponse)
      } catch {
        startPolling()
      }
    }
    source.addEventListener('generation.progress', handleEvent)
    source.addEventListener('generation.completed', handleEvent)
    source.addEventListener('generation.failed', handleEvent)
    source.addEventListener('generation.cancelled', handleEvent)
    source.onopen = () => setConnectionState('live')
    source.onerror = () => startPolling()
    return () => {
      source.close()
      if (pollTimerRef.current !== null) {
        window.clearInterval(pollTimerRef.current)
        pollTimerRef.current = null
      }
    }
  }, [activeJobId, activeJobStatus])

  const generationStatus = generationJob?.status

  useEffect(() => {
    if (generationStatus && !['queued', 'running'].includes(generationStatus)) {
      void loadHistory()
    }
  }, [generationStatus, loadHistory])

  useEffect(() => {
    if (!activeJobId || !activeJobStatus || !['completed', 'completed_with_errors', 'failed', 'cancelled'].includes(activeJobStatus)) return
    void getJson<{ results: GenerationResult[] }>(`/v1/generation-jobs/${activeJobId}/results`)
      .then((response) => {
        setResults(response.results)
        setSubmittedResults(new Set(response.results.filter((result) => result.approval_status).map((result) => result.id)))
      })
      .catch((resultsError) => setError(resultsError instanceof Error ? resultsError.message : 'Unable to read generation results.'))
  }, [activeJobId, activeJobStatus])

  const updateJob = async (action: 'cancel' | 'retry') => {
    if (!generationJob) return
    setLoading(true)
    try {
      const response = await postJson<GenerationJobResponse, Record<string, never>>(
        `/v1/generation-jobs/${generationJob.id}/${action}`,
        {},
      )
      setGenerationJob(response)
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : `Unable to ${action} generation.`)
    } finally {
      setLoading(false)
    }

  }

  const retryResult = async (result: GenerationResult) => {
    if (!generationJob) return
    setLoading(true)
    try {
      const response = await postJson<GenerationJobResponse, Record<string, never>>(
        `/v1/generation-jobs/${generationJob.id}/results/${result.id}/retry`,
        {},
      )
      setGenerationJob(response)
    } catch (retryError) {
      setError(retryError instanceof Error ? retryError.message : 'Unable to retry this result.')
    } finally {
      setLoading(false)
    }
  }

  const downloadResult = async (result: GenerationResult) => {
    if (!generationJob) return
    try {
      const blob = await getBlob(`/v1/generation-jobs/${generationJob.id}/results/${result.id}/download`)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = result.artifact_name ?? `row-${result.row_number}.feature`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (downloadError) {
      setError(downloadError instanceof Error ? downloadError.message : 'Unable to download this artifact.')
    }

  }

  const submitForApproval = async (result: GenerationResult) => {
    if (!generationJob) return
    setLoading(true)
    try {
      await postJson(`/v1/generation-jobs/${generationJob.id}/results/${result.id}/submit-approval`, {})
      setSubmittedResults((current) => new Set(current).add(result.id))
    } catch (approvalError) {
      setError(approvalError instanceof Error ? approvalError.message : 'Unable to submit this result for approval.')
    } finally {
      setLoading(false)
    }
  }

  const submitSelectedForApproval = async () => {
    if (!generationJob || selectedResults.size === 0) return
    setLoading(true)
    try {
      await postJson(`/v1/generation-jobs/${generationJob.id}/results/submit-approval`, {
        result_ids: Array.from(selectedResults),
      })
      setSelectedResults(new Set())
      const response = await getJson<{ results: GenerationResult[] }>(`/v1/generation-jobs/${generationJob.id}/results`)
      setResults(response.results)
      setSubmittedResults(new Set(response.results.filter((result) => result.approval_status).map((result) => result.id)))
    } catch (approvalError) {
      setError(approvalError instanceof Error ? approvalError.message : 'Unable to submit selected results for approval.')
    } finally {
      setLoading(false)
    }
  }

  const downloadResults = async () => {
    if (!generationJob) return
    try {
      const blob = await getBlob(`/v1/generation-jobs/${generationJob.id}/download`)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${generationJob.id}.zip`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (downloadError) {
      setError(downloadError instanceof Error ? downloadError.message : 'Unable to download generated features.')
    }
  }

  return (
    <div className="space-y-6">
      <div className="border-b border-border pb-4">
        <h2 className="flex items-center gap-2 text-xl font-bold text-foreground">
          <UploadCloud className="h-5 w-5 text-primary" aria-hidden="true" />
          <Tooltip content="Upload structured test cases, validate their rows, and start feature generation.">
            <span>Feature Generation</span>
          </Tooltip>
        </h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Import CSV or XLSX test cases and prepare them for asynchronous Gherkin generation.
        </p>
      </div>

      {error && <Alert variant="destructive" aria-live="assertive">{error}</Alert>}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5 text-primary" aria-hidden="true" />
            <span>New import</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <button
            type="button"
            className="flex w-full flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-border bg-muted/30 p-10 text-center transition hover:border-primary hover:bg-accent"
            onClick={() => inputRef.current?.click()}
          >
            <UploadCloud className="h-8 w-8 text-primary" aria-hidden="true" />
            <span className="font-medium text-foreground">{file ? file.name : 'Choose a CSV or XLSX file'}</span>
            <span className="text-xs text-muted-foreground">Files are validated before generation begins.</span>
          </button>
          <input
            ref={inputRef}
            className="sr-only"
            type="file"
            aria-label="Choose a CSV or XLSX file"
            accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            onChange={(event) => selectFile(event.target.files?.[0])}
          />
          <div className="flex justify-end">
            <Button onClick={() => void uploadFile()} disabled={!file || loading}>
              {loading ? 'Uploading...' : 'Upload and validate'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {importJob && (
        <Card>
          <CardHeader><CardTitle>Import validation</CardTitle></CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-4">
            <Metric label="Status" value={importJob.status} />
            <Metric label="Rows detected" value={importJob.row_count} />
            <Metric label="Format" value={importJob.format.toUpperCase()} />
            <Metric label="Validation" value={validation ? (validation.valid ? 'Passed' : 'Needs attention') : 'Not run'} />
            <div className="flex gap-2 sm:col-span-4">
              <Button variant="outline" onClick={() => void validateImport()} disabled={loading}>
                {loading && !generationJob ? 'Validating...' : 'Validate import'}
              </Button>
              <Button onClick={() => void startGeneration()} disabled={loading || !validation?.valid}>
                Start generation
              </Button>
            </div>
            {validation && !validation.valid && (
              <div className="space-y-3 sm:col-span-4">
                <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
                  {validation.errors.length} row validation issue(s) need attention before generation.
                </div>
                <div className="overflow-x-auto rounded-lg border border-border">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-muted text-muted-foreground">
                      <tr>
                        <th className="px-3 py-2 font-semibold">Row</th>
                        <th className="px-3 py-2 font-semibold">Field</th>
                        <th className="px-3 py-2 font-semibold">Issue</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {validation.errors.map((issue, index) => (
                        <tr key={`${issue.row}-${issue.field}-${index}`}>
                          <td className="px-3 py-2 text-foreground">{issue.row}</td>
                          <td className="px-3 py-2 text-foreground">{issue.field}</td>
                          <td className="px-3 py-2 text-destructive">{issue.message}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {preview && (
              <Card>
                <CardHeader><CardTitle>Import preview</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {preview.worksheet_names.length > 0 && (
                    <label className="block text-xs font-medium text-muted-foreground">
                      Worksheet
                      <select
                        className="mt-1 block h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground"
                        value={preview.worksheet ?? ''}
                        onChange={(event) => void changeWorksheet(event.target.value)}
                        disabled={mappingLoading}
                      >
                        {preview.worksheet_names.map((worksheet) => <option key={worksheet}>{worksheet}</option>)}
                      </select>
                    </label>
                  )}
                  <div className="grid gap-3 rounded-lg border border-border bg-muted/20 p-3 sm:grid-cols-2 lg:grid-cols-4">
                    {['id', 'title', 'role', 'action', 'benefit', 'acceptance_criteria', 'tags'].map((field) => (
                      <label key={field} className="text-xs font-medium text-muted-foreground">
                        {field.replace('_', ' ')}
                        <select
                          className="mt-1 block h-9 w-full rounded-md border border-input bg-background px-2 text-sm text-foreground"
                          value={mapping[field] ?? ''}
                          onChange={(event) => setMapping((current) => ({ ...current, [field]: event.target.value }))}
                        >
                          <option value="">Not mapped</option>
                          {preview.columns.map((column) => <option key={column} value={column}>{column}</option>)}
                        </select>
                      </label>
                    ))}
                  </div>
                  <Button variant="outline" size="sm" onClick={() => void saveMapping()} disabled={mappingLoading}>
                    {mappingLoading ? 'Saving mapping...' : 'Save column mapping'}
                  </Button>
                  <p className="text-xs text-muted-foreground">
                    Showing the first {preview.rows.length} of {preview.row_count} detected rows from {preview.filename}.
                  </p>
                  <div className="overflow-x-auto rounded-lg border border-border">
                    <table className="w-full min-w-[36rem] text-left text-xs">
                      <thead className="bg-muted text-muted-foreground">
                        <tr>
                          {preview.columns.map((column) => (
                            <th key={column} className="px-3 py-2 font-semibold">{column}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {preview.rows.slice(0, 5).map((row, index) => (
                          <tr key={index}>
                            {preview.columns.map((column) => (
                              <td key={column} className="max-w-64 truncate px-3 py-2 text-foreground">
                                {String(row.values[column] ?? '')}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Job history</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <label className="text-xs font-medium text-muted-foreground">
              Status
              <select
                className="ml-2 h-9 rounded-md border border-input bg-background px-2 text-sm text-foreground"
                value={historyStatus}
                onChange={(event) => {
                  setHistoryStatus(event.target.value)
                  void loadHistory(event.target.value)
                }}
              >
                <option value="">All jobs</option>
                <option value="queued">Queued</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="completed_with_errors">Completed with errors</option>
                <option value="failed">Failed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </label>
            <Button variant="outline" size="sm" onClick={() => void loadHistory()} disabled={historyLoading}>
              {historyLoading ? 'Refreshing...' : 'Refresh history'}
            </Button>
          </div>
          {history?.items.length ? (
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full min-w-[42rem] text-left text-xs">
                <thead className="bg-muted text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-semibold">Source</th>
                    <th className="px-3 py-2 font-semibold">Status</th>
                    <th className="px-3 py-2 font-semibold">Rows</th>
                    <th className="px-3 py-2 font-semibold">Results</th>
                    <th className="px-3 py-2 font-semibold">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {history.items.map((job) => (
                    <tr key={job.id}>
                      <td className="px-3 py-2 text-foreground">{job.source_filename ?? job.import_id}</td>
                      <td className="px-3 py-2 text-foreground">{job.status}</td>
                      <td className="px-3 py-2 text-foreground">{job.processed_rows} / {job.total_rows}</td>
                      <td className="px-3 py-2 text-foreground">
                        {job.successful_rows} successful, {job.failed_rows} failed
                      </td>
                      <td className="px-3 py-2">
                        <Button variant="outline" size="sm" onClick={() => void selectHistoryJob(job)}>
                          Open
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">
              {historyLoading ? 'Loading generation history...' : 'No generation jobs found.'}
            </p>
          )}
        </CardContent>
      </Card>

      {generationJob && (
        <Card>
          <CardHeader><CardTitle>Generation job</CardTitle></CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p><span className="text-muted-foreground">Status:</span> <strong>{generationJob.status}</strong></p>
              <div className="flex gap-2">
                {['queued', 'running'].includes(generationJob.status) && (
                  <Button variant="outline" size="sm" onClick={() => void updateJob('cancel')} disabled={loading}>Cancel</Button>
                )}
                {['failed', 'completed_with_errors', 'cancelled'].includes(generationJob.status) && (
                  <Button variant="outline" size="sm" onClick={() => void updateJob('retry')} disabled={loading}>Retry</Button>
                )}
                {['completed', 'completed_with_errors'].includes(generationJob.status) && (
                  <Button size="sm" onClick={() => void downloadResults()}><Download className="h-4 w-4" />Download</Button>
                )}
              </div>
            </div>
            <div
              className="h-3 overflow-hidden rounded-full bg-muted"
              role="progressbar"
              aria-label={`Generation progress: ${generationJob.progress_percent}%`}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={generationJob.progress_percent}
            >
              <div className="h-full bg-primary transition-all" style={{ width: `${generationJob.progress_percent}%` }} />
            </div>
            <div className="grid gap-3 sm:grid-cols-4">
              <Metric label="Progress" value={`${generationJob.progress_percent}%`} />
              <Metric label="Processed" value={`${generationJob.processed_rows} / ${generationJob.total_rows}`} />
              <Metric label="Successful" value={generationJob.successful_rows} />
              <Metric label="Failed" value={generationJob.failed_rows} />
            </div>
            {generationJob.current_item && <p className="text-xs text-muted-foreground">Current item: {generationJob.current_item}</p>}
            {['queued', 'running'].includes(generationJob.status) && (
              <p className="text-xs text-muted-foreground" role="status">
                Updates: {connectionState === 'live' ? 'live stream' : connectionState === 'polling' ? 'polling fallback' : 'connecting'}
              </p>
            )}
            {generationJob.error && <p className="text-xs text-destructive">{generationJob.error}</p>}
            {generationJob.status === 'running' && <Loader2 className="h-4 w-4 animate-spin text-primary" aria-label="Generation is running" />}
            {results.length > 0 && (
              <div className="space-y-2 border-t border-border pt-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium">Results ({results.length})</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => void submitSelectedForApproval()}
                    disabled={loading || selectedResults.size === 0}
                  >
                    Submit selected ({selectedResults.size})
                  </Button>
                </div>
                {results.map((result) => (
                  <div key={result.id} className="space-y-2 rounded-md border border-border p-2 text-xs">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={selectedResults.has(result.id)}
                          onChange={(event) => setSelectedResults((current) => {
                            const next = new Set(current)
                            if (event.target.checked) next.add(result.id)
                            else next.delete(result.id)
                            return next
                          })}
                          disabled={result.status !== 'completed' || Boolean(result.approval_status)}
                        />
                        <span>{result.case_id} · row {result.row_number}</span>
                      </label>
                      <span className={result.status === 'completed' ? 'text-success' : 'text-destructive'}>{result.status}</span>
                    </div>
                    {result.approval_status && <p className="text-muted-foreground">Approval: {result.approval_status}</p>}
                    <div className="flex flex-wrap gap-2">
                      {result.content && (
                        <Button variant="outline" size="sm" onClick={() => setSelectedResult(result)}>
                          <Eye className="h-3.5 w-3.5" /> Preview
                        </Button>
                      )}
                      {result.content && (
                        <Button variant="outline" size="sm" onClick={() => void downloadResult(result)}>
                          <Download className="h-3.5 w-3.5" /> Download
                        </Button>
                      )}
                      {result.content && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => void submitForApproval(result)}
                          disabled={loading || submittedResults.has(result.id)}
                        >
                          {result.approval_status || (submittedResults.has(result.id) ? 'PENDING' : 'Submit for approval')}
                        </Button>
                      )}
                      {result.status === 'failed' && (
                        <Button variant="outline" size="sm" onClick={() => void retryResult(result)} disabled={loading}>
                          <RotateCcw className="h-3.5 w-3.5" /> Retry
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            {selectedResult?.content && (
              <div className="rounded-lg border border-border bg-muted/30 p-3">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <p className="font-medium">Preview: {selectedResult.artifact_name ?? selectedResult.case_id}</p>
                  <Button variant="ghost" size="sm" onClick={() => setSelectedResult(null)}>Close</Button>
                </div>
                <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-md bg-background p-3 text-xs text-foreground">
                  {selectedResult.content}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold text-foreground">{value}</p>
    </div>
  )
}
