import { useNegotiation } from './useNegotiation.js'
import { MessageLog } from './MessageLog.jsx'
import { InvoiceBlock } from './InvoiceBlock.jsx'
import { InventoryContext } from './InventoryContext.jsx'
import './App.css'

export default function App() {
  const { state, error, loading, polling, start } = useNegotiation()

  const terminated = state?.status === 'TERMINATED'

  return (
    <main>
      <h1>Agentic Negotiation Platform</h1>

      <InventoryContext />

      <div className="toolbar">
        <button className="btn-start" onClick={start} disabled={loading || polling}>
          {loading ? 'Starting…' : 'Start Negotiation'}
        </button>
        {state && <span className={`badge badge--${state.status.toLowerCase()}`}>{state.status}</span>}
        {state && <span className="turn-counter">turn {state.turn}</span>}
      </div>

      {error && <p className="error">Error: {error}</p>}

      {terminated && (
        <div className="terminated-banner">
          <span className="terminated-banner__icon">✕</span>
          <div>
            <strong>Deal not reached</strong>
            <p>The negotiation was terminated — agents could not agree within the price bounds or turn limit.</p>
          </div>
        </div>
      )}

      <MessageLog messages={state?.messages} state={state} polling={polling} />

      {state?.status === 'FULFILLED' && <InvoiceBlock invoice={state.invoice} />}
    </main>
  )
}
