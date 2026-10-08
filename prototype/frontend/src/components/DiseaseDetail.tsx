import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { diseasesApi } from '../services/api'

export function DiseaseDetail() {
  const { orphaId } = useParams<{ orphaId: string }>()

  const { data: disease, isLoading, error } = useQuery({
    queryKey: ['disease', orphaId],
    queryFn: () => diseasesApi.get(orphaId!),
    enabled: !!orphaId,
  })

  const { data: genes, isLoading: genesLoading } = useQuery({
    queryKey: ['disease-genes', orphaId],
    queryFn: () => diseasesApi.getGenes(orphaId!),
    enabled: !!orphaId,
  })

  const { data: pathways, isLoading: pathwaysLoading } = useQuery({
    queryKey: ['disease-pathways', orphaId],
    queryFn: () => diseasesApi.getPathways(orphaId!),
    enabled: !!orphaId,
  })

  if (error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Error loading disease</h2>
        <p className="text-gray-600">{(error as Error).message}</p>
      </div>
    )
  }

  if (!disease || isLoading) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Loading disease details...</h2>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">{disease.name}</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Overview</h2>
          <p className="text-gray-700">{disease.description || 'No description available.'}</p>
        </div>
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-medium text-gray-800 mb-1">ORPHA Code</h3>
            <p className="font-mono bg-gray-50 p-2 rounded">{disease.orpha_id}</p>
          </div>
          {disease.prevalence !== null && disease.prevalence !== undefined && (
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-1">Prevalence</h3>
              <p className="text-gray-700">
                {disease.prevalence.toFixed(2)} per 100k
                {disease.prevalence_category && (
                  <span className="ml-2 inline-block px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                    {disease.prevalence_category}
                  </span>
                )}
              </p>
            </div>
          )}
          {disease.unmet_need_score !== null && disease.unmet_need_score !== undefined && (
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-1">Unmet Need Score</h3>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 rounded-full transition-all"
                    style={{ width: `${Math.min(disease.unmet_need_score * 100, 100)}%` }}
                  />
                </div>
                <p className="text-gray-900 font-medium">{disease.unmet_need_score.toFixed(2)}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Genes */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">
          Associated Genes ({genes?.length || 0})
        </h2>
        {genesLoading ? (
          <p className="text-gray-500">Loading genes...</p>
        ) : !genes || genes.length === 0 ? (
          <p className="text-gray-500">No genes associated with this disease.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {genes.slice(0, 10).map((symbol) => (
              <span key={symbol} className="bg-blue-50 px-3 py-1.5 text-xs font-medium rounded text-blue-800">
                {symbol}
              </span>
            ))}
            {genes.length > 10 && (
              <span className="bg-gray-200 px-3 py-1.5 text-xs font-medium rounded">
                +{genes.length - 10} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Pathways */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">
          Associated Pathways ({pathways?.length || 0})
        </h2>
        {pathwaysLoading ? (
          <p className="text-gray-500">Loading pathways...</p>
        ) : !pathways || pathways.length === 0 ? (
          <p className="text-gray-500">No pathways associated with this disease.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {pathways.slice(0, 10).map((name) => (
              <span key={name} className="bg-gray-50 px-3 py-1.5 text-xs font-medium rounded text-gray-800">
                {name}
              </span>
            ))}
            {pathways.length > 10 && (
              <span className="bg-gray-200 px-3 py-1.5 text-xs font-medium rounded">
                +{pathways.length - 10} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Existing Treatments */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Existing Treatments</h2>
        {disease.existing_treatments.length > 0 ? (
          <ul className="list-disc list-inside space-y-1 text-gray-700">
            {disease.existing_treatments.map((treatment, index) => (
              <li key={index}>{treatment}</li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500">No existing treatments listed.</p>
        )}
      </div>

      {/* Phenotypes */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Phenotypes</h2>
        {disease.phenotypes.length > 0 ? (
          <ul className="list-disc list-inside space-y-1 text-gray-700">
            {disease.phenotypes.map((phenotype, index) => (
              <li key={index}>{phenotype}</li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500">No phenotypes listed.</p>
        )}
      </div>

      {/* Action Button */}
      <div className="mt-8">
        <a href={`/diseases/${disease.orpha_id}/candidates`} className="btn-primary px-6 py-2">
          Generate Repurposing Candidates
        </a>
      </div>
    </div>
  )
}
