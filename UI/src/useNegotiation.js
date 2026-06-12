import { useState, useEffect, useRef, useCallback } from 'react'
import { startNegotiation, fetchNegotiation } from './api.js'
import { mockStart, mockFetch } from './mock.js'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export function useNegotiation() {
  const [state, setState] = useState(null)   // full negotiation object
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [polling, setPolling] = useState(false)
  const intervalRef = useRef(null)
  const txIdRef = useRef(null)

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setPolling(false)
  }, [])

  const poll = useCallback(async () => {
    try {
      const data = USE_MOCK
        ? await mockFetch()
        : await fetchNegotiation(txIdRef.current)
      setState(data)
      if (data.status === 'FULFILLED' || data.status === 'TERMINATED') {
        stopPolling()
      }
    } catch (err) {
      setError(err.message)
      stopPolling()
    }
  }, [stopPolling])

  const start = useCallback(async () => {
    setError(null)
    setLoading(true)
    setState(null)
    stopPolling()
    try {
      const { transaction_id } = USE_MOCK
        ? await mockStart()
        : await startNegotiation()
      txIdRef.current = transaction_id
      setPolling(true)
      // immediate first fetch, then every 1 s
      await poll()
      intervalRef.current = setInterval(poll, 1000)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [poll, stopPolling])

  useEffect(() => stopPolling, [stopPolling])

  return { state, error, loading, polling, start }
}
