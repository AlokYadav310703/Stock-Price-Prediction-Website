import { useEffect, useRef, useState } from 'react'

/**
 * Runs an async fetcher on mount (and whenever deps change), exposing
 * { data, loading, error, reload }. Every page uses this so loading /
 * error / empty states are handled consistently.
 */
export function useAsync(fetcher, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const mounted = useRef(true)

  const run = () => {
    setLoading(true)
    setError(null)
    fetcher()
      .then((res) => {
        if (mounted.current) setData(res)
      })
      .catch((err) => {
        if (mounted.current) setError(err?.message || 'Something went wrong.')
      })
      .finally(() => {
        if (mounted.current) setLoading(false)
      })
  }

  useEffect(() => {
    mounted.current = true
    run()
    return () => {
      mounted.current = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, loading, error, reload: run }
}
