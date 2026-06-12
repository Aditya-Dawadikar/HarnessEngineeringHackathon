import { useEffect, useRef } from 'react'
import { TypingIndicator } from './TypingIndicator.jsx'

const SENDER_LABEL = {
  VendorAgent: 'VENDOR',
  BuyerAgent:  'BUYER',
  System:      'SYS',
}

// Backend appends a structured tag to each agent message, e.g.
// "[OFFER price=8.57 quantity=200 action=ACCEPT]". Strip it for display and
// pull the action out so we can show it as a chip.
const OFFER_TAG = /\[OFFER price=[0-9.]+ quantity=[0-9]+ action=(ACCEPT|COUNTER|REJECT)\]/

function parseOffer(text) {
  const match = text.match(OFFER_TAG)
  return {
    clean: text.replace(OFFER_TAG, '').trim(),
    action: match ? match[1] : null,
  }
}

function fmt(val, prefix) {
  if (val == null) return null
  return `${prefix}${Number(val).toFixed(2)}`
}

function Message({ msg }) {
  const label = SENDER_LABEL[msg.sender] ?? msg.sender
  const { clean, action } = parseOffer(msg.text)
  const price = fmt(msg.extracted_price, '$')
  const qty   = msg.extracted_quantity != null ? `×${msg.extracted_quantity}` : null

  return (
    <div className={`msg msg--${msg.sender.toLowerCase()}`}>
      <span className="msg__sender">[{label}]</span>
      <span className="msg__text">
        {clean}
        {action && <span className={`msg__action msg__action--${action.toLowerCase()}`}>{action}</span>}
      </span>
      {(price || qty) && (
        <span className="msg__meta">
          {[price, qty].filter(Boolean).join('  ')}
        </span>
      )}
      <span className="msg__ts">{new Date(msg.timestamp).toLocaleTimeString()}</span>
    </div>
  )
}

export function MessageLog({ messages, state, polling }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, polling])

  const isEmpty = !messages?.length

  return (
    <div className={`log${isEmpty ? ' log--empty-state' : ''}`}>
      {isEmpty ? (
        <div className="log-empty">
          <div className="log-empty__icon">⟳</div>
          <p className="log-empty__text">
            {polling ? 'Waiting for agents to start…' : 'Hit Start Negotiation to begin.'}
          </p>
        </div>
      ) : (
        <>
          {messages.map((m, i) => <Message key={i} msg={m} />)}
          <TypingIndicator state={state} polling={polling} />
          <div ref={bottomRef} />
        </>
      )}
    </div>
  )
}
