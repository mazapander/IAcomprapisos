import {
  ArrowRight,
  BookOpenCheck,
  ChevronRight,
  Database,
  Map,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

import { TOOLS } from '../app/toolCatalog'
import MarketPulse from '../features/observatory/MarketPulse'
import type { ToolId } from '../types'

export default function HomeView({ onSelect }: { onSelect: (id: ToolId) => void }) {
  return (
    <>
      <section className="hero-section">
        <div className="hero-copy">
          <span className="eyebrow eyebrow--hero"><Sparkles size={15} /> El radar de quien compra</span>
          <h1>Que el mercado no juegue en tu contra.</h1>
          <p>
            Precio, zona, hipoteca y condiciones de la oferta: el contexto que necesitas para
            tomar una decisión grande y sentarte delante de una entidad con mejores preguntas.
          </p>
          <div className="hero-actions">
            <button className="button button--dark hero-primary" onClick={() => onSelect('market')}>
              Explorar una zona <ArrowRight size={18} />
            </button>
            <button className="button button--ghost" onClick={() => onSelect('mortgage')}>
              Comparar una oferta
            </button>
          </div>
          <div className="trust-row">
            <span><Database size={16} /> Fuentes oficiales</span>
            <span><ShieldCheck size={16} /> Datos financieros sin persistencia</span>
            <span><BookOpenCheck size={16} /> Cálculos explicables</span>
          </div>
        </div>

        <div className="hero-visual hero-visual--editorial" aria-label="Resumen de las herramientas disponibles">
          <div className="hero-visual__topline"><span>Decide con contexto</span><i /></div>
          <div className="hero-visual__number">01</div>
          <div className="hero-visual__statement">
            <Map size={23} />
            <p>Elige un territorio, mira las series y lleva una referencia a la conversación.</p>
          </div>
          <div className="hero-visual__route">
            <span>Mapa</span><span>Mercado</span><span>Oferta</span><span>Preguntas</span>
          </div>
        </div>
      </section>

      <MarketPulse />

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
              <button className={`tool-card tool-card--${tool.tone}`} key={tool.id} onClick={() => onSelect(tool.id)}>
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
        <div><span className="eyebrow">El método</span><h2>De “me han ofrecido esto” a “sé qué tengo que negociar”</h2></div>
        <ol>
          <li><span>01</span><strong>Observa</strong><p>Sigue precios, hipotecas y tipos con su fuente y periodo real.</p></li>
          <li><span>02</span><strong>Contextualiza</strong><p>Entiende el territorio y el mercado financiero de la operación.</p></li>
          <li><span>03</span><strong>Normaliza</strong><p>Compara todas las ofertas con los mismos supuestos y costes.</p></li>
          <li><span>04</span><strong>Negocia</strong><p>Llega a la entidad con diferencias cuantificadas y preguntas concretas.</p></li>
        </ol>
      </section>
    </>
  )
}
