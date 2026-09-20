import { useEffect, useState } from 'react'
import { FileText } from 'lucide-react'

interface Feature {
  id: string
  title: string
  gherkin: string
  status: string
  created_at: string
}

export default function FeatureReview() {
  const [features, setFeatures] = useState<Feature[]>([])
  const [selectedFeature, setSelectedFeature] = useState<Feature | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    fetch('/api/features')
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setFeatures(data)
          if (data.length > 0) setSelectedFeature(data[0])
        }
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
            <FileText className="h-5 w-5 text-indigo-400" />
            <span>Feature Review</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Review generated Gherkin feature files and quality gate evaluations.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="p-8 text-center text-slate-400">Loading features...</div>
      ) : features.length === 0 ? (
        <div className="p-8 text-center text-slate-500 border border-slate-800 rounded-xl bg-slate-950">
          No generated features found for review.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Features List</h3>
            <div className="space-y-2">
              {features.map((f) => (
                <button
                  key={f.id}
                  onClick={() => setSelectedFeature(f)}
                  className={`w-full text-left p-3 rounded-lg border text-sm transition ${
                    selectedFeature?.id === f.id
                      ? 'bg-indigo-600/20 border-indigo-500 text-slate-100'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <div className="font-medium truncate">{f.title || f.id}</div>
                  <div className="text-xs text-slate-500 mt-1 uppercase">{f.status}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="md:col-span-2 space-y-4 bg-slate-950 border border-slate-800 p-6 rounded-xl">
            {selectedFeature ? (
              <>
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="font-semibold text-slate-200">{selectedFeature.title || selectedFeature.id}</h3>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {selectedFeature.status}
                  </span>
                </div>
                <pre className="bg-slate-900 border border-slate-800 p-4 rounded-lg font-mono text-xs text-indigo-300 overflow-x-auto whitespace-pre-wrap">
                  {selectedFeature.gherkin || '# No Gherkin feature text available.'}
                </pre>
              </>
            ) : (
              <div className="text-slate-500 text-sm">Select a feature from the list to review.</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
