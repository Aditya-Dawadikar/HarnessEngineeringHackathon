export function InvoiceBlock({ invoice }) {
  if (!invoice) return null

  // Backend builds the invoice across payment_request → payment_authorization
  // → generate_invoice. `agreed_unit_price` and `unit_price` carry the same
  // value; prefer agreed_unit_price, fall back to unit_price.
  const unitPrice = invoice.agreed_unit_price ?? invoice.unit_price

  const rows = [
    ['Transaction ID', invoice.transaction_id],
    ['Product ID',     invoice.product_id],
    ['Unit Price',     unitPrice != null ? `$${Number(unitPrice).toFixed(2)}` : null],
    ['Quantity',       invoice.quantity],
    ['Total',          invoice.total_amount != null ? `$${Number(invoice.total_amount).toFixed(2)}` : null],
    ['Payment Intent', invoice.payment_intent_id],
  ]

  const paid = invoice.payment_status === 'succeeded'

  return (
    <div className="invoice">
      <div className="invoice__head">
        <h2 className="invoice__title">Invoice</h2>
        {invoice.payment_status && (
          <span className={`invoice__status${paid ? ' invoice__status--paid' : ''}`}>
            {invoice.payment_status}
          </span>
        )}
      </div>
      <table className="invoice__table">
        <tbody>
          {rows.filter(([, v]) => v != null).map(([label, value]) => (
            <tr key={label}>
              <td className="invoice__label">{label}</td>
              <td className="invoice__value">{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
