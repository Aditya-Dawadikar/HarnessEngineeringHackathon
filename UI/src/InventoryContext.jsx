import { useConfig } from './useConfig.js'

function PriceBar({ vendor, buyer }) {
  const min = Math.min(vendor.floor_price, buyer.floor_price) * 0.9
  const max = Math.max(vendor.ceiling_price, buyer.ceiling_price) * 1.1
  const range = max - min

  const toPercent = (v) => `${((v - min) / range) * 100}%`

  const overlapLow  = Math.max(vendor.floor_price, buyer.floor_price)
  const overlapHigh = Math.min(vendor.ceiling_price, buyer.ceiling_price)
  const hasOverlap  = overlapLow <= overlapHigh

  return (
    <div className="price-bar-wrap">
      <div className="price-bar">
        <div
          className="price-bar__range price-bar__range--vendor"
          style={{ left: toPercent(vendor.floor_price), width: `calc(${toPercent(vendor.ceiling_price)} - ${toPercent(vendor.floor_price)})` }}
        />
        <div
          className="price-bar__range price-bar__range--buyer"
          style={{ left: toPercent(buyer.floor_price), width: `calc(${toPercent(buyer.ceiling_price)} - ${toPercent(buyer.floor_price)})` }}
        />
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

function VendorCard({ vendor }) {
  return (
    <div className="inv-card inv-card--vendor">
      <div className="inv-card__header">
        <span className="inv-card__role">VENDOR</span>
        <span className="inv-card__company">{vendor.company}</span>
      </div>
      <div className="inv-card__body">
        <Row label="Product"   value={`${vendor.product.name} (${vendor.product.id})`} />
        <Row label="Grade"     value={vendor.product.description} />
        <Row label="In stock"  value={`${vendor.stock_quantity.toLocaleString()} ${vendor.product.unit}`} />
        <Row label="Ask range" value={`$${vendor.floor_price.toFixed(2)} – $${vendor.ceiling_price.toFixed(2)}`} accent />
      </div>
      <div className="inv-card__note">Floor price is a hard lower bound — agent will not go below.</div>
    </div>
  )
}

function BuyerCard({ buyer }) {
  return (
    <div className="inv-card inv-card--buyer">
      <div className="inv-card__header">
        <span className="inv-card__role">BUYER</span>
        <span className="inv-card__company">{buyer.company}</span>
      </div>
      <div className="inv-card__body">
        <Row label="Target"    value={`${buyer.product.name} (${buyer.product.id})`} />
        <Row label="Quantity"  value={`${buyer.desired_quantity.toLocaleString()} ${buyer.product.unit}`} />
        <Row label="Budget"    value={`$${buyer.floor_price.toFixed(2)} – $${buyer.ceiling_price.toFixed(2)}`} accent />
        <Row label="Max spend" value={`$${(buyer.ceiling_price * buyer.desired_quantity).toLocaleString(undefined, { minimumFractionDigits: 2 })}`} />
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
  const { config, error } = useConfig()

  if (error) {
    return (
      <section className="inv-section">
        <h2 className="inv-section__title">Negotiation Context</h2>
        <p className="inv-error">Could not load config: {error}</p>
      </section>
    )
  }

  if (!config) {
    return (
      <section className="inv-section">
        <h2 className="inv-section__title">Negotiation Context</h2>
        <p className="inv-loading">Loading…</p>
      </section>
    )
  }

  return (
    <section className="inv-section">
      <h2 className="inv-section__title">Negotiation Context</h2>
      <div className="inv-cards">
        <VendorCard vendor={config.vendor} />
        <BuyerCard buyer={config.buyer} />
      </div>
      <PriceBar vendor={config.vendor} buyer={config.buyer} />
    </section>
  )
}
