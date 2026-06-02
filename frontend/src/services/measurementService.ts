import { apiGet, apiPost } from './api'

export type BodyMeasurement = {
  id: number
  recorded_at: string
  body_weight_lbs: number
  waist_inches: number
}

export type BodyMeasurementInput = {
  recorded_at: string
  body_weight_lbs: number
  waist_inches: number
}

export function fetchMeasurements(): Promise<BodyMeasurement[]> {
  return apiGet<BodyMeasurement[]>('/measurements')
}

export function createMeasurement(
  input: BodyMeasurementInput,
): Promise<BodyMeasurement> {
  return apiPost<BodyMeasurement, BodyMeasurementInput>('/measurements', input)
}
