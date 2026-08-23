import { useMemo, useState } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  Check,
  Landmark,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

import { reviewMortgage, track } from '../api'
import type { CalculationResult, MortgageReviewPayload, RateType } from '../types'
import { ErrorState, LoadingState, NumberField, ResultPanel, Segmented } from './ui'

const STORAGE_KEY = 'iacomprapisos.mortgageScenario'

export default function MortgageReview({
  euribor,
  marketApr,
  geographyCode,
}: {
  euribor?: number
  marketApr?: number
  geographyCode: string
}) {
  const [step, setStep] = useState(1)
  const [propertyPrice, setPropertyPrice] = useState(250000)
  const [savings, setSavings] = useState(70000)
  const [ltv, setLtv] = useState(80)
  const [propertyType, setPropertyType] = useState<'used' | 'new'>('used')
  const [rateType, setRateType] = useState<RateType>('fixed')
  const [fixedRate, setFixedRate] = useState(2.75)
  const [spread, setSpread] = useState(0.75)
  const [referenceRate, setReferenceRate] = useState(euribor ?? 2.5)
  const [term, setTerm] = useState(25)
  const [fixedYears, setFixedYears] = useState(5)
  const [apr, setApr] = useState<number | ''>('')
  const [monthlyIncome, setMonthlyIncome] = useState(3500)
  const [monthlyDebt, setMonthlyDebt] = useState(0)
  const [livingCosts, setLivingCosts] = useState(1400)
  const [advanced, setAdvanced] = useState(false)
  const [saveLocal, setSaveLocal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<CalculationResult | null>(null)

  const mortgageAmount = Math.round((propertyPrice * ltv) / 100)
  const purchaseCosts = propertyType === 'new' ? 12 : 10
  const currentVariableRate = Math.max(0, referenceRate + spread)
  const requiredCash = propertyPrice * (1 - ltv / 100 + purchaseCosts / 100)
  const stepLabels = ['Vivienda', 'Oferta', 'Tu hogar']

  const payload = useMemo<MortgageReviewPayload>(() => {
    const result: MortgageReviewPayload = {
      property_price_eur: propertyPrice,
      savings_eur: savings,
      annual_net_household_income_eur: monthlyIncome * 12,
      mortgage_amount_eur: mortgageAmount,
      rate_type: rateType,
      annual_nominal_rate_pct: rateType === 'variable' ? currentVariableRate : fixedRate,
      term_years: term,
      existing_monthly_debt_eur: monthlyDebt,
      monthly_living_costs_eur: livingCosts,
      purchase_cost_pct: purchaseCosts,
      stress_rate_increase_pp: 2,
      euribor_pct: referenceRate,
    }
    if (apr !== '') result.annual_apr_pct = apr
    if (marketApr != null) result.market_apr_pct = marketApr
    if (rateType === 'mixed') {
      result.mixed_fixed_years = fixedYears
      result.variable_spread_pct = spread
    }
    return result
  }, [
    apr,
    currentVariableRate,
    fixedRate,
    fixedYears,
    livingCosts,
    ltv,
    marketApr,
    monthlyDebt,
    monthlyIncome,
    mortgageAmount,
    propertyPrice,
    purchaseCosts,
    rateType,
    referenceRate,
    savings,
    spread,
    term,
  ])

  function nextStep() {
    const next = Math.min(3, step + 1)
    void track('wizard_step_completed', { step, use_case: 'mortgage' })
    setStep(next)
  }

  async function submit() {
    setLoading(true)
    setError('')
    setResult(null)
    void track('review_started', { rate_type: rateType })
    try {
      const response = await reviewMortgage(payload)
      setResult(response)
      if (saveLocal) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
        void track('scenario_saved', { rate_type: rateType })
      } else {
        localStorage.removeItem(STORAGE_KEY)
      }
      const effort = Number(response.calculations.effort_pct ?? 0)
      const resultLtv = Number(response.calculations.ltv_pct ?? 0)
      void track('review_completed', {
        result_status: response.status,
        effort_bucket: effort < 30 ? 'under_30' : effort < 40 ? '30_39' : '40_plus',
        ltv_bucket: resultLtv <= 80 ? 'up_to_80' : 'over_80',
        alert_count_bucket:
          response.alerts.length === 0 ? '0' : response.alerts.length < 3 ? '1_2' : '3_plus',
        rate_type: rateType,
        geography_code: geographyCode,
      })
    } catch {
      setError('No hemos podido revisar la oferta. Comprueba los datos de cada paso.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mortgage-workspace">
      <section className="panel mortgage-wizard">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Revisión guiada</span>
            <h2>Entiende la oferta sin pelearte con el formulario</h2>
          </div>
          <Landmark size={25} />
        </div>

        <ol className="stepper" aria-label="Pasos del análisis">
          {stepLabels.map((label, index) => {
            const number = index + 1
            return (
              <li key={label} className={step === number ? 'is-current' : step > number ? 'is-done' : ''}>
                <button type="button" onClick={() => number < step && setStep(number)}>
                  <span>{step > number ? <Check size={15} /> : number}</span>
                  {label}
                </button>
              </li>
            )
          })}
        </ol>

        {step === 1 && (
          <div className="wizard-step">
            <div className="smart-fill-note">
              <Sparkles size={18} />
              <span>
                Calculamos el importe de hipoteca y el efectivo necesario a partir del precio y
                del porcentaje de financiación.
              </span>
            </div>
            <div className="form-grid">
              <NumberField
                label="Precio de la vivienda"
                value={propertyPrice}
                onChange={setPropertyPrice}
                suffix="€"
                min={1}
              />
              <NumberField
                label="Ahorro disponible"
                value={savings}
                onChange={setSavings}
                suffix="€"
              />
            </div>
            <Segmented
              label="Tipo de vivienda"
              value={propertyType}
              onChange={setPropertyType}
              options={[
                { value: 'used', label: 'Segunda mano', description: 'Gastos estimados: 10 %' },
                { value: 'new', label: 'Obra nueva', description: 'Gastos estimados: 12 %' },
              ]}
            />
            <div className="range-control">
              <div>
                <span>Financiación</span>
                <strong>{ltv} %</strong>
              </div>
              <input
                type="range"
                min="50"
                max="100"
                value={ltv}
                onChange={(event) => setLtv(Number(event.target.value))}
              />
              <div className="auto-summary">
                <span>Hipoteca calculada <strong>{mortgageAmount.toLocaleString('es-ES')} €</strong></span>
                <span>Entrada y gastos aprox. <strong>{Math.round(requiredCash).toLocaleString('es-ES')} €</strong></span>
              </div>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="wizard-step">
            <Segmented
              label="Tipo de hipoteca"
              value={rateType}
              onChange={setRateType}
              options={[
                { value: 'fixed', label: 'Fija', description: 'Una cuota estable' },
                { value: 'variable', label: 'Variable', description: 'Referencia + diferencial' },
                { value: 'mixed', label: 'Mixta', description: 'Tramo fijo y después variable' },
              ]}
            />
            <div className="form-grid">
              {rateType !== 'variable' && (
                <NumberField
                  label={rateType === 'mixed' ? 'TIN del tramo fijo' : 'TIN de la oferta'}
                  value={fixedRate}
                  onChange={setFixedRate}
                  suffix="%"
                  step={0.01}
                  max={30}
                />
              )}
              {rateType !== 'fixed' && (
                <NumberField
                  label="Diferencial"
                  value={spread}
                  onChange={setSpread}
                  suffix="% sobre Euríbor"
                  step={0.01}
                  max={10}
                />
              )}
              <Segmented
                label="Plazo total"
                value={term}
                onChange={setTerm}
                options={[20, 25, 30, 35].map((value) => ({ value, label: `${value} años` }))}
              />
              {rateType === 'mixed' && (
                <Segmented
                  label="Duración del tramo fijo"
                  value={fixedYears}
                  onChange={setFixedYears}
                  options={[3, 5, 10].map((value) => ({ value, label: `${value} años` }))}
                />
              )}
            </div>
            {rateType !== 'fixed' && (
              <div className="reference-rate">
                <span>Euríbor usado</span>
                <strong>{referenceRate.toLocaleString('es-ES')} %</strong>
                <span>Tipo variable de partida: {currentVariableRate.toLocaleString('es-ES')} %</span>
              </div>
            )}
            <button className="text-button" type="button" onClick={() => setAdvanced((value) => !value)}>
              {advanced ? 'Ocultar TAE y referencia' : 'Tengo la TAE o quiero cambiar la referencia'}
            </button>
            {advanced && (
              <div className="advanced-box form-grid">
                <NumberField
                  label="TAE de la oferta"
                  value={apr === '' ? 0 : apr}
                  onChange={(value) => setApr(value || '')}
                  suffix="%"
                  step={0.01}
                  max={30}
                  hint="Opcional. Sirve para comparar costes, no para calcular la cuota."
                />
                {rateType !== 'fixed' && (
                  <NumberField
                    label="Euríbor de referencia"
                    value={referenceRate}
                    onChange={setReferenceRate}
                    suffix="%"
                    step={0.01}
                    min={-10}
                    max={30}
                  />
                )}
              </div>
            )}
          </div>
        )}

        {step === 3 && (
          <div className="wizard-step">
            <div className="form-grid">
              <NumberField
                label="Ingresos netos del hogar"
                value={monthlyIncome}
                onChange={setMonthlyIncome}
                suffix="€/mes"
                min={1}
                hint="Los convertimos automáticamente a renta anual."
              />
              <NumberField
                label="Otras cuotas y préstamos"
                value={monthlyDebt}
                onChange={setMonthlyDebt}
                suffix="€/mes"
              />
              <NumberField
                label="Gastos habituales"
                value={livingCosts}
                onChange={setLivingCosts}
                suffix="€/mes"
                hint="Se usan para calcular el colchón tras la compra."
              />
            </div>
            <label className="check-row">
              <input
                type="checkbox"
                checked={saveLocal}
                onChange={(event) => setSaveLocal(event.target.checked)}
              />
              <span>
                <strong>Recordar este escenario en este dispositivo</strong>
                <small>No se guarda en el servidor ni se sincroniza con otras cuentas.</small>
              </span>
            </label>
          </div>
        )}

        <div className="wizard-actions">
          {step > 1 && (
            <button className="button button--ghost" type="button" onClick={() => setStep(step - 1)}>
              <ArrowLeft size={18} /> Atrás
            </button>
          )}
          {step < 3 ? (
            <button className="button button--primary" type="button" onClick={nextStep}>
              Continuar <ArrowRight size={18} />
            </button>
          ) : (
            <button className="button button--primary" type="button" onClick={submit}>
              Revisar escenario <ArrowRight size={18} />
            </button>
          )}
        </div>
        <div className="privacy-inline">
          <ShieldCheck size={18} /> La renta, el ahorro y la oferta se procesan sin persistencia.
        </div>
      </section>

      <aside className="mortgage-result">
        {loading && <LoadingState />}
        {error && <ErrorState message={error} />}
        {!loading && !error && !result && (
          <div className="empty-result empty-result--sticky">
            <span><Building2 size={30} /></span>
            <h3>Un resultado que explica el porqué</h3>
            <p>
              Separaremos cuota, esfuerzo, entrada, colchón y exposición a tipos. En una mixta
              verás el tramo fijo y el posterior por separado.
            </p>
          </div>
        )}
        {result && (
          <ResultPanel
            result={result}
            title={
              result.status === 'balanced'
                ? 'El escenario está equilibrado con estos supuestos'
                : result.status === 'high_risk'
                  ? 'Hay señales que conviene resolver antes de firmar'
                  : 'El escenario merece una segunda revisión'
            }
            featuredKeys={[
              'monthly_payment_eur',
              ...(rateType === 'mixed' ? ['post_fixed_monthly_payment_eur'] : []),
              'stressed_monthly_payment_eur',
              'effort_pct',
              'stressed_effort_pct',
              'cash_required_eur',
              'remaining_savings_eur',
              'emergency_buffer_months',
              'total_interest_eur',
            ]}
          />
        )}
        {localStorage.getItem(STORAGE_KEY) && (
          <button
            className="text-button delete-scenario"
            type="button"
            onClick={() => {
              localStorage.removeItem(STORAGE_KEY)
              setSaveLocal(false)
            }}
          >
            Borrar el escenario guardado
          </button>
        )}
      </aside>
    </div>
  )
}
