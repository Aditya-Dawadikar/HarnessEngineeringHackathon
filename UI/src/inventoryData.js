// Dummy inventory context — replace with real API fetch when backend is ready.
// Shape must match Backend/app/config.py VENDOR_CONFIG / BUYER_CONFIG.

export const VENDOR_INVENTORY = {
  agent_id: 'VendorAgent',
  company:  'Acme Supplies Co.',
  product: {
    id:          'PROD-1001',
    name:        'Industrial Widget',
    description: 'Heavy-duty steel widget, grade A',
    unit:        'pcs',
  },
  stock_quantity: 500,
  floor_price:    8.00,   // will not go below this
  ceiling_price:  12.00,  // opening ask price
}

export const BUYER_INVENTORY = {
  agent_id: 'BuyerAgent',
  company:  'BuildCorp Ltd.',
  product: {
    id:   'PROD-1001',
    name: 'Industrial Widget',
    unit: 'pcs',
  },
  desired_quantity:  200,
  floor_price:       7.00,  // opening bid price
  ceiling_price:     10.00, // will not go above this
}
