import { Building2 } from 'lucide-react'

export default function SiteFooter({ onPrivacy }: { onPrivacy: () => void }) {
  return (
    <footer className="site-footer">
      <div className="brand brand--footer"><span><Building2 size={19} /></span><strong>IA Compra Pisos</strong></div>
      <p>Más información para quien toma la decisión más importante.</p>
      <div>
        <button type="button" onClick={onPrivacy}>Privacidad y medición</button>
        <a href="/docs">API</a>
      </div>
    </footer>
  )
}
