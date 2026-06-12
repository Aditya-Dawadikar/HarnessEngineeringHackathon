import { useNegotiation } from './useNegotiation.js'
import { MessageLog } from './MessageLog.jsx'
import { InvoiceBlock } from './InvoiceBlock.jsx'
import { InventoryContext } from './InventoryContext.jsx'
import './App.css'

export default function App() {
  const { state, error, loading, start } = useNegotiation()

  return (
    <main>
      <h1>Agentic Negotiation Platform</h1>

      <InventoryContext />

      <div className="toolbar">
        <button className="btn-start" onClick={start} disabled={loading}>
          {loading ? 'Starting…' : 'Start Negotiation'}
        </button>
        {state && <span className={`badge badge--${state.status.toLowerCase()}`}>{state.status}</span>}
        {state && <span className="turn-counter">turn {state.turn}</span>}
      </div>

      {error && <p className="error">Error: {error}</p>}

      <MessageLog messages={state?.messages} />

      {state?.status === 'FULFILLED' && <InvoiceBlock invoice={state.invoice} />}
    </main>
  )
}
