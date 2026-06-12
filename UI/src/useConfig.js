import { useState, useEffect } from 'react'
import { fetchConfig } from './api.js'
import { mockConfig } from './mock.js'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export function useConfig() {
  const [config, setConfig] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const load = USE_MOCK ? mockConfig : fetchConfig
    load()
      .then(setConfig)
      .catch((err) => setError(err.message))
  }, [])

  return { config, error }
}
