import { api, buildQuery } from './api'
import type { Category, Paginated, Product, Warehouse } from '../types'

export function getCategories(params: { page?: number; page_size?: number; search?: string } = {}) {
  return api.get<Paginated<Category>>(`/categories${buildQuery(params)}`)
}

export function createCategory(payload: { name: string; description?: string | null }) {
  return api.post<Category>('/categories', payload)
}

export function updateCategory(id: number, payload: { name?: string; description?: string | null }) {
  return api.patch<Category>(`/categories/${id}`, payload)
}

export function getProducts(
  params: {
    page?: number
    page_size?: number
    search?: string
    category_id?: number
    status?: string
  } = {},
) {
  return api.get<Paginated<Product>>(`/products${buildQuery(params)}`)
}

export function getProductOptions() {
  return api.get<Product[]>('/products/options')
}

export function createProduct(payload: object) {
  return api.post<Product>('/products', payload)
}

export function updateProduct(id: number, payload: object) {
  return api.patch<Product>(`/products/${id}`, payload)
}

export function getWarehouses(
  params: { page?: number; page_size?: number; search?: string; status?: string } = {},
) {
  return api.get<Paginated<Warehouse>>(`/warehouses${buildQuery(params)}`)
}

export function getWarehouseOptions() {
  return api.get<Warehouse[]>('/warehouses/options')
}

export function createWarehouse(payload: object) {
  return api.post<Warehouse>('/warehouses', payload)
}

export function updateWarehouse(id: number, payload: object) {
  return api.patch<Warehouse>(`/warehouses/${id}`, payload)
}
