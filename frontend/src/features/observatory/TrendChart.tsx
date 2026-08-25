import type { ObservatorySeries } from '../../types'
import { formatValue } from '../../shared/components/ui'

const WIDTH = 760
const HEIGHT = 260
const PAD_X = 54
const PAD_Y = 28

export default function TrendChart({ series }: { series: ObservatorySeries }) {
  const points = series.points
  if (points.length < 2 || !series.latest) {
    return <div className="observatory-chart-empty">No hay suficientes observaciones para dibujar la evolución.</div>
  }

  const values = points.map((point) => point.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const spread = max - min || 1
  const plotWidth = WIDTH - PAD_X * 2
  const plotHeight = HEIGHT - PAD_Y * 2
  const coordinates = points.map((point, index) => ({
    ...point,
    x: PAD_X + (index / (points.length - 1)) * plotWidth,
    y: PAD_Y + (1 - (point.value - min) / spread) * plotHeight,
  }))
  const polyline = coordinates.map(({ x, y }) => `${x},${y}`).join(' ')
  const first = points[0].period.slice(0, 7)
  const last = points[points.length - 1].period.slice(0, 7)

  return (
    <div className="observatory-chart" role="img" aria-label={`Evolución de ${series.label} entre ${first} y ${last}`}>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} preserveAspectRatio="none" aria-hidden="true">
        {[0, 0.5, 1].map((step) => (
          <line key={step} x1={PAD_X} x2={WIDTH - PAD_X} y1={PAD_Y + step * plotHeight} y2={PAD_Y + step * plotHeight} />
        ))}
        <polyline points={polyline} />
        <circle cx={coordinates.at(-1)!.x} cy={coordinates.at(-1)!.y} r="5" />
      </svg>
      <span className="chart-axis chart-axis--max">{formatValue(max, series.latest.unit)}</span>
      <span className="chart-axis chart-axis--min">{formatValue(min, series.latest.unit)}</span>
      <span className="chart-period chart-period--first">{first}</span>
      <span className="chart-period chart-period--last">{last}</span>
    </div>
  )
}
