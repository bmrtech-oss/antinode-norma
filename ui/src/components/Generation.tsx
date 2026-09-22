import { useEffect, useRef, useState } from 'react'
import { Download, FileSpreadsheet, Loader2, UploadCloud } from 'lucide-react'
import { getBlob, getJson, postForm, postJson } from '../lib/api'
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
}

interface GenerationResult {
  id: string
  row_number: number
  case_id: string
  status: string
  artifact_name?: string | null
  warnings: string[]
  error?: string | null
}

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
      setGenerationJob(await postJson<GenerationJobResponse, { import_id: string }>('/v1/generation-jobs', { import_id: importJob.id }))
    } catch (generationError) {
      setError(generationError instanceof Error ? generationError.message : 'Generation could not be started.')
    } finally {
      setLoading(false)
    }

  }

  useEffect(() => {
    if (!generationJob || !['queued', 'running'].includes(generationJob.status)) return
    const timer = window.setInterval(() => {
      void getJson<GenerationJobResponse>(`/v1/generation-jobs/${generationJob.id}`)
        .then(setGenerationJob)
        .catch((pollError) => setError(pollError instanceof Error ? pollError.message : 'Unable to read generation progress.'))
    }, 1500)
    return () => window.clearInterval(timer)
  }, [generationJob])

  useEffect(() => {
    if (!generationJob || !['completed', 'completed_with_errors', 'failed', 'cancelled'].includes(generationJob.status)) return
    void getJson<{ results: GenerationResult[] }>(`/v1/generation-jobs/${generationJob.id}/results`)
      .then((response) => setResults(response.results))
      .catch((resultsError) => setError(resultsError instanceof Error ? resultsError.message : 'Unable to read generation results.'))
  }, [generationJob])

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

  const downloadResults = async () => {
    if (!generationJob) return
    try {
      const blob = await getBlob(`/v1/generation-jobs/${generationJob.id}/download`)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${generationJob.id}.zip`
      link.click()
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
            <div className="h-3 overflow-hidden rounded-full bg-muted" aria-label={`Generation progress ${generationJob.progress_percent}%`}>
              <div className="h-full bg-primary transition-all" style={{ width: `${generationJob.progress_percent}%` }} />
            </div>
            <div className="grid gap-3 sm:grid-cols-4">
              <Metric label="Progress" value={`${generationJob.progress_percent}%`} />
              <Metric label="Processed" value={`${generationJob.processed_rows} / ${generationJob.total_rows}`} />
              <Metric label="Successful" value={generationJob.successful_rows} />
              <Metric label="Failed" value={generationJob.failed_rows} />
            </div>
            {generationJob.current_item && <p className="text-xs text-muted-foreground">Current item: {generationJob.current_item}</p>}
            {generationJob.error && <p className="text-xs text-destructive">{generationJob.error}</p>}
            {generationJob.status === 'running' && <Loader2 className="h-4 w-4 animate-spin text-primary" aria-label="Generation is running" />}
            {results.length > 0 && (
              <div className="space-y-2 border-t border-border pt-4">
                <p className="font-medium">Results ({results.length})</p>
                {results.map((result) => (
                  <div key={result.id} className="flex flex-wrap justify-between gap-2 rounded-md border border-border p-2 text-xs">
                    <span>{result.case_id} · row {result.row_number}</span>
                    <span className={result.status === 'completed' ? 'text-success' : 'text-destructive'}>{result.status}</span>
                  </div>
                ))}
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
