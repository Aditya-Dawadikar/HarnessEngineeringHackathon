import { VENDOR_INVENTORY, BUYER_INVENTORY } from './inventoryData.js'

function PriceBar({ floor, ceiling, counterFloor, counterCeiling }) {
  const min = Math.min(floor, counterFloor) * 0.9
  const max = Math.max(ceiling, counterCeiling) * 1.1
  const range = max - min

  const toPercent = (v) => `${((v - min) / range) * 100}%`

  const overlapLow  = Math.max(floor, counterFloor)
  const overlapHigh = Math.min(ceiling, counterCeiling)
  const hasOverlap  = overlapLow <= overlapHigh

  return (
    <div className="price-bar-wrap">
      <div className="price-bar">
        {/* vendor range */}
        <div
          className="price-bar__range price-bar__range--vendor"
          style={{ left: toPercent(VENDOR_INVENTORY.floor_price), width: `calc(${toPercent(VENDOR_INVENTORY.ceiling_price)} - ${toPercent(VENDOR_INVENTORY.floor_price)})` }}
        />
        {/* buyer range */}
        <div
          className="price-bar__range price-bar__range--buyer"
          style={{ left: toPercent(BUYER_INVENTORY.floor_price), width: `calc(${toPercent(BUYER_INVENTORY.ceiling_price)} - ${toPercent(BUYER_INVENTORY.floor_price)})` }}
        />
        {/* overlap zone */}
        {hasOverlap && (
          <div
            className="price-bar__overlap"
            style={{ left: toPercent(overlapLow), width: `calc(${toPercent(overlapHigh)} - ${toPercent(overlapLow)})` }}
          />
        )}
      </div>
      <div className="price-bar__labels">
        <span>${min.toFixed(0)}</span>
        {hasOverlap && (
          <span className="price-bar__overlap-label">
            deal zone ${overlapLow.toFixed(2)}–${overlapHigh.toFixed(2)}
          </span>
        )}
        <span>${max.toFixed(0)}</span>
      </div>
    </div>
  )
}

function VendorCard() {
  const v = VENDOR_INVENTORY
  return (
    <div className="inv-card inv-card--vendor">
      <div className="inv-card__header">
        <span className="inv-card__role">VENDOR</span>
        <span className="inv-card__company">{v.company}</span>
      </div>
      <div className="inv-card__body">
        <Row label="Product"   value={`${v.product.name} (${v.product.id})`} />
        <Row label="Grade"     value={v.product.description} />
        <Row label="In stock"  value={`${v.stock_quantity.toLocaleString()} ${v.product.unit}`} />
        <Row label="Ask range" value={`$${v.floor_price.toFixed(2)} – $${v.ceiling_price.toFixed(2)}`} accent />
      </div>
      <div className="inv-card__note">Floor price is a hard lower bound — agent will not go below.</div>
    </div>
  )
}

function BuyerCard() {
  const b = BUYER_INVENTORY
  return (
    <div className="inv-card inv-card--buyer">
      <div className="inv-card__header">
        <span className="inv-card__role">BUYER</span>
        <span className="inv-card__company">{b.company}</span>
      </div>
      <div className="inv-card__body">
        <Row label="Target"    value={`${b.product.name} (${b.product.id})`} />
        <Row label="Quantity"  value={`${b.desired_quantity.toLocaleString()} ${b.product.unit}`} />
        <Row label="Budget"    value={`$${b.floor_price.toFixed(2)} – $${b.ceiling_price.toFixed(2)}`} accent />
        <Row label="Max spend" value={`$${(b.ceiling_price * b.desired_quantity).toLocaleString(undefined, { minimumFractionDigits: 2 })}`} />
      </div>
      <div className="inv-card__note">Ceiling price is a hard upper bound — agent will not exceed.</div>
    </div>
  )
}

function Row({ label, value, accent }) {
  return (
    <div className="inv-row">
      <span className="inv-row__label">{label}</span>
      <span className={`inv-row__value${accent ? ' inv-row__value--accent' : ''}`}>{value}</span>
    </div>
  )
}

export function InventoryContext() {
  return (
    <section className="inv-section">
      <h2 className="inv-section__title">Negotiation Context</h2>
      <div className="inv-cards">
        <VendorCard />
        <BuyerCard />
      </div>
      <PriceBar
        floor={VENDOR_INVENTORY.floor_price}
        ceiling={VENDOR_INVENTORY.ceiling_price}
        counterFloor={BUYER_INVENTORY.floor_price}
        counterCeiling={BUYER_INVENTORY.ceiling_price}
      />
    </section>
  )
}
