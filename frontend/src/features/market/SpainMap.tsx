import { useEffect, useRef, useState } from 'react'

import type { Geography } from '../../types'
import spainMapUrl from '../../data/Blank_Spain_Map_(Autonomous_Communities).svg'

type RegionPath = {
  code: string
  label: string
  elementId: string
}

// IDs from the supplied source artwork. Interactions are applied to the actual
// territory paths — no second, approximate map is rendered above the SVG.
const REGIONS: RegionPath[] = [
  { code: 'CCAA:12', label: 'Galicia', elementId: '_127780568' },
  { code: 'CCAA:03', label: 'Asturias', elementId: '_128682832' },
  { code: 'CCAA:06', label: 'Cantabria', elementId: '_129423256' },
  { code: 'CCAA:16', label: 'País Vasco', elementId: '_127677112' },
  { code: 'CCAA:17', label: 'La Rioja', elementId: '_129181960' },
  { code: 'CCAA:15', label: 'Navarra', elementId: '_129786416' },
  { code: 'CCAA:07', label: 'Castilla y León', elementId: '_130150024' },
  { code: 'CCAA:02', label: 'Aragón', elementId: '_129253112' },
  { code: 'CCAA:09', label: 'Cataluña', elementId: '_129272280' },
  { code: 'CCAA:11', label: 'Extremadura', elementId: '_129003504' },
  { code: 'CCAA:13', label: 'Comunidad de Madrid', elementId: '_130150096' },
  { code: 'CCAA:08', label: 'Castilla-La Mancha', elementId: '_129252504' },
  { code: 'CCAA:10', label: 'Comunitat Valenciana', elementId: '_129182272' },
  { code: 'CCAA:14', label: 'Región de Murcia', elementId: '_128683144' },
  { code: 'CCAA:01', label: 'Andalucía', elementId: '_128681296' },
  { code: 'CCAA:04', label: 'Illes Balears', elementId: '_128752360' },
  { code: 'CCAA:05', label: 'Canarias', elementId: '_129811768' },
  { code: 'CCAA:18', label: 'Ceuta', elementId: '_128750616' },
  { code: 'CCAA:19', label: 'Melilla', elementId: '_129003024' },
]

export default function SpainMap({
  geographies,
  selectedCode,
  onSelect,
}: {
  geographies: Map<string, Geography>
  selectedCode: string
  onSelect: (geography: Geography) => void
}) {
  const artworkRef = useRef<HTMLObjectElement>(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  const selectedRegion = selectedCode.startsWith('CCAA:') ? selectedCode : geographies.get(selectedCode)?.parent_code

  useEffect(() => {
    const document = artworkRef.current?.contentDocument
    if (!document || !mapLoaded) return
    const cleanup: Array<() => void> = []

    for (const region of REGIONS) {
      const path = document.querySelector<SVGPathElement | SVGPolygonElement>(`#${region.elementId}`)
      const geography = geographies.get(region.code)
      if (!path) continue
      path.setAttribute('tabindex', geography ? '0' : '-1')
      path.setAttribute('role', 'button')
      path.setAttribute('aria-label', `Seleccionar ${geography?.name ?? region.label}`)
      path.setAttribute('aria-pressed', String(selectedRegion === region.code))
      path.style.cursor = geography ? 'pointer' : 'default'

      const applyStyle = (hovered = false) => {
        const active = selectedRegion === region.code
        path.style.setProperty('fill', active ? '#75b08b' : hovered ? '#b5d93b' : geography?.available ? '#d8e7bd' : '#d4dbd2', 'important')
        path.style.setProperty('stroke', active ? '#0d1612' : hovered ? '#264333' : '#f8fbf5', 'important')
        path.style.setProperty('stroke-width', active ? '3.2' : hovered ? '2.4' : '1.15', 'important')
      }
      applyStyle()

      const select = () => geography && onSelect(geography)
      const keyDown = (event: Event) => {
        const key = (event as KeyboardEvent).key
        if (key === 'Enter' || key === ' ') {
          event.preventDefault()
          select()
        }
      }
      const enter = () => geography && applyStyle(true)
      const leave = () => applyStyle()
      path.addEventListener('click', select)
      path.addEventListener('keydown', keyDown)
      path.addEventListener('mouseenter', enter)
      path.addEventListener('mouseleave', leave)
      cleanup.push(() => {
        path.removeEventListener('click', select)
        path.removeEventListener('keydown', keyDown)
        path.removeEventListener('mouseenter', enter)
        path.removeEventListener('mouseleave', leave)
      })
    }
    return () => cleanup.forEach((remove) => remove())
  }, [geographies, mapLoaded, onSelect, selectedRegion])

  return (
    <div className="spain-map" aria-label="Mapa interactivo de comunidades autónomas">
      <object
        className="spain-map__artwork"
        ref={artworkRef}
        data={spainMapUrl}
        type="image/svg+xml"
        aria-label="Mapa de España por comunidades autónomas"
        onLoad={() => setMapLoaded(true)}
      />
      <div className="spain-map__legend"><i /> Pulsa una comunidad para abrir su contexto</div>
    </div>
  )
}
