import type {
  CalculationResult,
  Geography,
  MarketSummary,
  MortgageReviewPayload,
  NationalObservatoryData,
} from './types'

const API_ROOT = '/api/v1'

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, init)
  if (!response.ok) {
    let detail = 'No hemos podido completar la consulta.'
    try {
      const body = await response.json()
      detail = typeof body.detail === 'string' ? body.detail : detail
    } catch {
      // Preserve the human-readable fallback when the proxy does not return JSON.
    }
    throw new ApiError(detail, response.status)
  }
  return response.json() as Promise<T>
}

export async function getGeographies(): Promise<Geography[]> {
  const result = await request<{ items: Geography[] }>('/markets/geographies')
  return result.items
}

export function getMarketSummary(
  geographyCode: string,
  assumptions: { homeSize: number; ltv: number; term: number },
) {
  const params = new URLSearchParams({
    home_size_m2: String(assumptions.homeSize),
    ltv_pct: String(assumptions.ltv),
    term_years: String(assumptions.term),
  })
  return request<MarketSummary>(
    `/markets/${encodeURIComponent(geographyCode)}/summary?${params.toString()}`,
  )
}

export function getNationalObservatory(years = 10) {
  return request<NationalObservatoryData>(`/markets/observatory/national?years=${years}`)
}

export function calculateBudget(payload: Record<string, number>) {
  return request<CalculationResult>('/mortgages/budget', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function reviewMortgage(payload: MortgageReviewPayload) {
  return request<CalculationResult>('/mortgages/review', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function submitQuestion(payload: Record<string, unknown>) {
  return request<{ id: string; status: string }>('/product/questions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

function readCookie(name: string) {
  return document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`))
    ?.split('=')[1]
}

const SESSION_KEY = 'iacomprapisos.session'

function sessionId() {
  const saved = sessionStorage.getItem(SESSION_KEY)
  if (saved) return saved
  const created = crypto.randomUUID()
  sessionStorage.setItem(SESSION_KEY, created)
  return created
}

export function analyticsConsent() {
  return readCookie('iacp_consent') as 'accepted' | 'rejected' | undefined
}

export async function setAnalyticsConsent(choice: 'accepted' | 'rejected') {
  await request('/product/consent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ choice }),
  })
}

export async function track(
  event_name: string,
  properties: Record<string, string | number | boolean> = {},
) {
  if (analyticsConsent() !== 'accepted') return
  try {
    await request('/product/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_name,
        session_id: sessionId(),
        page_path: window.location.pathname,
        properties,
      }),
    })
  } catch {
    // Analytics must never interrupt the decision tools.
  }
}
