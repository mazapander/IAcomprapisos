import { useCallback, useEffect, useState } from 'react'
import {
  ArrowRight,
  BarChart3,
  BookOpenCheck,
  Building2,
  Calculator,
  ChevronRight,
  Database,
  Landmark,
  Map,
  Menu,
  MessageSquareText,
  Scale,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react'

import { getMarketSummary, track } from './api'
import BudgetCalculator from './components/BudgetCalculator'
import ConsentBanner from './components/ConsentBanner'
import MarketExplorer from './components/MarketExplorer'
import MortgageReview from './components/MortgageReview'
import OfferComparison from './components/OfferComparison'
import QuestionCenter from './components/QuestionCenter'
import { FALLBACK_GEOGRAPHIES } from './data/geographies'
import type { Geography, MarketSummary, ToolId } from './types'

const TOOLS = [
  {
    id: 'market' as const,
    title: 'Entender una zona',
    description: 'Precio, renta, esfuerzo y financiación con fuente y fecha visibles.',
    action: 'Explorar el mapa',
    icon: Map,
    tone: 'blue',
  },
  {
    id: 'budget' as const,
    title: 'Saber cuánto puedo comprar',
    description: 'Un rango sostenible según ingresos, ahorro, deudas y colchón.',
    action: 'Calcular mi rango',
    icon: Calculator,
    tone: 'green',
  },
  {
    id: 'mortgage' as const,
    title: 'Comparar ofertas',
    description: 'Fija, variable o mixta: cuota, TAE, comisiones y vinculaciones.',
    action: 'Comparar hipotecas',
    icon: Scale,
    tone: 'amber',
  },
  {
    id: 'questions' as const,
    title: 'Preparar mi negociación',
    description: 'Convierte tu caso en preguntas concretas y ayúdanos a cubrir dudas reales.',
    action: 'Plantear mi caso',
    icon: MessageSquareText,
    tone: 'violet',
  },
]

function App() {
  const [activeTool, setActiveTool] = useState<ToolId | null>(null)
  const [mobileMenu, setMobileMenu] = useState(false)
  const [mortgageMode, setMortgageMode] = useState<'compare' | 'single'>('compare')
  const [privacySignal, setPrivacySignal] = useState(0)
  const [geography, setGeography] = useState<Geography>(
    FALLBACK_GEOGRAPHIES.find((item) => item.code === 'PROV:24')!,
  )
  const [market, setMarket] = useState<MarketSummary | null>(null)

  useEffect(() => {
    getMarketSummary('PROV:24', { homeSize: 90, ltv: 80, term: 25 })
      .then(setMarket)
      .catch(() => setMarket(null))
    void track('page_view', { source: 'direct' })
  }, [])

  const updateMarketContext = useCallback(
    (context: { geography: Geography; summary: MarketSummary | null }) => {
      setGeography(context.geography)
      setMarket(context.summary)
    },
    [],
  )

  function selectTool(id: ToolId) {
    setActiveTool(id)
    setMobileMenu(false)
    void track('tool_selected', { use_case: id })
    window.setTimeout(() => document.getElementById('workspace')?.scrollIntoView({ behavior: 'smooth' }), 0)
  }

  const euribor = market?.market_card.euribor_12m_pct.value ?? undefined
  const marketApr = market?.market_card.new_mortgage_apr_pct.value ?? undefined
  const marketRate = market?.market_card.new_mortgage_tedr_pct.value ?? marketApr

  return (
    <div className="app-shell">
      <header className="site-header">
        <button className="brand" type="button" onClick={() => setActiveTool(null)} aria-label="Ir al inicio">
          <span><Building2 size={21} /></span>
          <strong>IA Compra Pisos</strong>
        </button>
        <nav className={mobileMenu ? 'is-open' : ''} aria-label="Navegación principal">
          {TOOLS.map((tool) => (
            <button key={tool.id} type="button" onClick={() => selectTool(tool.id)}>
              {tool.title}
            </button>
          ))}
          <a href="#method">Cómo funciona</a>
        </nav>
        <button className="button button--small button--dark desktop-cta" onClick={() => selectTool('mortgage')}>
          Comparar ofertas
        </button>
        <button
          className="menu-button"
          type="button"
          onClick={() => setMobileMenu((value) => !value)}
          aria-label="Abrir menú"
        >
          {mobileMenu ? <X /> : <Menu />}
        </button>
      </header>

      <main>
        {!activeTool && (
          <>
            <section className="hero-section">
              <div className="hero-copy">
                <span className="eyebrow eyebrow--hero"><Sparkles size={15} /> Información para negociar de tú a tú</span>
                <h1>Comprar una vivienda no debería significar negociar a ciegas.</h1>
                <p>
                  Bancos, entidades e intermediarios conocen el mercado mejor que quien compra.
                  Reunimos datos y herramientas para reducir esa desventaja y ayudarte a decidir,
                  comparar y preguntar con criterio.
                </p>
                <div className="hero-actions">
                  <button className="button button--primary" onClick={() => selectTool('mortgage')}>
                    Comparar mis ofertas <ArrowRight size={18} />
                  </button>
                  <button className="button button--ghost" onClick={() => selectTool('market')}>
                    Explorar una zona
                  </button>
                </div>
                <div className="trust-row">
                  <span><Database size={16} /> Fuentes oficiales</span>
                  <span><ShieldCheck size={16} /> Datos financieros sin persistencia</span>
                  <span><BookOpenCheck size={16} /> Cálculos explicables</span>
                </div>
              </div>

              <div className="hero-visual" aria-label="De la desventaja informativa a una negociación preparada">
                <div className="asymmetry-card asymmetry-card--buyer">
                  <span className="asymmetry-icon"><Building2 size={21} /></span>
                  <div>
                    <small>Quien compra</small>
                    <strong>Una decisión enorme</strong>
                    <span>Información dispersa y poco tiempo</span>
                  </div>
                </div>
                <div className="bridge-card">
                  <span><BarChart3 size={19} /></span>
                  <strong>Contexto + comparables + preguntas</strong>
                  <small>La información se convierte en capacidad de negociación</small>
                </div>
                <div className="asymmetry-card asymmetry-card--bank">
                  <span className="asymmetry-icon"><Landmark size={21} /></span>
                  <div>
                    <small>La entidad</small>
                    <strong>Miles de operaciones</strong>
                    <span>Modelos, precios y condiciones</span>
                  </div>
                </div>
              </div>
            </section>

            <section className="tool-section">
              <div className="section-heading">
                <span className="eyebrow">Empieza por tu pregunta real</span>
                <h2>No necesitas saber qué calculadora buscar</h2>
                <p>Elige la situación en la que estás y te pediremos solo la información necesaria.</p>
              </div>
              <div className="tool-grid">
                {TOOLS.map((tool) => {
                  const Icon = tool.icon
                  return (
                    <button
                      className={`tool-card tool-card--${tool.tone}`}
                      key={tool.id}
                      onClick={() => selectTool(tool.id)}
                    >
                      <span className="tool-card__icon"><Icon size={23} /></span>
                      <h3>{tool.title}</h3>
                      <p>{tool.description}</p>
                      <span className="tool-card__action">{tool.action} <ChevronRight size={17} /></span>
                    </button>
                  )
                })}
              </div>
            </section>

            <section className="method-section" id="method">
              <div>
                <span className="eyebrow">El método</span>
                <h2>De “me han ofrecido esto” a “sé qué tengo que negociar”</h2>
              </div>
              <ol>
                <li><span>01</span><strong>Contextualiza</strong><p>Entiende el territorio y el mercado financiero con fuente y periodo.</p></li>
                <li><span>02</span><strong>Normaliza</strong><p>Compara todas las ofertas con los mismos supuestos, incluidos costes ocultos.</p></li>
                <li><span>03</span><strong>Estresa</strong><p>Comprueba qué ocurre si suben los tipos o cambia tu margen mensual.</p></li>
                <li><span>04</span><strong>Negocia</strong><p>Llega a la entidad con diferencias cuantificadas y preguntas concretas.</p></li>
              </ol>
            </section>
          </>
        )}

        {activeTool && (
          <section className="workspace-section" id="workspace">
            <div className="workspace-header">
              <button className="back-link" type="button" onClick={() => setActiveTool(null)}>
                <ArrowRight size={16} /> Volver al inicio
              </button>
              <div>
                <span className="eyebrow">Herramienta activa</span>
                <h1>{TOOLS.find((tool) => tool.id === activeTool)?.title}</h1>
              </div>
              <div className="context-chip">
                <Map size={16} /> Contexto: {geography.name}
                {market ? <i className="context-chip__ok" /> : <i />}
              </div>
            </div>

            {activeTool === 'market' && <MarketExplorer onContextChange={updateMarketContext} />}
            {activeTool === 'budget' && <BudgetCalculator marketRate={marketRate} />}
            {activeTool === 'mortgage' && mortgageMode === 'compare' && (
              <OfferComparison
                euribor={euribor}
                marketApr={marketApr}
                geographyCode={geography.code}
                onSingleReview={() => setMortgageMode('single')}
              />
            )}
            {activeTool === 'mortgage' && mortgageMode === 'single' && (
              <>
                <button className="mode-switch" type="button" onClick={() => setMortgageMode('compare')}>
                  <Scale size={17} /> Volver a comparar varias ofertas
                </button>
                <MortgageReview euribor={euribor} marketApr={marketApr} geographyCode={geography.code} />
              </>
            )}
            {activeTool === 'questions' && <QuestionCenter geographyCode={geography.code} />}
          </section>
        )}
      </main>

      <footer className="site-footer">
        <div className="brand brand--footer"><span><Building2 size={19} /></span><strong>IA Compra Pisos</strong></div>
        <p>Más información para quien toma la decisión más importante.</p>
        <div>
          <button type="button" onClick={() => setPrivacySignal((value) => value + 1)}>Privacidad y medición</button>
          <a href="/docs">API</a>
        </div>
      </footer>
      <ConsentBanner settingsSignal={privacySignal} />
    </div>
  )
}

export default App
