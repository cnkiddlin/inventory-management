import { api, buildQuery } from './api'
import type {
  InboundOrder,
  OutboundOrder,
  Paginated,
  StockTransfer,
} from '../types'

export function getInboundOrders(
  params: { page?: number; page_size?: number; search?: string; status?: string; warehouse_id?: number } = {},
) {
  return api.get<Paginated<InboundOrder>>(`/inbound-orders${buildQuery(params)}`)
}

export function createInboundOrder(payload: object) {
  return api.post<InboundOrder>('/inbound-orders', payload)
}

export function confirmInboundOrder(id: number) {
  return api.post<InboundOrder>(`/inbound-orders/${id}/confirm`)
}

export function getOutboundOrders(
  params: { page?: number; page_size?: number; search?: string; status?: string; warehouse_id?: number } = {},
) {
  return api.get<Paginated<OutboundOrder>>(`/outbound-orders${buildQuery(params)}`)
}

export function createOutboundOrder(payload: object) {
  return api.post<OutboundOrder>('/outbound-orders', payload)
}

export function confirmOutboundOrder(id: number) {
  return api.post<OutboundOrder>(`/outbound-orders/${id}/confirm`)
}

export function getTransfers(
  params: { page?: number; page_size?: number; search?: string; status?: string; warehouse_id?: number } = {},
) {
  return api.get<Paginated<StockTransfer>>(`/stock-transfers${buildQuery(params)}`)
}

export function createTransfer(payload: object) {
  return api.post<StockTransfer>('/stock-transfers', payload)
}

export function completeTransfer(id: number) {
  return api.post<StockTransfer>(`/stock-transfers/${id}/complete`)
}
