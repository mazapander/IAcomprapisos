import { useState } from 'react'
import { Building2, Menu, X } from 'lucide-react'

import { TOOLS } from '../app/toolCatalog'
import type { ToolId } from '../types'

export default function SiteHeader({ onSelect, onHome, onMethod }: { onSelect: (id: ToolId) => void; onHome: () => void; onMethod: () => void }) {
  const [mobileMenu, setMobileMenu] = useState(false)

  function select(id: ToolId) {
    setMobileMenu(false)
    onSelect(id)
  }

  return (
    <header className="site-header">
      <button className="brand" type="button" onClick={onHome} aria-label="Ir al inicio">
        <span><Building2 size={21} /></span>
        <strong>IA Compra Pisos</strong>
      </button>
      <nav className={mobileMenu ? 'is-open' : ''} aria-label="Navegación principal">
        {TOOLS.map((tool) => (
          <button key={tool.id} type="button" onClick={() => select(tool.id)}>{tool.title}</button>
        ))}
        <button type="button" onClick={() => { setMobileMenu(false); onMethod() }}>Cómo funciona</button>
      </nav>
      <button className="button button--small button--dark desktop-cta" onClick={() => select('mortgage')}>
        Comparar ofertas
      </button>
      <button
        className="menu-button"
        type="button"
        onClick={() => setMobileMenu((value) => !value)}
        aria-label="Abrir menú"
      >
        {mobileMenu ? <X /> : <Menu />}
      </button>
    </header>
  )
}
