import { useMemo, useState } from 'react'
import { ArrowRight, BadgeEuro, Plus, Scale, ShieldCheck, Trash2, TrendingDown } from 'lucide-react'

import { reviewMortgage, track } from '../../api'
import type { CalculationResult, MortgageReviewPayload, RateType } from '../../types'
import { ErrorState, LoadingState, NumberField, Segmented, formatValue } from '../../shared/components/ui'

interface Offer {
  id: number
  entity: string
  rateType: RateType
  fixedRate: number
  spread: number
  apr: number
  term: number
  fixedYears: number
  fees: number
  linkedMonthly: number
}

const newOffer = (id: number, entity: string): Offer => ({
  id,
  entity,
  rateType: 'fixed',
  fixedRate: id === 1 ? 2.75 : 2.95,
  spread: 0.75,
  apr: id === 1 ? 2.94 : 3.12,
  term: 25,
  fixedYears: 5,
  fees: 0,
  linkedMonthly: 0,
})

export default function OfferComparison({
  euribor = 2.5,
  marketApr,
  geographyCode,
  onSingleReview,
}: {
  euribor?: number
  marketApr?: number
  geographyCode: string
  onSingleReview: () => void
}) {
  const [propertyPrice, setPropertyPrice] = useState(250000)
  const [mortgageAmount, setMortgageAmount] = useState(200000)
  const [savings, setSavings] = useState(70000)
  const [monthlyIncome, setMonthlyIncome] = useState(3500)
  const [monthlyDebt, setMonthlyDebt] = useState(0)
  const [livingCosts, setLivingCosts] = useState(1400)
  const [purchaseCosts, setPurchaseCosts] = useState(10)
  const [offers, setOffers] = useState<Offer[]>([newOffer(1, 'Oferta A'), newOffer(2, 'Oferta B')])
  const [results, setResults] = useState<Array<{ offer: Offer; result: CalculationResult }> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function updateOffer(id: number, patch: Partial<Offer>) {
    setOffers((current) => current.map((offer) => (offer.id === id ? { ...offer, ...patch } : offer)))
  }

  function payloadFor(offer: Offer): MortgageReviewPayload {
    const variableRate = Math.max(0, euribor + offer.spread)
    return {
      property_price_eur: propertyPrice,
      savings_eur: savings,
      annual_net_household_income_eur: monthlyIncome * 12,
      mortgage_amount_eur: mortgageAmount,
      rate_type: offer.rateType,
      annual_nominal_rate_pct: offer.rateType === 'variable' ? variableRate : offer.fixedRate,
      annual_apr_pct: offer.apr,
      term_years: offer.term,
      mixed_fixed_years: offer.rateType === 'mixed' ? offer.fixedYears : undefined,
      variable_spread_pct: offer.rateType === 'mixed' ? offer.spread : undefined,
      upfront_fees_eur: offer.fees,
      monthly_linked_costs_eur: offer.linkedMonthly,
      existing_monthly_debt_eur: monthlyDebt,
      monthly_living_costs_eur: livingCosts,
      purchase_cost_pct: purchaseCosts,
      stress_rate_increase_pp: 2,
      market_apr_pct: marketApr,
      euribor_pct: euribor,
    }
  }

  async function compare(event: React.FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setResults(null)
    void track('comparison_started', { use_case: 'offer_comparison' })
    try {
      const calculated = await Promise.all(
        offers.map(async (offer) => ({ offer, result: await reviewMortgage(payloadFor(offer)) })),
      )
      calculated.sort(
        (left, right) =>
          Number(left.result.calculations.estimated_total_cost_eur ?? Infinity) -
          Number(right.result.calculations.estimated_total_cost_eur ?? Infinity),
      )
      setResults(calculated)
      void track('comparison_completed', {
        use_case: 'offer_comparison',
        offer_count_bucket: offers.length >= 4 ? '4' : String(offers.length),
        geography_code: geographyCode,
      })
    } catch {
      setError('No hemos podido comparar todas las ofertas. Revisa especialmente los tramos mixtos.')
    } finally {
      setLoading(false)
    }
  }

  const savingAgainstSecond = useMemo(() => {
    if (!results || results.length < 2) return null
    return (
      Number(results[1].result.calculations.estimated_total_cost_eur) -
      Number(results[0].result.calculations.estimated_total_cost_eur)
    )
  }, [results])

  return (
    <form className="compare-layout" onSubmit={compare}>
      <section className="panel comparison-context">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Misma vivienda, mismas reglas</span>
            <h2>Compara ofertas de verdad comparables</h2>
            <p>
              Normalizamos plazo, cuota, comisiones, vinculaciones y riesgo de tipo para que el
              banco no marque por sí solo el terreno de juego.
            </p>
          </div>
          <Scale size={25} />
        </div>
        <div className="form-grid form-grid--three">
          <NumberField label="Precio" value={propertyPrice} onChange={setPropertyPrice} suffix="€" min={1} />
          <NumberField label="Importe solicitado" value={mortgageAmount} onChange={setMortgageAmount} suffix="€" min={1} />
          <NumberField label="Ahorro" value={savings} onChange={setSavings} suffix="€" />
          <NumberField label="Ingresos netos" value={monthlyIncome} onChange={setMonthlyIncome} suffix="€/mes" min={1} />
          <NumberField label="Otras deudas" value={monthlyDebt} onChange={setMonthlyDebt} suffix="€/mes" />
          <NumberField label="Gastos habituales" value={livingCosts} onChange={setLivingCosts} suffix="€/mes" />
        </div>
        <button className="text-button" type="button" onClick={onSingleReview}>
          Solo quiero revisar una oferta paso a paso
        </button>
      </section>

      <div className="offer-grid">
        {offers.map((offer, index) => (
          <article className="panel offer-card" key={offer.id}>
            <div className="offer-card__heading">
              <span className="offer-number">{index + 1}</span>
              <label>
                <span>Entidad u oferta</span>
                <input
                  value={offer.entity}
                  maxLength={60}
                  onChange={(event) => updateOffer(offer.id, { entity: event.target.value })}
                />
              </label>
              {offers.length > 2 && (
                <button
                  type="button"
                  aria-label={`Eliminar ${offer.entity}`}
                  onClick={() => setOffers((current) => current.filter((item) => item.id !== offer.id))}
                >
                  <Trash2 size={17} />
                </button>
              )}
            </div>
            <Segmented
              label="Modalidad"
              value={offer.rateType}
              onChange={(rateType) => updateOffer(offer.id, { rateType })}
              options={[
                { value: 'fixed', label: 'Fija' },
                { value: 'variable', label: 'Variable' },
                { value: 'mixed', label: 'Mixta' },
              ]}
            />
            <div className="form-grid">
              {offer.rateType !== 'variable' && (
                <NumberField
                  label={offer.rateType === 'mixed' ? 'TIN tramo fijo' : 'TIN'}
                  value={offer.fixedRate}
                  onChange={(fixedRate) => updateOffer(offer.id, { fixedRate })}
                  suffix="%"
                  step={0.01}
                  max={30}
                />
              )}
              {offer.rateType !== 'fixed' && (
                <NumberField
                  label="Diferencial"
                  value={offer.spread}
                  onChange={(spread) => updateOffer(offer.id, { spread })}
                  suffix="%"
                  step={0.01}
                  max={10}
                />
              )}
              <NumberField
                label="TAE"
                value={offer.apr}
                onChange={(apr) => updateOffer(offer.id, { apr })}
                suffix="%"
                step={0.01}
                max={30}
              />
              <NumberField
                label="Plazo"
                value={offer.term}
                onChange={(term) => updateOffer(offer.id, { term })}
                suffix="años"
                min={1}
                max={50}
              />
              {offer.rateType === 'mixed' && (
                <NumberField
                  label="Tramo fijo"
                  value={offer.fixedYears}
                  onChange={(fixedYears) => updateOffer(offer.id, { fixedYears })}
                  suffix="años"
                  min={1}
                  max={40}
                />
              )}
              <NumberField
                label="Comisiones iniciales"
                value={offer.fees}
                onChange={(fees) => updateOffer(offer.id, { fees })}
                suffix="€"
              />
              <NumberField
                label="Vinculaciones"
                value={offer.linkedMonthly}
                onChange={(linkedMonthly) => updateOffer(offer.id, { linkedMonthly })}
                suffix="€/mes"
                hint="Coste medio de seguros, cuentas y productos exigidos."
              />
            </div>
          </article>
        ))}
        {offers.length < 4 && (
          <button
            type="button"
            className="add-offer"
            onClick={() => {
              const id = Math.max(...offers.map((offer) => offer.id)) + 1
              setOffers((current) => [...current, newOffer(id, `Oferta ${String.fromCharCode(64 + id)}`)])
            }}
          >
            <Plus size={20} /> Añadir otra oferta
          </button>
        )}
      </div>

      <div className="comparison-actions">
        <button className="button button--primary" type="submit">
          Comparar en igualdad de condiciones <ArrowRight size={18} />
        </button>
        <span className="privacy-inline">
          <ShieldCheck size={18} /> Las ofertas no se almacenan en el servidor.
        </span>
      </div>

      {loading && <LoadingState label="Normalizando y comparando ofertas…" />}
      {error && <ErrorState message={error} />}
      {results && (
        <section className="panel comparison-results" aria-live="polite">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Argumentos para negociar</span>
              <h2>{results[0].offer.entity} parte con el menor coste comparable</h2>
              {savingAgainstSecond != null && savingAgainstSecond > 0 && (
                <p>
                  La diferencia estimada frente a la siguiente oferta es de{' '}
                  <strong>{formatValue(savingAgainstSecond, 'eur')}</strong> durante el plazo.
                </p>
              )}
            </div>
            <TrendingDown size={25} />
          </div>
          <div className="comparison-table-wrap">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Oferta</th>
                  <th>Cuota inicial</th>
                  <th>Cuota estresada</th>
                  <th>TAE vs. mercado</th>
                  <th>Vinculaciones</th>
                  <th>Coste comparable</th>
                </tr>
              </thead>
              <tbody>
                {results.map(({ offer, result }, index) => (
                  <tr key={offer.id} className={index === 0 ? 'is-best' : ''}>
                    <th>
                      {index === 0 && <span className="best-badge"><BadgeEuro size={14} /> Mejor coste</span>}
                      {offer.entity}
                      <small>{offer.rateType === 'fixed' ? 'Fija' : offer.rateType === 'mixed' ? 'Mixta' : 'Variable'}</small>
                    </th>
                    <td>{formatValue(result.calculations.monthly_payment_eur, 'eur')}</td>
                    <td>{formatValue(result.calculations.stressed_monthly_payment_eur, 'eur')}</td>
                    <td>{formatValue(result.calculations.apr_vs_market_pp, 'percentage_points')}</td>
                    <td>{formatValue(result.calculations.linked_costs_total_eur, 'eur')}</td>
                    <td><strong>{formatValue(result.calculations.estimated_total_cost_eur, 'eur')}</strong></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="negotiation-note">
            <strong>Úsalo como palanca.</strong>
            <span>
              Pide a cada entidad que iguale el coste total de la mejor alternativa, no solo el
              TIN. Contrasta también qué vinculaciones puedes cancelar y cuándo.
            </span>
          </div>
          <p className="disclaimer">
            Comparación educativa basada en los datos introducidos. Las vinculaciones se
            proyectan durante todo el plazo para hacerlas visibles; revisa en la FEIN su duración
            y condiciones reales.
          </p>
        </section>
      )}
    </form>
  )
}
