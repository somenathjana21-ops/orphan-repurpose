import type { FAERSSignal } from '../types'

export interface ADMETPrediction {
  endpoint: string
  name: string
  value: number
  unit: string
  classification: 'pass' | 'caution' | 'fail'
}

export interface SafetyAssessment {
  drug_id: string
  drug_name: string
  faers_signals: FAERSSignal[]
  admet_predictions: Record<string, number>
  admet_classifications: Record<string, 'pass' | 'caution' | 'fail'>
  contraindications: string[]
  overall: 'pass' | 'caution' | 'fail'
}
