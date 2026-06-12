import { useEffect, useRef } from 'react'

const SENDER_LABEL = {
  VendorAgent: 'VENDOR',
  BuyerAgent:  'BUYER',
  System:      'SYS',
}

function fmt(val, prefix) {
  if (val == null) return null
  return `${prefix}${Number(val).toFixed(2)}`
}

function Message({ msg }) {
  const label = SENDER_LABEL[msg.sender] ?? msg.sender
  const price = fmt(msg.extracted_price, '$')
  const qty   = msg.extracted_quantity != null ? `×${msg.extracted_quantity}` : null

  return (
    <div className={`msg msg--${msg.sender.toLowerCase()}`}>
      <span className="msg__sender">[{label}]</span>
      <span className="msg__text">{msg.text}</span>
      {(price || qty) && (
        <span className="msg__meta">
          {[price, qty].filter(Boolean).join('  ')}
        </span>
      )}
      <span className="msg__ts">{new Date(msg.timestamp).toLocaleTimeString()}</span>
    </div>
  )
}

export function MessageLog({ messages }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (!messages?.length) return <p className="log-empty">No messages yet.</p>

  return (
    <div className="log">
      {messages.map((m, i) => <Message key={i} msg={m} />)}
      <div ref={bottomRef} />
    </div>
  )
}
