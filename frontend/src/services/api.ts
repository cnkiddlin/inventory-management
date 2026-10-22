const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export class ApiError extends Error {
  status: number
  code: string
  details: unknown

  constructor(message: string, status: number, code = 'request_failed', details: unknown = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

type QueryValue = string | number | boolean | null | undefined

export function buildQuery(params: Record<string, QueryValue>): string {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value))
    }
  })
  const text = query.toString()
  return text ? `?${text}` : ''
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
  })

  const contentType = response.headers.get('content-type') || ''
  const body = contentType.includes('application/json') ? await response.json() : null
  if (!response.ok) {
    const error = body?.error
    throw new ApiError(
      error?.message || `请求失败 (${response.status})`,
      response.status,
      error?.code,
      error?.details,
    )
  }
  return body as T
}

export const api = {
  get<T>(path: string): Promise<T> {
    return request<T>(path)
  },
  post<T>(path: string, payload?: unknown): Promise<T> {
    return request<T>(path, { method: 'POST', body: payload === undefined ? undefined : JSON.stringify(payload) })
  },
  patch<T>(path: string, payload: unknown): Promise<T> {
    return request<T>(path, { method: 'PATCH', body: JSON.stringify(payload) })
  },
}

export const API_BASE_URL = API_BASE
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

