import { useMemo, useState } from 'react'
import { BadgeEuro, CheckCircle2, Database, ShieldCheck } from 'lucide-react'

import { submitMarketObservation, track } from '../../api'
import { ErrorState, Field, LoadingState, NumberField, Segmented, formatValue } from '../../shared/components/ui'

type PropertyType = 'apartment' | 'house' | 'other'
type PropertyAge = 'new' | 'up_to_5' | 'over_5' | 'unknown'
type ContributorRole = 'buyer' | 'seller' | 'professional' | 'other'

interface PriceFieldProps {
  label: string
  hint: string
  value: string
  onChange: (value: string) => void
}

function PriceField({ label, hint, value, onChange }: PriceFieldProps) {
  return (
    <Field label={label} hint={hint}>
      <span className="number-input">
        <input
          type="number"
          min="1"
          max="100000000"
          step="1000"
          inputMode="numeric"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Opcional"
        />
        <span>€</span>
      </span>
    </Field>
  )
}

function optionalPrice(value: string) {
  const parsed = Number(value)
  return value && parsed > 0 ? parsed : null
}

export default function MarketObservationForm({
  geographyCode,
  geographyName,
}: {
  geographyCode: string
  geographyName: string
}) {
  const currentMonth = new Date().toISOString().slice(0, 7)
  const [propertyType, setPropertyType] = useState<PropertyType>('apartment')
  const [propertyAge, setPropertyAge] = useState<PropertyAge>('over_5')
  const [contributorRole, setContributorRole] = useState<ContributorRole>('buyer')
  const [surface, setSurface] = useState(80)
  const [askingPrice, setAskingPrice] = useState('')
  const [appraisalValue, setAppraisalValue] = useState('')
  const [negotiatedPrice, setNegotiatedPrice] = useState('')
  const [deedPrice, setDeedPrice] = useState('')
  const [observedMonth, setObservedMonth] = useState(currentMonth)
  const [consent, setConsent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [metrics, setMetrics] = useState<Record<string, number | null> | null>(null)

  const suppliedPrices = useMemo(
    () => [askingPrice, appraisalValue, negotiatedPrice, deedPrice].filter((value) => Number(value) > 0).length,
    [askingPrice, appraisalValue, negotiatedPrice, deedPrice],
  )

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setError('')
    if (suppliedPrices === 0) {
      setError('Añade al menos uno de los importes para aportar una observación útil.')
      return
    }
    setLoading(true)
    try {
      const result = await submitMarketObservation({
        geography_code: geographyCode,
        property_type: propertyType,
        property_age: propertyAge,
        contributor_role: contributorRole,
        surface_area_m2: surface,
        asking_price_eur: optionalPrice(askingPrice),
        appraisal_value_eur: optionalPrice(appraisalValue),
        negotiated_price_eur: optionalPrice(negotiatedPrice),
        deed_price_eur: optionalPrice(deedPrice),
        observed_period: `${observedMonth}-01`,
        market_data_consent: consent,
      })
      setMetrics(result.metrics)
      void track('market_observation_submitted', {
        geography_code: geographyCode,
        property_type: propertyType,
        property_age: propertyAge,
        price_fields_count_bucket: suppliedPrices >= 3 ? '3_plus' : String(suppliedPrices),
      })
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'No hemos podido guardar la observación.')
    } finally {
      setLoading(false)
    }
  }

  if (metrics) {
    const visibleMetrics = [
      ['Precio solicitado', metrics.asking_price_eur_m2, 'eur_m2'],
      ['Valor tasado', metrics.appraisal_value_eur_m2, 'eur_m2'],
      ['Prima solicitada sobre tasación', metrics.asking_vs_appraisal_pct, 'percent'],
      ['Descuento negociado', metrics.negotiated_discount_pct, 'percent'],
      ['Precio escriturado sobre tasación', metrics.deed_vs_appraisal_pct, 'percent'],
    ].filter(([, value]) => value != null) as Array<[string, number, string]>

    return (
      <section className="panel market-contribution-success" aria-live="polite">
        <span><CheckCircle2 size={31} /></span>
        <div>
          <span className="eyebrow">Observación recibida</span>
          <h2>Tu dato ya suma contexto a {geographyName}</h2>
          <p>Se utilizará de forma agregada cuando exista una muestra territorial suficiente.</p>
        </div>
        <div className="market-contribution-metrics">
          {visibleMetrics.map(([label, value, unit]) => (
            <article key={label}><span>{label}</span><strong>{formatValue(value, unit)}</strong></article>
          ))}
        </div>
        <button className="button button--secondary" type="button" onClick={() => setMetrics(null)}>
          Aportar otro caso
        </button>
      </section>
    )
  }

  return (
    <form className="panel market-contribution-form" onSubmit={submit}>
      <div className="panel-heading">
        <div>
          <span className="eyebrow"><Database size={14} /> Datos aportados por compradores</span>
          <h2>¿Qué precio has visto, tasado o negociado?</h2>
          <p>
            Con suficiente muestra podremos medir la distancia real entre lo que se pide, lo que
            se tasa y lo que finalmente se paga en cada territorio.
          </p>
        </div>
        <BadgeEuro size={27} />
      </div>

      <div className="market-contribution-context">
        <span>Territorio de la observación</span>
        <strong>{geographyName}</strong>
        <small>Cambia la zona desde “Entender una zona” si necesitas seleccionar otra provincia.</small>
      </div>

      <Segmented
        label="Tipo de vivienda"
        value={propertyType}
        onChange={setPropertyType}
        options={[
          { value: 'apartment', label: 'Piso' },
          { value: 'house', label: 'Casa' },
          { value: 'other', label: 'Otra' },
        ]}
      />
      <Segmented
        label="Antigüedad comparable con MIVAU"
        value={propertyAge}
        onChange={setPropertyAge}
        options={[
          { value: 'new', label: 'Obra nueva' },
          { value: 'up_to_5', label: 'Hasta 5 años' },
          { value: 'over_5', label: 'Más de 5 años' },
          { value: 'unknown', label: 'No lo sé' },
        ]}
      />

      <div className="form-grid form-grid--three market-contribution-basics">
        <NumberField label="Superficie" value={surface} onChange={setSurface} suffix="m²" min={11} max={2000} />
        <Field label="Mes de referencia">
          <input type="month" value={observedMonth} max={currentMonth} onChange={(event) => setObservedMonth(event.target.value)} required />
        </Field>
        <Field label="Tu relación con el caso">
          <select value={contributorRole} onChange={(event) => setContributorRole(event.target.value as ContributorRole)}>
            <option value="buyer">Comprador/a</option>
            <option value="seller">Vendedor/a</option>
            <option value="professional">Profesional</option>
            <option value="other">Otra</option>
          </select>
        </Field>
      </div>

      <div className="market-price-grid">
        <PriceField label="Precio solicitado" hint="Importe anunciado por la vivienda." value={askingPrice} onChange={setAskingPrice} />
        <PriceField label="Valor de tasación" hint="Valor indicado por la tasadora." value={appraisalValue} onChange={setAppraisalValue} />
        <PriceField label="Precio negociado" hint="Importe aceptado antes de escritura." value={negotiatedPrice} onChange={setNegotiatedPrice} />
        <PriceField label="Precio escriturado" hint="Importe final que figura en la escritura." value={deedPrice} onChange={setDeedPrice} />
      </div>

      <div className="market-privacy-note">
        <ShieldCheck size={21} />
        <p><strong>Solo necesitamos el contexto de mercado.</strong> No solicitamos dirección, referencia catastral, URL del anuncio, identidad, ingresos ni documentación.</p>
      </div>

      <label className="check-row">
        <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} required />
        <span>
          <strong>Aporto voluntariamente estos datos para elaborar estadísticas agregadas.</strong>
          <small>Se conservarán durante el plazo indicado en el aviso de privacidad y no se publicarán como un caso individual.</small>
        </span>
      </label>

      {loading && <LoadingState label="Guardando observación…" />}
      {error && <ErrorState message={error} />}
      <div className="form-submit-row">
        <span className="privacy-inline"><ShieldCheck size={18} /> Consentimiento específico y separado.</span>
        <button className="button button--primary" type="submit" disabled={loading || !consent}>
          Aportar al índice <BadgeEuro size={18} />
        </button>
      </div>
    </form>
  )
}
