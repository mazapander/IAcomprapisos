import { useMemo, useState } from 'react'

import type { ObservatorySeries } from '../../types'
import { formatValue } from '../../shared/components/ui'

const WIDTH = 760
const HEIGHT = 260
const PAD_X = 54
const PAD_Y = 28

function formatPeriod(value: string) {
  return new Intl.DateTimeFormat('es-ES', { month: 'short', year: 'numeric' })
    .format(new Date(`${value.slice(0, 7)}-01T12:00:00`))
}

export default function TrendChart({ series }: { series: ObservatorySeries }) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)
  const points = series.points
  const latest = series.latest
  const chart = useMemo(() => {
    if (points.length < 2 || !latest) return null
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
    const area = `${PAD_X},${HEIGHT - PAD_Y} ${polyline} ${WIDTH - PAD_X},${HEIGHT - PAD_Y}`
    const ticks = [0, 0.25, 0.5, 0.75, 1].map((ratio) => ({
      value: max - spread * ratio,
      y: PAD_Y + ratio * (HEIGHT - PAD_Y * 2),
    }))
    const periodTicks = [0, 0.33, 0.66, 1].map((ratio) => coordinates[Math.round(ratio * (coordinates.length - 1))])
    return { min, max, coordinates, polyline, area, ticks, periodTicks }
  }, [points, latest])

  if (!chart || !latest) {
    return <div className="observatory-chart-empty">No hay suficientes observaciones para dibujar la evolución.</div>
  }

  const activeIndex = hoveredIndex ?? points.length - 1
  const active = chart.coordinates[activeIndex]
  const first = points[0].period.slice(0, 7)
  const last = points.at(-1)!.period.slice(0, 7)

  function updateHoveredIndex(clientX: number, element: SVGSVGElement) {
    const rect = element.getBoundingClientRect()
    const progress = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
    setHoveredIndex(Math.round(progress * (points.length - 1)))
  }

  return (
    <div className="observatory-chart" aria-label={`Evolución de ${series.label} entre ${first} y ${last}`}>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        preserveAspectRatio="none"
        role="application"
        tabIndex={0}
        aria-label={`Gráfica interactiva de ${series.label}. Usa las flechas para recorrer los periodos.`}
        onPointerMove={(event) => updateHoveredIndex(event.clientX, event.currentTarget)}
        onPointerLeave={() => setHoveredIndex(null)}
        onFocus={() => setHoveredIndex(points.length - 1)}
        onBlur={() => setHoveredIndex(null)}
        onKeyDown={(event) => {
          if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return
          event.preventDefault()
          setHoveredIndex((current) => {
            const index = current ?? points.length - 1
            return Math.max(0, Math.min(points.length - 1, index + (event.key === 'ArrowLeft' ? -1 : 1)))
          })
        }}
      >
        <defs>
          <linearGradient id={`trend-area-${series.code}`} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="currentColor" stopOpacity=".27" />
            <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
          </linearGradient>
        </defs>
        {chart.ticks.map((tick) => (
          <g key={tick.y}>
            <line x1={PAD_X} x2={WIDTH - PAD_X} y1={tick.y} y2={tick.y} />
            <text className="trend-y-label" x={PAD_X - 10} y={tick.y + 4}>{formatValue(tick.value, latest.unit)}</text>
          </g>
        ))}
        {chart.periodTicks.slice(1, -1).map((point) => (
          <line className="trend-period-grid" key={point.period} x1={point.x} x2={point.x} y1={PAD_Y} y2={HEIGHT - PAD_Y} />
        ))}
        <polygon className="trend-area" points={chart.area} style={{ color: 'var(--chart-accent)' }} fill={`url(#trend-area-${series.code})`} />
        <polyline points={chart.polyline} />
        <line className="trend-cursor" x1={active.x} x2={active.x} y1={PAD_Y} y2={HEIGHT - PAD_Y} />
        <circle className="trend-point" cx={active.x} cy={active.y} r="5" />
      </svg>
      <div className="trend-tooltip" style={{ left: `${(active.x / WIDTH) * 100}%` }}>
        <strong>{formatValue(active.value, latest.unit)}</strong>
        <span>{formatPeriod(active.period)}</span>
      </div>
      <span className="chart-period chart-period--first">{first}</span>
      <span className="chart-period chart-period--last">{last}</span>
      <span className="chart-source">Serie oficial · fuente y periodo verificables</span>
      <span className="sr-only" aria-live="polite">{formatPeriod(active.period)}: {formatValue(active.value, latest.unit)}</span>
    </div>
  )
}
