export function InvoiceBlock({ invoice }) {
  if (!invoice) return null

  const rows = [
    ['Transaction ID',  invoice.transaction_id],
    ['Product ID',      invoice.product_id],
    ['Unit Price',      `$${Number(invoice.agreed_unit_price).toFixed(2)}`],
    ['Quantity',        invoice.quantity],
    ['Total',           `$${Number(invoice.total_amount).toFixed(2)}`],
    ['Issued',          new Date(invoice.issued_at).toLocaleString()],
  ]

  return (
    <div className="invoice">
      <h2 className="invoice__title">Invoice</h2>
      <table className="invoice__table">
        <tbody>
          {rows.map(([label, value]) => (
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
