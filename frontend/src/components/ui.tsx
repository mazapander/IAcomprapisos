import type { ReactNode } from 'react'
import { AlertCircle, CheckCircle2, Info, LoaderCircle } from 'lucide-react'

import type { CalculationResult, Metric } from '../types'

export function Field({
  label,
  hint,
  children,
  className = '',
}: {
  label: string
  hint?: string
  children: ReactNode
  className?: string
}) {
  return (
    <label className={`field ${className}`}>
      <span className="field__label">{label}</span>
      {children}
      {hint && <small className="field__hint">{hint}</small>}
    </label>
  )
}

export function NumberField({
  label,
  value,
  onChange,
  suffix,
  hint,
  min = 0,
  max,
  step = 1,
}: {
  label: string
  value: number
  onChange: (value: number) => void
  suffix?: string
  hint?: string
  min?: number
  max?: number
  step?: number
}) {
  return (
    <Field label={label} hint={hint}>
      <span className="number-input">
        <input
          type="number"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(event) => onChange(Number(event.target.value))}
        />
        {suffix && <span>{suffix}</span>}
      </span>
    </Field>
  )
}

export function Segmented<T extends string | number>({
  label,
  options,
  value,
  onChange,
}: {
  label: string
  options: Array<{ value: T; label: string; description?: string }>
  value: T
  onChange: (value: T) => void
}) {
  return (
    <fieldset className="segmented-field">
      <legend>{label}</legend>
      <div className="segmented">
        {options.map((option) => (
          <button
            className={value === option.value ? 'is-active' : ''}
            key={option.value}
            type="button"
            aria-pressed={value === option.value}
            onClick={() => onChange(option.value)}
          >
            <strong>{option.label}</strong>
            {option.description && <small>{option.description}</small>}
          </button>
        ))}
      </div>
    </fieldset>
  )
}

export function LoadingState({ label = 'Calculando…' }: { label?: string }) {
  return (
    <div className="status-box" aria-live="polite">
      <LoaderCircle className="spin" size={20} /> {label}
    </div>
  )
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="status-box status-box--error" role="alert">
      <AlertCircle size={20} />
      <span>{message}</span>
    </div>
  )
}

const METRIC_LABELS: Record<string, string> = {
  price_eur_m2: 'Precio de referencia',
  annual_household_net_income_eur: 'Renta neta del hogar',
  salary_income_weight_pct: 'Peso de los salarios',
  mortgages_yoy_pct: 'Evolución de hipotecas',
  new_mortgage_apr_pct: 'TAE de nuevas hipotecas',
  new_mortgage_tedr_pct: 'TEDR de nuevas hipotecas',
  new_financing_volume_eur: 'Financiación nueva',
  euribor_12m_pct: 'Euríbor a 12 meses',
  estimated_purchase_effort_pct: 'Esfuerzo estimado',
  mortgage_spread_pp: 'Diferencial de mercado',
  price_to_income_years: 'Precio / renta',
  price_to_rent_years: 'Precio / alquiler',
  income_adjusted_price_yoy_pct: 'Precio ajustado por renta',
  monthly_payment_eur: 'Cuota inicial',
  post_fixed_monthly_payment_eur: 'Cuota tras el tramo fijo',
  stressed_monthly_payment_eur: 'Cuota en escenario de estrés',
  effort_pct: 'Esfuerzo actual',
  stressed_effort_pct: 'Esfuerzo con tipos al alza',
  committed_income_pct: 'Ingresos comprometidos',
  ltv_pct: 'Financiación sobre precio',
  cash_required_eur: 'Entrada y gastos',
  remaining_savings_eur: 'Ahorro restante',
  emergency_buffer_months: 'Colchón restante',
  total_interest_eur: 'Intereses estimados',
  upfront_fees_eur: 'Comisiones iniciales',
  linked_costs_total_eur: 'Vinculaciones durante el plazo',
  estimated_total_cost_eur: 'Coste financiero comparable',
  apr_vs_market_pp: 'TAE frente al mercado',
  max_purchase_price_eur: 'Precio de compra orientativo',
  recommended_mortgage_eur: 'Hipoteca estimada',
  estimated_monthly_payment_eur: 'Cuota estimada',
  reserved_savings_eur: 'Colchón reservado',
  max_monthly_payment_eur: 'Cuota máxima elegida',
}

export function formatValue(value: number | null, unit?: string | null, key?: string) {
  if (value == null) return 'Sin dato'
  const number = new Intl.NumberFormat('es-ES', {
    maximumFractionDigits: unit === 'eur' || unit === 'eur_m2' ? 0 : 1,
  }).format(value)
  if (unit === 'eur_m2') return `${number} €/m²`
  if (unit === 'eur_year') return `${number} €/año`
  if (unit === 'eur' || key?.endsWith('_eur')) return `${number} €`
  if (unit === 'percent' || key?.endsWith('_pct')) return `${number} %`
  if (unit === 'percentage_points' || key?.endsWith('_pp')) return `${number} pp`
  if (unit === 'years') return `${number} años`
  if (unit === 'months' || key?.endsWith('_months')) return `${number} meses`
  return number
}

export function MetricCard({ metricKey, metric }: { metricKey: string; metric: Metric }) {
  const hasSource = metric.period || metric.source
  return (
    <article className={`metric-card ${metric.value == null ? 'metric-card--empty' : ''}`}>
      <span>{METRIC_LABELS[metricKey] ?? metricKey}</span>
      <strong>{formatValue(metric.value, metric.unit, metricKey)}</strong>
      <small>
        {hasSource
          ? [metric.period?.slice(0, 7), metric.source].filter(Boolean).join(' · ')
          : metric.value == null
            ? 'Pendiente de cobertura'
            : 'Cálculo orientativo'}
      </small>
    </article>
  )
}

export function ResultPanel({
  result,
  title,
  featuredKeys,
}: {
  result: CalculationResult
  title: string
  featuredKeys: string[]
}) {
  const positive = result.status === 'balanced' || result.status === 'estimated'
  return (
    <section className="result-panel" aria-live="polite">
      <div className="result-panel__heading">
        <span className={`result-icon ${positive ? 'result-icon--positive' : ''}`}>
          {positive ? <CheckCircle2 size={22} /> : <Info size={22} />}
        </span>
        <div>
          <span className="eyebrow">Resultado orientativo</span>
          <h3>{title}</h3>
        </div>
      </div>
      {result.alerts.length > 0 && (
        <ul className="alert-list">
          {result.alerts.map((alert) => (
            <li key={alert.code} data-level={alert.level}>
              <AlertCircle size={17} /> {alert.message}
            </li>
          ))}
        </ul>
      )}
      <div className="metrics-grid metrics-grid--results">
        {featuredKeys.map((key) => (
          <MetricCard
            key={key}
            metricKey={key}
            metric={{ value: result.calculations[key] ?? null, unit: null }}
          />
        ))}
      </div>
      <p className="disclaimer">{result.disclaimer}</p>
    </section>
  )
}
