// Relative base by default → requests go same-origin and are forwarded to the
// backend by the Vite dev proxy (see vite.config.js). Set VITE_API_BASE to hit
// a backend directly (e.g. a deployed URL).
const BASE = import.meta.env.VITE_API_BASE ?? ''

async function parseJSON(res, label) {
  const text = await res.text()
  if (!res.ok) throw new Error(`${label} failed: ${res.status}`)
  try {
    return JSON.parse(text)
  } catch {
    throw new Error(`${label}: server returned unexpected response (backend may be unreachable)`)
  }
}

export async function startNegotiation() {
  const res = await fetch(`${BASE}/negotiations/start`, { method: 'POST' })
  return parseJSON(res, 'start')
}

export async function fetchNegotiation(transactionId) {
  const res = await fetch(`${BASE}/negotiations/${transactionId}`)
  return parseJSON(res, 'fetch')
}
