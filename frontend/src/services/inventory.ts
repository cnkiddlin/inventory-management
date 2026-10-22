import { api, buildQuery } from './api'
import type {
  InventoryAlert,
  InventoryRecord,
  InventoryTransaction,
  Paginated,
} from '../types'

export function getInventory(
  params: {
    page?: number
    page_size?: number
    search?: string
    product_id?: number
    warehouse_id?: number
    category_id?: number
    status?: string
  } = {},
) {
  return api.get<Paginated<InventoryRecord>>(`/inventory${buildQuery(params)}`)
}

export function getAlerts(
  params: { page?: number; page_size?: number; search?: string; status?: string } = {},
) {
  return api.get<Paginated<InventoryAlert>>(`/inventory/alerts${buildQuery(params)}`)
}

export function getTransactions(
  params: {
    page?: number
    page_size?: number
    search?: string
    product_id?: number
    warehouse_id?: number
    transaction_type?: string
    date_from?: string
    date_to?: string
  } = {},
) {
  return api.get<Paginated<InventoryTransaction>>(`/inventory/transactions${buildQuery(params)}`)
}
