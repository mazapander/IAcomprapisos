import { useEffect, useState } from 'react'
import { BarChart3, ShieldCheck, X } from 'lucide-react'

import { analyticsConsent, setAnalyticsConsent, track } from '../api'

export default function ConsentBanner({ settingsSignal = 0 }: { settingsSignal?: number }) {
  const [visible, setVisible] = useState(() => !analyticsConsent())
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (settingsSignal > 0) setVisible(true)
  }, [settingsSignal])

  async function choose(choice: 'accepted' | 'rejected') {
    setSaving(true)
    try {
      await setAnalyticsConsent(choice)
      setVisible(false)
      if (choice === 'accepted') void track('page_view', { source: 'consent' })
    } finally {
      setSaving(false)
    }
  }

  if (!visible) return null

  return (
    <aside className="consent-banner" aria-label="Preferencias de medición">
      <button className="consent-close" type="button" onClick={() => setVisible(false)} aria-label="Cerrar">
        <X size={18} />
      </button>
      <span className="consent-icon"><BarChart3 size={22} /></span>
      <div>
        <strong>Medir para reducir la desventaja informativa</strong>
        <p>
          Con tu permiso medimos qué herramientas se usan y qué dudas aparecen. Nunca enviamos
          importes financieros, texto libre ni datos bancarios a la analítica.
        </p>
        <div className="consent-actions">
          <button className="button button--primary" disabled={saving} onClick={() => choose('accepted')}>
            Aceptar medición
          </button>
          <button className="button button--ghost" disabled={saving} onClick={() => choose('rejected')}>
            Rechazar
          </button>
          <span><ShieldCheck size={15} /> Cookies propias, sin publicidad</span>
        </div>
      </div>
    </aside>
  )
}
