import { useState } from 'react'
import {
  ArrowRight,
  BadgeEuro,
  Banknote,
  CheckCircle2,
  CircleHelp,
  FileSearch,
  Landmark,
  MapPinned,
  MessageSquareText,
  RefreshCcw,
  ShieldCheck,
} from 'lucide-react'

import { submitQuestion, track } from '../../api'
import { ErrorState, LoadingState, Segmented } from '../../shared/components/ui'

const CATEGORIES = [
  { value: 'affordability', label: 'Qué puedo permitirme', icon: Banknote },
  { value: 'offer', label: 'Si mi oferta es buena', icon: BadgeEuro },
  { value: 'mixed_mortgage', label: 'Hipoteca mixta', icon: Landmark },
  { value: 'early_repayment', label: 'Amortizar o cambiar', icon: RefreshCcw },
  { value: 'costs', label: 'Entrada, impuestos y gastos', icon: FileSearch },
  { value: 'market', label: 'Mercado de una zona', icon: MapPinned },
  { value: 'process', label: 'Proceso y negociación', icon: MessageSquareText },
  { value: 'other', label: 'Otra duda', icon: CircleHelp },
] as const

export default function QuestionCenter({ geographyCode }: { geographyCode: string }) {
  const [category, setCategory] = useState<(typeof CATEGORIES)[number]['value']>('offer')
  const [stage, setStage] = useState('comparing')
  const [question, setQuestion] = useState('')
  const [privacy, setPrivacy] = useState(false)
  const [email, setEmail] = useState('')
  const [contactConsent, setContactConsent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [sent, setSent] = useState(false)

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await submitQuestion({
        question,
        category,
        journey_stage: stage,
        geography_code: geographyCode || null,
        contact_email: email || null,
        contact_consent: Boolean(email) && contactConsent,
        privacy_notice_accepted: privacy,
      })
      setSent(true)
      setQuestion('')
      void track('question_submitted', {
        geography_code: geographyCode,
        question_category: category,
      })
    } catch {
      setError('No hemos podido guardar la consulta. Revisa el consentimiento y vuelve a intentarlo.')
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
    return (
      <section className="panel question-success">
        <span><CheckCircle2 size={30} /></span>
        <h2>Consulta recibida</h2>
        <p>
          La usaremos para entender qué información falta a los compradores y priorizar nuevas
          explicaciones y herramientas.
        </p>
        <button className="button button--secondary" type="button" onClick={() => setSent(false)}>
          Enviar otra duda
        </button>
      </section>
    )
  }

  return (
    <form className="panel question-form" onSubmit={submit}>
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Centro de dudas</span>
          <h2>¿Qué necesitas saber para hablar de tú a tú?</h2>
          <p>
            No hace falta que sepas formular la pregunta “correcta”. Clasificamos la necesidad y
            guardamos la duda para mejorar el producto.
          </p>
        </div>
        <MessageSquareText size={25} />
      </div>

      <fieldset className="category-picker">
        <legend>Elige lo que más se parece a tu caso</legend>
        <div>
          {CATEGORIES.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.value}
                type="button"
                className={category === item.value ? 'is-active' : ''}
                aria-pressed={category === item.value}
                onClick={() => {
                  setCategory(item.value)
                  void track('question_started', { question_category: item.value })
                }}
              >
                <Icon size={19} /> {item.label}
              </button>
            )
          })}
        </div>
      </fieldset>

      <Segmented
        label="¿En qué punto estás?"
        value={stage}
        onChange={setStage}
        options={[
          { value: 'exploring', label: 'Explorando' },
          { value: 'comparing', label: 'Comparando' },
          { value: 'offer_received', label: 'Con una oferta' },
          { value: 'ready_to_sign', label: 'Antes de firmar' },
        ]}
      />

      <label className="field question-textarea">
        <span className="field__label">Cuéntanos la situación con tus palabras</span>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          minLength={5}
          maxLength={2000}
          required
          placeholder="Por ejemplo: me ofrecen cinco años al 2,1 % y después Euríbor + 0,7 %, pero no sé cómo compararlo con una fija…"
        />
        <small className="field__hint">
          No incluyas DNI, cuenta bancaria, dirección completa ni documentación privada.
        </small>
      </label>

      <details className="contact-details">
        <summary>Quiero que podáis responderme</summary>
        <label className="field">
          <span className="field__label">Correo electrónico</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="tu@email.com"
          />
        </label>
        {email && (
          <label className="check-row">
            <input
              type="checkbox"
              checked={contactConsent}
              onChange={(event) => setContactConsent(event.target.checked)}
              required
            />
            <span>Acepto que uséis este correo únicamente para responder a esta consulta.</span>
          </label>
        )}
      </details>

      <label className="check-row">
        <input
          type="checkbox"
          checked={privacy}
          onChange={(event) => setPrivacy(event.target.checked)}
          required
        />
        <span>
          <strong>Acepto que se guarde esta consulta</strong>
          <small>
            Se analizará para identificar dudas frecuentes y mejorar el servicio según el aviso
            de privacidad.
          </small>
        </span>
      </label>

      {loading && <LoadingState label="Enviando consulta…" />}
      {error && <ErrorState message={error} />}
      <div className="form-submit-row">
        <span className="privacy-inline"><ShieldCheck size={18} /> Consentimiento separado de la analítica.</span>
        <button className="button button--primary" type="submit" disabled={loading}>
          Enviar mi duda <ArrowRight size={18} />
        </button>
      </div>
    </form>
  )
}
