const BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

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
