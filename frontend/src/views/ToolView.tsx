import { useState } from 'react'
import { ArrowRight, Map, Scale } from 'lucide-react'

import { toolById } from '../app/toolCatalog'
import BudgetCalculator from '../features/budget/BudgetCalculator'
import MarketExplorer from '../features/market/MarketExplorer'
import MarketObservationForm from '../features/market-data/MarketObservationForm'
import MortgageReview from '../features/mortgages/MortgageReview'
import OfferComparison from '../features/mortgages/OfferComparison'
import NationalObservatory from '../features/observatory/NationalObservatory'
import QuestionCenter from '../features/questions/QuestionCenter'
import type { Geography, MarketSummary, ToolId } from '../types'

interface ToolViewProps {
  activeTool: ToolId
  geography: Geography
  market: MarketSummary | null
  onBack: () => void
  onMarketContext: (context: { geography: Geography; summary: MarketSummary | null }) => void
}

export default function ToolView({ activeTool, geography, market, onBack, onMarketContext }: ToolViewProps) {
  const [mortgageMode, setMortgageMode] = useState<'compare' | 'single'>('compare')
  const tool = toolById(activeTool)
  const euribor = market?.market_card.euribor_12m_pct.value ?? undefined
  const marketApr = market?.market_card.new_mortgage_apr_pct.value ?? undefined
  const marketRate = market?.market_card.new_mortgage_tedr_pct.value ?? marketApr

  return (
    <section className="workspace-section" id="workspace">
      <div className="workspace-header">
        <button className="back-link" type="button" onClick={onBack}><ArrowRight size={16} /> Volver al inicio</button>
        <div><span className="eyebrow">Herramienta activa</span><h1>{tool.title}</h1></div>
        <div className="context-chip">
          <Map size={16} /> {activeTool === 'observatory' ? 'Contexto: España' : `Contexto: ${geography.name}`}
          <i className={activeTool === 'observatory' || market ? 'context-chip__ok' : ''} />
        </div>
      </div>

      {activeTool === 'observatory' && <NationalObservatory />}
      {activeTool === 'market' && <MarketExplorer onContextChange={onMarketContext} />}
      {activeTool === 'market-data' && <MarketObservationForm geographyCode={geography.code} geographyName={geography.name} />}
      {activeTool === 'budget' && <BudgetCalculator marketRate={marketRate} />}
      {activeTool === 'mortgage' && mortgageMode === 'compare' && (
        <OfferComparison euribor={euribor} marketApr={marketApr} geographyCode={geography.code} onSingleReview={() => setMortgageMode('single')} />
      )}
      {activeTool === 'mortgage' && mortgageMode === 'single' && (
        <>
          <button className="mode-switch" type="button" onClick={() => setMortgageMode('compare')}><Scale size={17} /> Volver a comparar varias ofertas</button>
          <MortgageReview euribor={euribor} marketApr={marketApr} geographyCode={geography.code} />
        </>
      )}
      {activeTool === 'questions' && <QuestionCenter geographyCode={geography.code} />}
    </section>
  )
}
