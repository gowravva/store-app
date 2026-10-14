import { useState, useEffect } from 'react'

// This app's own backend (the Store API). It owns the products, stock and
// orders — everything lives in one app.
//
// Baked in at BUILD time from VITE_API_URL (see the frontend Dockerfile).
// Falls back to localhost so `npm run dev` still works with no setup.
const API = import.meta.env.VITE_API_URL || 'http://localhost:8001'

const money = (n) => '$' + Number(n).toFixed(2)

// Decide the availability label shown as a colored pill.
function stockStatus(q) {
  if (q === 0) return { label: 'Sold out', tone: 'danger' }
  if (q <= 5) return { label: `Only ${q} left`, tone: 'warn' }
  return { label: 'In stock', tone: 'ok' }
}

export default function App() {
  const [catalog, setCatalog] = useState([])
  const [orders, setOrders] = useState([])
  const [online, setOnline] = useState(true)
  const [busy, setBusy] = useState(null) // id of the product currently being bought
  const [toast, setToast] = useState(null) // { tone, text }

  const flash = (tone, text) => {
    setToast({ tone, text })
    setTimeout(() => setToast(null), 2600)
  }

  const load = async () => {
    try {
      const [c, o] = await Promise.all([
        fetch(`${API}/catalog`).then((r) => r.json()),
        fetch(`${API}/orders`).then((r) => r.json()),
      ])
      setCatalog(c)
      setOrders(o)
      setOnline(true)
    } catch {
      setOnline(false)
    }
  }

  // Load once, then auto-refresh every 2s so stock changes appear live.
  useEffect(() => {
    load()
    const timer = setInterval(load, 2000)
    return () => clearInterval(timer)
  }, [])

  const buy = async (product) => {
    setBusy(product.id)
    try {
      const res = await fetch(`${API}/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: product.id, quantity: 1 }),
      })
      if (res.ok) {
        flash('ok', `Sold 1 × ${product.name}`)
      } else {
        const err = await res.json().catch(() => ({}))
        flash('danger', err.detail || 'Could not complete the sale')
      }
    } catch {
      flash('danger', 'Store backend offline')
    } finally {
      setBusy(null)
      load()
    }
  }

  // KPI numbers
  const productsAvailable = catalog.filter((p) => p.quantity > 0).length
  const ordersCount = orders.length
  const unitsSold = orders.reduce((s, o) => s + o.quantity, 0)
  const revenue = orders.reduce((s, o) => s + o.total, 0)

  return (
    <div className="app">
      {/* Top bar */}
      <header className="topbar">
        <div className="brand">
          <span className="logo">🛍️</span>
          <div>
            <div className="brand-name">The Store</div>
            <div className="brand-sub">Application 1 · shop &amp; checkout</div>
          </div>
        </div>
        <div className={`status ${online ? 'up' : 'down'}`}>
          <span className="dot" />
          {online ? 'Connected · :8001' : 'Backend offline'}
        </div>
      </header>

      <main className="container">
        {/* KPI tiles */}
        <section className="kpis">
          <Kpi label="Products for sale" value={productsAvailable} />
          <Kpi label="Orders" value={ordersCount} />
          <Kpi label="Units sold" value={unitsSold} />
          <Kpi label="Revenue" value={money(revenue)} />
        </section>

        {/* Catalog */}
        <section className="card">
          <div className="card-head">
            <div>
              <h2>Catalog</h2>
              <p className="muted">Buying a product reduces its stock instantly.</p>
            </div>
          </div>

          <div className="grid">
            {catalog.length === 0 && (
              <div className="empty">Catalog is empty — add a product via the API (POST /products).</div>
            )}
            {catalog.map((p) => {
              const s = stockStatus(p.quantity)
              const soldOut = p.quantity === 0
              return (
                <div className="product" key={p.id}>
                  <div className="product-top">
                    <div className="pname">{p.name}</div>
                    <span className={`pill ${s.tone}`}>{s.label}</span>
                  </div>
                  <div className="price mono">{money(p.price)}</div>
                  <button
                    className="btn primary full"
                    disabled={soldOut || busy === p.id}
                    onClick={() => buy(p)}
                  >
                    {busy === p.id ? 'Selling…' : soldOut ? 'Sold out' : 'Buy 1'}
                  </button>
                </div>
              )
            })}
          </div>
        </section>

        {/* Recent orders */}
        <section className="card">
          <div className="card-head">
            <div>
              <h2>Recent orders</h2>
              <p className="muted">Every sale is saved in the Store's own database (store.db).</p>
            </div>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th className="num">#</th>
                  <th>Product</th>
                  <th className="right">Qty</th>
                  <th className="right">Unit</th>
                  <th className="right">Total</th>
                  <th>When</th>
                </tr>
              </thead>
              <tbody>
                {orders.length === 0 && (
                  <tr><td colSpan="6" className="empty">No sales yet. Buy something above.</td></tr>
                )}
                {orders.map((o) => (
                  <tr key={o.id}>
                    <td className="num muted">{o.id}</td>
                    <td className="pname">{o.product_name}</td>
                    <td className="right mono">{o.quantity}</td>
                    <td className="right mono">{money(o.unit_price)}</td>
                    <td className="right mono">{money(o.total)}</td>
                    <td className="muted">{o.created_at.replace('T', ' ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>

      {toast && <div className={`toast ${toast.tone}`}>{toast.text}</div>}
    </div>
  )
}

function Kpi({ label, value, tone }) {
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value ${tone || ''}`}>{value}</div>
    </div>
  )
}
