import { useEffect, useMemo, useState } from 'react'
import { Database, MapPin, Search, SlidersHorizontal } from 'lucide-react'

import { getGeographies, getMarketSummary, track } from '../api'
import { FALLBACK_GEOGRAPHIES, REGION_TILES } from '../data/geographies'
import type { Geography, MarketSummary, Metric } from '../types'
import { ErrorState, LoadingState, MetricCard, NumberField, Segmented } from './ui'

const DEFAULT_ASSUMPTIONS = { homeSize: 90, ltv: 80, term: 25 }

export default function MarketExplorer({
  onContextChange,
}: {
  onContextChange: (context: { geography: Geography; summary: MarketSummary | null }) => void
}) {
  const [geographies, setGeographies] = useState(FALLBACK_GEOGRAPHIES)
  const [selectedCode, setSelectedCode] = useState('PROV:24')
  const [selectedRegion, setSelectedRegion] = useState('CCAA:07')
  const [search, setSearch] = useState('León')
  const [draft, setDraft] = useState(DEFAULT_ASSUMPTIONS)
  const [assumptions, setAssumptions] = useState(DEFAULT_ASSUMPTIONS)
  const [summary, setSummary] = useState<MarketSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getGeographies()
      .then((items) => setGeographies(items))
      .catch(() => {
        // Names remain usable while the summary communicates backend availability.
      })
  }, [])

  const byCode = useMemo(
    () => new Map(geographies.map((geography) => [geography.code, geography])),
    [geographies],
  )
  const selected = byCode.get(selectedCode) ?? FALLBACK_GEOGRAPHIES.find((g) => g.code === selectedCode)!
  const provinces = geographies.filter(
    (geography) => geography.level === 'province' && geography.parent_code === selectedRegion,
  )

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    getMarketSummary(selectedCode, assumptions)
      .then((result) => {
        if (!active) return
        setSummary(result)
        onContextChange({ geography: selected, summary: result })
      })
      .catch(() => {
        if (!active) return
        setSummary(null)
        setError(
          'No hay una ficha disponible para este territorio todavía. Puedes elegir otro o volver a intentarlo.',
        )
        onContextChange({ geography: selected, summary: null })
      })
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [assumptions, onContextChange, selected, selectedCode])

  function selectGeography(geography: Geography, method: 'map' | 'search' | 'province_list') {
    setSelectedCode(geography.code)
    setSearch(geography.name)
    if (geography.level === 'ccaa') setSelectedRegion(geography.code)
    if (geography.level === 'province' && geography.parent_code) {
      setSelectedRegion(geography.parent_code)
    }
    void track('location_selected', {
      geography_code: geography.code,
      selection_method: method,
    })
    void track('market_compared', { geography_code: geography.code })
  }

  function chooseSearch(value: string) {
    setSearch(value)
    const match = geographies.find(
      (geography) => geography.name.localeCompare(value, 'es', { sensitivity: 'base' }) === 0,
    )
    if (match) selectGeography(match, 'search')
  }

  const derivedMetrics = summary
    ? Object.entries(summary.derived).filter(([, value]) => 'value' in value) as Array<
        [string, Metric]
      >
    : []

  return (
    <div className="workspace-grid workspace-grid--market">
      <aside className="panel location-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">1 · Elige territorio</span>
            <h2>¿Dónde estás mirando?</h2>
          </div>
          <MapPin size={22} />
        </div>

        <label className="search-box">
          <Search size={18} />
          <input
            list="geography-options"
            value={search}
            onChange={(event) => chooseSearch(event.target.value)}
            placeholder="Busca provincia o comunidad"
            aria-label="Busca provincia o comunidad"
          />
        </label>
        <datalist id="geography-options">
          {geographies
            .filter((geography) => geography.level !== 'country')
            .map((geography) => (
              <option key={geography.code} value={geography.name} />
            ))}
        </datalist>

        <div className="tile-map" aria-label="Mapa simplificado de comunidades autónomas">
          {REGION_TILES.map((tile) => {
            const geography = byCode.get(tile.code)
            return (
              <button
                key={tile.code}
                type="button"
                className={`${selectedRegion === tile.code ? 'is-active' : ''} ${geography?.available ? 'has-data' : ''}`}
                style={{
                  gridColumn: `${tile.x + 1} / span ${tile.width ?? 1}`,
                  gridRow: tile.y + 1,
                }}
                onClick={() => geography && selectGeography(geography, 'map')}
                title={geography?.name ?? tile.shortName}
              >
                {tile.shortName}
              </button>
            )
          })}
        </div>
        <p className="map-caption">
          Vista territorial simplificada. El punto azul indica cobertura directa en la base.
        </p>

        {provinces.length > 0 && (
          <div className="province-picker">
            <span>Provincias de {byCode.get(selectedRegion)?.name}</span>
            <div>
              {provinces.map((province) => (
                <button
                  key={province.code}
                  type="button"
                  className={selectedCode === province.code ? 'is-active' : ''}
                  onClick={() => selectGeography(province, 'province_list')}
                >
                  {province.name}
                  {province.available && <i aria-label="Con datos" />}
                </button>
              ))}
            </div>
          </div>
        )}
      </aside>

      <main className="market-main">
        <section className="panel scenario-strip">
          <div className="panel-heading panel-heading--compact">
            <div>
              <span className="eyebrow">2 · Ajusta la vivienda</span>
              <h2>Escenario para {selected.name}</h2>
            </div>
            <SlidersHorizontal size={21} />
          </div>
          <div className="form-grid form-grid--inline">
            <NumberField
              label="Tamaño"
              value={draft.homeSize}
              onChange={(homeSize) => setDraft((current) => ({ ...current, homeSize }))}
              suffix="m²"
              min={20}
              max={500}
            />
            <NumberField
              label="Financiación"
              value={draft.ltv}
              onChange={(ltv) => setDraft((current) => ({ ...current, ltv }))}
              suffix="%"
              min={10}
              max={100}
            />
            <Segmented
              label="Plazo"
              value={draft.term}
              onChange={(term) => setDraft((current) => ({ ...current, term }))}
              options={[20, 25, 30].map((value) => ({ value, label: `${value} años` }))}
            />
            <button className="button button--secondary scenario-apply" onClick={() => setAssumptions(draft)}>
              Aplicar escenario
            </button>
          </div>
        </section>

        {loading && <LoadingState label="Consultando las series oficiales…" />}
        {error && <ErrorState message={error} />}
        {summary && !loading && (
          <>
            <section className="market-summary-heading">
              <div>
                <span className="eyebrow">Ficha territorial</span>
                <h2>{selected.name}, en contexto</h2>
              </div>
              <span className="coverage-pill">
                <Database size={15} /> {summary.coverage.available_fields}/
                {summary.coverage.total_fields} indicadores
              </span>
            </section>
            <div className="metrics-grid">
              {Object.entries(summary.market_card).map(([key, metric]) => (
                <MetricCard key={key} metricKey={key} metric={metric} />
              ))}
            </div>
            <section className="derived-section">
              <div>
                <span className="eyebrow">Lectura rápida</span>
                <h3>Qué significan juntos estos datos</h3>
              </div>
              <div className="metrics-grid metrics-grid--derived">
                {derivedMetrics.map(([key, metric]) => (
                  <MetricCard key={key} metricKey={key} metric={metric} />
                ))}
              </div>
            </section>
            <div className="data-note">
              <Database size={18} />
              <p>
                Cada cifra conserva periodo y fuente. Cuando falta cobertura local, la ficha lo
                indica y no presenta un dato provincial como municipal.
              </p>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
