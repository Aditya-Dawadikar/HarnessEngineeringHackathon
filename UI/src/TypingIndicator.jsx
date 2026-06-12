const SENDER_LABEL = { VendorAgent: 'VENDOR', BuyerAgent: 'BUYER' }

export function TypingIndicator({ state, polling }) {
  if (!polling || !state) return null
  if (state.status !== 'NEGOTIATING') return null

  // Figure out whose turn is next based on who sent the last message
  const last = state.messages?.at(-1)
  const nextSender = last?.sender === 'BuyerAgent' ? 'VendorAgent' : 'BuyerAgent'
  const label = SENDER_LABEL[nextSender]

  return (
    <div className="typing">
      <span className="typing__label">[{label}]</span>
      <span className="typing__text">thinking</span>
      <span className="typing__dots">
        <span /><span /><span />
      </span>
    </div>
  )
}
