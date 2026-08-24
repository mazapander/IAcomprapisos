import { useState } from 'react'
import { ArrowRight, PiggyBank, ShieldCheck, Sparkles } from 'lucide-react'

import { calculateBudget, track } from '../../api'
import type { CalculationResult } from '../../types'
import { ErrorState, LoadingState, NumberField, ResultPanel, Segmented } from '../../shared/components/ui'

export default function BudgetCalculator({ marketRate }: { marketRate?: number }) {
  const [monthlyIncome, setMonthlyIncome] = useState(3500)
  const [savings, setSavings] = useState(70000)
  const [monthlyDebt, setMonthlyDebt] = useState(0)
  const [livingCosts, setLivingCosts] = useState(1400)
  const [term, setTerm] = useState(25)
  const [rate, setRate] = useState(marketRate ?? 3)
  const [maxEffort, setMaxEffort] = useState(35)
  const [ltv, setLtv] = useState(80)
  const [purchaseCosts, setPurchaseCosts] = useState(10)
  const [reserveMonths, setReserveMonths] = useState(6)
  const [advanced, setAdvanced] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<CalculationResult | null>(null)

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    void track('budget_started')
    try {
      const response = await calculateBudget({
        annual_net_household_income_eur: monthlyIncome * 12,
        savings_eur: savings,
        existing_monthly_debt_eur: monthlyDebt,
        monthly_living_costs_eur: livingCosts,
        annual_nominal_rate_pct: rate,
        term_years: term,
        max_effort_pct: maxEffort,
        max_ltv_pct: ltv,
        purchase_cost_pct: purchaseCosts,
        reserve_months: reserveMonths,
      })
      setResult(response)
      void track('budget_completed', { limiting_factor: response.limiting_factor ?? 'unknown' })
    } catch {
      setError('No hemos podido calcular el presupuesto. Revisa los datos e inténtalo de nuevo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="calculator-layout">
      <form className="panel calculator-form" onSubmit={submit}>
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Presupuesto sostenible</span>
            <h2>¿Hasta qué precio puedes mirar?</h2>
            <p>Partimos de lo que entra cada mes y del colchón que quieres conservar.</p>
          </div>
          <PiggyBank size={25} />
        </div>

        <div className="smart-fill-note">
          <Sparkles size={18} />
          <span>
            Introduce importes mensuales. Nosotros los anualizamos y combinamos capacidad de
            pago, ahorro y gastos de compra.
          </span>
        </div>

        <div className="form-grid">
          <NumberField
            label="Ingresos netos del hogar"
            value={monthlyIncome}
            onChange={setMonthlyIncome}
            suffix="€/mes"
            min={1}
            hint="Suma de todas las personas que comprarán."
          />
          <NumberField
            label="Ahorro disponible"
            value={savings}
            onChange={setSavings}
            suffix="€"
          />
          <NumberField
            label="Otras cuotas y préstamos"
            value={monthlyDebt}
            onChange={setMonthlyDebt}
            suffix="€/mes"
            hint="Coche, préstamos personales, tarjetas…"
          />
          <NumberField
            label="Gastos habituales"
            value={livingCosts}
            onChange={setLivingCosts}
            suffix="€/mes"
            hint="Sin incluir la vivienda que estás calculando."
          />
        </div>

        <Segmented
          label="Plazo que te planteas"
          value={term}
          onChange={setTerm}
          options={[20, 25, 30, 35].map((value) => ({ value, label: `${value} años` }))}
        />

        <button className="text-button" type="button" onClick={() => setAdvanced((value) => !value)}>
          {advanced ? 'Ocultar criterios avanzados' : 'Ajustar criterios avanzados'}
        </button>
        {advanced && (
          <div className="advanced-box form-grid">
            <NumberField
              label="Tipo estimado"
              value={rate}
              onChange={setRate}
              suffix="% TIN"
              step={0.01}
              max={30}
            />
            <NumberField
              label="Esfuerzo máximo"
              value={maxEffort}
              onChange={setMaxEffort}
              suffix="%"
              max={60}
            />
            <NumberField
              label="Financiación máxima"
              value={ltv}
              onChange={setLtv}
              suffix="%"
              max={100}
            />
            <NumberField
              label="Impuestos y gastos"
              value={purchaseCosts}
              onChange={setPurchaseCosts}
              suffix="%"
              max={30}
              step={0.5}
            />
            <NumberField
              label="Colchón a conservar"
              value={reserveMonths}
              onChange={setReserveMonths}
              suffix="meses"
              max={36}
            />
          </div>
        )}

        <button className="button button--primary button--wide" type="submit">
          Calcular mi rango <ArrowRight size={18} />
        </button>
        <div className="privacy-inline">
          <ShieldCheck size={18} /> Tus importes se calculan en el momento y no se guardan en el
          servidor.
        </div>
      </form>

      <div className="calculator-result">
        {loading && <LoadingState />}
        {error && <ErrorState message={error} />}
        {!loading && !error && !result && (
          <div className="empty-result">
            <span><PiggyBank size={30} /></span>
            <h3>Tu rango aparecerá aquí</h3>
            <p>
              Verás qué te limita más, la cuota mensual o el ahorro, sin convertirlo en una
              aprobación bancaria.
            </p>
          </div>
        )}
        {result && (
          <ResultPanel
            result={result}
            title={
              result.limiting_factor === 'available_savings'
                ? 'Tu límite principal es la entrada disponible'
                : 'Tu límite principal es la cuota mensual'
            }
            featuredKeys={[
              'max_purchase_price_eur',
              'recommended_mortgage_eur',
              'estimated_monthly_payment_eur',
              'cash_required_eur',
              'reserved_savings_eur',
              'remaining_savings_eur',
            ]}
          />
        )}
      </div>
    </div>
  )
}
