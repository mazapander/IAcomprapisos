import {
  ArrowRight,
  BarChart3,
  BookOpenCheck,
  Building2,
  ChevronRight,
  Database,
  Landmark,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

import { TOOLS } from '../app/toolCatalog'
import type { ToolId } from '../types'

export default function HomeView({ onSelect }: { onSelect: (id: ToolId) => void }) {
  return (
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
            <button className="button button--primary" onClick={() => onSelect('mortgage')}>
              Comparar mis ofertas <ArrowRight size={18} />
            </button>
            <button className="button button--ghost" onClick={() => onSelect('observatory')}>
              Ver el mercado estatal
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
            <div><small>Quien compra</small><strong>Una decisión enorme</strong><span>Información dispersa y poco tiempo</span></div>
          </div>
          <div className="bridge-card">
            <span><BarChart3 size={19} /></span>
            <strong>Contexto + comparables + preguntas</strong>
            <small>La información se convierte en capacidad de negociación</small>
          </div>
          <div className="asymmetry-card asymmetry-card--bank">
            <span className="asymmetry-icon"><Landmark size={21} /></span>
            <div><small>La entidad</small><strong>Miles de operaciones</strong><span>Modelos, precios y condiciones</span></div>
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
