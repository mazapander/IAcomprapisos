import { useEffect, useState } from 'react'
import { BarChart3, Landmark, TrendingUp } from 'lucide-react'

import { getNationalObservatory } from '../../api'
import type { NationalObservatoryData, ObservatorySeries } from '../../types'
import { formatValue } from '../../shared/components/ui'

type PulseItem = {
  code: string
  label: string
  fallback: string
  icon: typeof Landmark
}

const PULSE: PulseItem[] = [
  { code: 'mortgages_housing_total', label: 'Hipotecas constituidas', fallback: 'Último mes publicado', icon: Landmark },
  { code: 'average_mortgage_amount_eur', label: 'Importe medio hipotecado', fallback: 'Último mes publicado', icon: TrendingUp },
  { code: 'appraisal_price_eur_m2', label: 'Valor tasado medio', fallback: 'Último trimestre publicado', icon: BarChart3 },
]

function findSeries(data: NationalObservatoryData, code: string): ObservatorySeries | undefined {
  return Object.values(data.groups).flatMap((group) => group.series).find((series) => series.code === code)
}

export default function MarketPulse() {
  const [data, setData] = useState<NationalObservatoryData | null>(null)

  useEffect(() => {
    let active = true
    getNationalObservatory(5).then((result) => active && setData(result)).catch(() => {})
    return () => { active = false }
  }, [])

  return (
    <section className="market-pulse" aria-label="Pulso reciente del mercado estatal">
      <div className="market-pulse__heading">
        <span>España en cifras</span>
        <small>Fuentes oficiales · periodos publicados</small>
      </div>
      <div className="market-pulse__grid">
        {PULSE.map((item) => {
          const series = data && findSeries(data, item.code)
          const Icon = item.icon
          return (
            <article key={item.code} className="market-pulse__item">
              <Icon size={16} />
              <span>{item.label}</span>
              <strong>{series?.latest ? formatValue(series.latest.value, series.latest.unit) : '—'}</strong>
              <small>{series?.latest?.period.slice(0, 7) ?? item.fallback}</small>
            </article>
          )
        })}
      </div>
    </section>
  )
}
