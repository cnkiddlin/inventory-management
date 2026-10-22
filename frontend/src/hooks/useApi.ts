import { useCallback, useEffect, useRef, useState } from 'react'
import type { DependencyList } from 'react'


export function useApi<T>(loader: () => Promise<T>, deps: DependencyList) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const loaderRef = useRef(loader)
  loaderRef.current = loader

  const reload = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await loaderRef.current()
      setData(result)
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void reload()
    // The dependency list is intentionally supplied by each caller.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, loading, error, reload }
}

