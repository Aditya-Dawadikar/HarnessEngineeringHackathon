// Relative base by default → requests go same-origin and are forwarded to the
// backend by the Vite dev proxy (see vite.config.js). Set VITE_API_BASE to hit
// a backend directly (e.g. a deployed URL).
const BASE = import.meta.env.VITE_API_BASE ?? ''

export async function startNegotiation() {
  const res = await fetch(`${BASE}/negotiations/start`, { method: 'POST' })
  if (!res.ok) throw new Error(`start failed: ${res.status}`)
  return res.json() // { transaction_id }
}

export async function fetchNegotiation(transactionId) {
  const res = await fetch(`${BASE}/negotiations/${transactionId}`)
  if (!res.ok) throw new Error(`fetch failed: ${res.status}`)
  return res.json()
}
