// Local mock of the Shared API Contract for development without the backend.
// Shapes mirror the REAL backend (Backend/app/graph.py): agent messages carry a
// raw "[OFFER price=.. quantity=.. action=..]" tag, and the invoice uses the
// keys produced by payment_request → payment_authorization → generate_invoice.
// Enable with VITE_USE_MOCK=true.

let _tick = 0

const SCRIPT = [
  { sender: 'BuyerAgent',  price: 7.00, qty: 200, action: 'COUNTER', lead: "I'd like to buy 200 units at $7.00 per unit." },
  { sender: 'VendorAgent', price: 9.50, qty: 200, action: 'COUNTER', lead: 'I can supply 200 units at $9.50 per unit.' },
  { sender: 'BuyerAgent',  price: 8.25, qty: 200, action: 'COUNTER', lead: "I'd like to buy 200 units at $8.25 per unit." },
  { sender: 'VendorAgent', price: 8.88, qty: 200, action: 'COUNTER', lead: 'I can supply 200 units at $8.88 per unit.' },
  { sender: 'BuyerAgent',  price: 8.57, qty: 200, action: 'COUNTER', lead: "I'd like to buy 200 units at $8.57 per unit." },
  { sender: 'VendorAgent', price: 8.57, qty: 200, action: 'ACCEPT',  lead: 'I can supply 200 units at $8.57 per unit.' },
]

const AGREED_PRICE = 8.57
const AGREED_QTY = 200

function scriptMessage({ sender, price, qty, action, lead }) {
  return {
    sender,
    text: `${lead} [OFFER price=${price.toFixed(2)} quantity=${qty} action=${action}]`,
    extracted_price: price,
    extracted_quantity: qty,
    timestamp: new Date().toISOString(),
  }
}

function buildInvoice() {
  const total = Number((AGREED_PRICE * AGREED_QTY).toFixed(2))
  return {
    transaction_id: 'mock-0000-0001',
    buyer_agent_id: 'BuyerAgent',
    product_id: 'PROD-1001',
    agreed_unit_price: AGREED_PRICE,
    quantity: AGREED_QTY,
    total_amount: total,
    payment_intent_id: 'pi_mock_0000000000000000000001',
    payment_status: 'succeeded',
    payment_method_token: 'tok_mock_visa',
    authorized_amount: total,
    unit_price: AGREED_PRICE,
  }
}

let _state = null

export function mockConfig() {
  return Promise.resolve({
    vendor: {
      agent_id: 'VendorAgent',
      company: 'Acme Supplies Co.',
      product: { id: 'PROD-1001', name: 'Industrial Widget', description: 'Heavy-duty steel widget, grade A', unit: 'pcs' },
      stock_quantity: 500,
      floor_price: 8.00,
      ceiling_price: 12.00,
    },
    buyer: {
      agent_id: 'BuyerAgent',
      company: 'BuildCorp Ltd.',
      product: { id: 'PROD-1001', name: 'Industrial Widget', unit: 'pcs' },
      desired_quantity: 200,
      floor_price: 7.00,
      ceiling_price: 10.00,
    },
  })
}

export function mockStart() {
  _tick = 0
  _state = {
    transaction_id: 'mock-0000-0001',
    status: 'NEGOTIATING',
    turn: 0,
    messages: [],
    invoice: null,
  }
  return Promise.resolve({ transaction_id: _state.transaction_id })
}

export function mockFetch() {
  if (!_state) return Promise.reject(new Error('no active negotiation'))
  if (_tick < SCRIPT.length) {
    _state.messages = [..._state.messages, scriptMessage(SCRIPT[_tick])]
    _state.turn = _tick + 1
    // last script entry is the ACCEPT → deal closes and payment settles
    _state.status = _tick === SCRIPT.length - 1 ? 'FULFILLED' : 'NEGOTIATING'
    _state.invoice = _state.status === 'FULFILLED' ? buildInvoice() : null
    _tick += 1
  }
  return Promise.resolve({ ..._state, messages: [..._state.messages] })
}
