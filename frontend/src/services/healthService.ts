import { apiGet } from './api'

export type HealthStatus = {
  status: string
}

export function fetchHealth(): Promise<HealthStatus> {
  return apiGet<HealthStatus>('/health')
}
