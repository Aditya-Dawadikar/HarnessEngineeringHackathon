// Local mock of the Shared API Contract for development before BE-6 is ready.
// Import useNegotiation from useNegotiation.js — it switches to real API when
// VITE_USE_MOCK is not set to "true".

let _tick = 0

const SCRIPT = [
  { sender: 'BuyerAgent',  text: 'I would like 50 units at $10.00 each.',      extracted_price: 10.00,  extracted_quantity: 50  },
  { sender: 'VendorAgent', text: 'Our floor is $14.00. Best I can do is $14.',  extracted_price: 14.00,  extracted_quantity: 50  },
  { sender: 'BuyerAgent',  text: 'I can go up to $12.50.',                      extracted_price: 12.50,  extracted_quantity: 50  },
  { sender: 'VendorAgent', text: 'Meet me at $13.00 and we have a deal.',       extracted_price: 13.00,  extracted_quantity: 50  },
  { sender: 'BuyerAgent',  text: 'Agreed. $13.00 for 50 units.',               extracted_price: 13.00,  extracted_quantity: 50  },
  { sender: 'System',      text: 'Agreement reached. Initiating payment.',      extracted_price: null,   extracted_quantity: null },
  { sender: 'System',      text: 'Payment authorized. Invoice generated.',      extracted_price: null,   extracted_quantity: null },
]

function statusAt(tick) {
  if (tick < 5) return 'NEGOTIATING'
  if (tick === 5) return 'AGREEMENT'
  if (tick === 6) return 'PAYMENT_PENDING'
  return 'FULFILLED'
}

function invoiceAt(tick) {
  if (tick < 7) return null
  return {
    transaction_id: 'mock-0000-0001',
    product_id: 'PROD-001',
    agreed_unit_price: 13.00,
    quantity: 50,
    total_amount: 650.00,
    issued_at: new Date().toISOString(),
  }
}

let _state = null

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
    const { sender, text, extracted_price, extracted_quantity } = SCRIPT[_tick]
    _state.messages = [
      ..._state.messages,
      { sender, text, extracted_price, extracted_quantity, timestamp: new Date().toISOString() },
    ]
    _state.turn = _tick + 1
    _state.status = statusAt(_tick)
    _state.invoice = invoiceAt(_tick)
    _tick += 1
  }
  return Promise.resolve({ ..._state, messages: [..._state.messages] })
}
