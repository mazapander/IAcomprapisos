export type ToolId = 'observatory' | 'market' | 'budget' | 'mortgage' | 'questions'
export type RateType = 'fixed' | 'variable' | 'mixed'
export type ObservatoryGroupId = 'prices' | 'mortgages' | 'rates'

export interface Geography {
  code: string
  name: string
  level: 'country' | 'ccaa' | 'province'
  parent_code: string | null
  available: boolean
  indicator_count: number
  latest_period: string | null
}

export interface Metric {
  value: number | null
  unit: string | null
  period?: string | null
  source?: string | null
  indicator_code?: string
  geography_code?: string
  inputs?: string[]
}

export interface MarketSummary {
  geography_code: string
  generated_at: string
  assumptions: Record<string, string | number | null>
  market_card: Record<string, Metric>
  derived: Record<string, Metric | Record<string, unknown>>
  coverage: {
    available_fields: number
    total_fields: number
    ratio_pct: number
    missing_inputs: string[]
  }
}

export interface ObservatorySeries {
  code: string
  label: string
  description: string
  available: boolean
  latest: {
    value: number
    unit: string
    period: string
    source: string
  } | null
  change_previous: { value: number | null; unit: string | null }
  change_year_on_year: { value: number | null; unit: string | null }
  direction: 'up' | 'down' | 'flat' | null
  points: Array<{ period: string; value: number }>
}

export interface ObservatoryGroup {
  label: string
  description: string
  series: ObservatorySeries[]
}

export interface NationalObservatoryData {
  geography_code: 'ES'
  generated_at: string
  groups: Record<ObservatoryGroupId, ObservatoryGroup>
  coverage: {
    available_series: number
    total_series: number
    latest_period: string | null
  }
  methodology: {
    notice: string
    average_mortgage_amount: string
  }
}

export interface CalculationResult {
  status: string
  limiting_factor?: 'monthly_capacity' | 'available_savings'
  alerts: Array<{ level: string; code: string; message: string }>
  calculations: Record<string, number | null>
  assumptions: Record<string, string | number | boolean | null>
  disclaimer: string
}

export interface MortgageReviewPayload {
  property_price_eur: number
  savings_eur: number
  annual_net_household_income_eur: number
  mortgage_amount_eur: number
  rate_type: RateType
  annual_nominal_rate_pct: number
  annual_apr_pct?: number
  term_years: number
  mixed_fixed_years?: number
  variable_spread_pct?: number
  upfront_fees_eur?: number
  monthly_linked_costs_eur?: number
  existing_monthly_debt_eur: number
  monthly_living_costs_eur: number
  purchase_cost_pct: number
  stress_rate_increase_pp: number
  market_apr_pct?: number
  euribor_pct?: number
}
