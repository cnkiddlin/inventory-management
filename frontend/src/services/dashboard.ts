import { api } from './api'
import type { DashboardData, HealthData } from '../types'

export function getDashboard() {
  return api.get<DashboardData>('/dashboard')
}

export function getHealth() {
  return api.get<HealthData>('/health')
}

