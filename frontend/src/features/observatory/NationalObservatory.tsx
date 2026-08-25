import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  CalendarDays,
  Database,
  Minus,
} from 'lucide-react'

import { getNationalObservatory, track } from '../../api'
import type { NationalObservatoryData, ObservatoryGroupId, ObservatorySeries } from '../../types'
import { ErrorState, LoadingState, formatValue } from '../../shared/components/ui'
import TrendChart from './TrendChart'

const GROUPS: ObservatoryGroupId[] = ['prices', 'mortgages', 'rates']

function Change({ series }: { series: ObservatorySeries }) {
  const change = series.change_year_on_year
  if (change.value == null) return <span className="observatory-change">Sin comparativa interanual</span>
  const Icon = change.value > 0 ? ArrowUpRight : change.value < 0 ? ArrowDownRight : Minus
  const direction = change.value > 0 ? 'up' : change.value < 0 ? 'down' : 'flat'
  return (
    <span className={`observatory-change observatory-change--${direction}`}>
      <Icon size={15} /> {change.value > 0 ? '+' : ''}{formatValue(change.value, change.unit)} interanual
    </span>
  )
}

export default function NationalObservatory() {
  const [years, setYears] = useState(10)
  const [activeGroup, setActiveGroup] = useState<ObservatoryGroupId>('prices')
  const [selectedCode, setSelectedCode] = useState('')
  const [data, setData] = useState<NationalObservatoryData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    getNationalObservatory(years)
      .then((result) => {
        setData(result)
        setSelectedCode('')
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false))
  }, [years])

  const group = data?.groups[activeGroup]
  const selected = useMemo(
    () => group?.series.find((series) => series.code === selectedCode)
      ?? group?.series.find((series) => series.available)
      ?? group?.series[0],
    [group, selectedCode],
  )

  function changeGroup(id: ObservatoryGroupId) {
    setActiveGroup(id)
    setSelectedCode('')
    void track('observatory_group_changed', { use_case: id })
  }

  if (loading) return <LoadingState label="Preparando las series estatales…" />
  if (error || !data) return <ErrorState message={error || 'No se ha podido cargar el observatorio.'} />

  return (
    <div className="observatory-layout">
      <section className="panel observatory-overview">
        <div className="panel-heading">
          <div>
            <span className="eyebrow"><Activity size={14} /> España · datos oficiales</span>
            <h2>El mercado que condiciona tu negociación</h2>
            <p>Observa la tendencia antes de interpretar una oferta bancaria o el precio de una vivienda.</p>
          </div>
          <label className="observatory-range">
            <span>Histórico</span>
            <select value={years} onChange={(event) => setYears(Number(event.target.value))}>
              <option value={5}>5 años</option>
              <option value={10}>10 años</option>
              <option value={20}>20 años</option>
            </select>
          </label>
        </div>
        <div className="observatory-coverage">
          <span><Database size={16} /> {data.coverage.available_series} de {data.coverage.total_series} series disponibles</span>
          <span><CalendarDays size={16} /> Última observación: {data.coverage.latest_period?.slice(0, 7) ?? 'sin datos'}</span>
        </div>
      </section>

      <div className="observatory-tabs" role="tablist" aria-label="Bloques del observatorio">
        {GROUPS.map((id) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={activeGroup === id}
            className={activeGroup === id ? 'is-active' : ''}
            onClick={() => changeGroup(id)}
          >
            <strong>{data.groups[id].label}</strong>
            <span>{data.groups[id].description}</span>
          </button>
        ))}
      </div>

      <div className="observatory-series-grid">
        {group?.series.map((series) => (
          <button
            type="button"
            key={series.code}
            className={`observatory-series-card ${selected?.code === series.code ? 'is-active' : ''} ${!series.available ? 'is-empty' : ''}`}
            onClick={() => series.available && setSelectedCode(series.code)}
          >
            <span>{series.label}</span>
            <strong>{formatValue(series.latest?.value ?? null, series.latest?.unit)}</strong>
            <Change series={series} />
            <small>{series.latest ? `${series.latest.period.slice(0, 7)} · ${series.latest.source}` : 'Pendiente de cobertura'}</small>
          </button>
        ))}
      </div>

      {selected && (
        <section className="panel observatory-detail">
          <div className="observatory-detail__heading">
            <div>
              <span className="eyebrow">Serie seleccionada</span>
              <h2>{selected.label}</h2>
              <p>{selected.description}</p>
            </div>
            {selected.latest && (
              <div className="observatory-latest">
                <span>Último dato</span>
                <strong>{formatValue(selected.latest.value, selected.latest.unit)}</strong>
                <Change series={selected} />
              </div>
            )}
          </div>
          <TrendChart series={selected} />
          <div className="observatory-reading">
            <strong><ArrowRight size={17} /> Cómo usarlo</strong>
            <p>
              Utiliza la tendencia como contexto y contrasta tu oferta con la TAE, el tipo efectivo y el
              Euríbor del mismo periodo. Una media estatal no sustituye las condiciones concretas de la FEIN.
            </p>
          </div>
        </section>
      )}

      <p className="data-note"><Database size={16} /> {data.methodology.notice}</p>
    </div>
  )
}
