import type { Geography } from '../../types'

type RegionShape = {
  code: string
  label: string
  d: string
}

// A lightweight, hand-drawn geographic silhouette keeps the interaction local and
// accessible. Provinces remain available in the selector below the map.
const REGIONS: RegionShape[] = [
  { code: 'CCAA:12', label: 'Galicia', d: 'M45 103 L69 84 94 91 106 112 99 132 72 137 51 125Z' },
  { code: 'CCAA:03', label: 'Asturias', d: 'M105 83 L151 75 165 86 157 99 119 102Z' },
  { code: 'CCAA:06', label: 'Cantabria', d: 'M165 78 L198 75 209 88 199 99 169 97Z' },
  { code: 'CCAA:16', label: 'País Vasco', d: 'M207 74 L241 77 251 94 234 105 208 96Z' },
  { code: 'CCAA:15', label: 'Navarra', d: 'M247 85 L274 86 286 112 271 129 248 114Z' },
  { code: 'CCAA:17', label: 'La Rioja', d: 'M215 102 L247 108 251 124 224 129 207 119Z' },
  { code: 'CCAA:07', label: 'Castilla y León', d: 'M106 105 L205 98 222 128 209 166 160 175 111 157 91 129Z' },
  { code: 'CCAA:02', label: 'Aragón', d: 'M274 106 L318 96 342 128 326 190 288 182 267 140Z' },
  { code: 'CCAA:09', label: 'Cataluña', d: 'M320 86 L370 73 402 103 393 144 365 157 342 129Z' },
  { code: 'CCAA:11', label: 'Extremadura', d: 'M103 159 L158 176 157 224 126 247 94 225 83 185Z' },
  { code: 'CCAA:13', label: 'Comunidad de Madrid', d: 'M192 165 L218 169 225 193 203 205 181 188Z' },
  { code: 'CCAA:08', label: 'Castilla-La Mancha', d: 'M158 177 L207 167 245 190 278 202 269 257 205 276 156 237Z' },
  { code: 'CCAA:10', label: 'Comunitat Valenciana', d: 'M326 174 L356 157 374 185 364 246 338 272 315 240Z' },
  { code: 'CCAA:14', label: 'Región de Murcia', d: 'M304 241 L338 267 326 293 298 284Z' },
  { code: 'CCAA:01', label: 'Andalucía', d: 'M123 248 L168 229 207 275 267 259 301 285 283 320 224 335 172 320 135 292Z' },
  { code: 'CCAA:04', label: 'Illes Balears', d: 'M423 169 L439 158 451 167 445 180 431 181ZM458 195 L469 188 477 198 469 208Z' },
  { code: 'CCAA:05', label: 'Canarias', d: 'M45 327 L59 320 69 328 61 339ZM82 345 L100 337 113 349 99 358ZM122 326 L136 320 147 331 137 341Z' },
  { code: 'CCAA:18', label: 'Ceuta', d: 'M267 347 L278 345 282 351 271 354Z' },
  { code: 'CCAA:19', label: 'Melilla', d: 'M300 347 L311 344 316 350 304 353Z' },
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
  const selectedRegion = selectedCode.startsWith('CCAA:') ? selectedCode : geographies.get(selectedCode)?.parent_code

  return (
    <div className="spain-map" aria-label="Mapa interactivo de comunidades autónomas">
      <svg viewBox="0 0 500 375" role="group" aria-label="Selecciona una comunidad autónoma">
        <path className="spain-map__sea" d="M21 55 H420 Q469 76 477 137 V294 Q452 360 350 369 H43 Q16 340 16 291 V92Q16 67 21 55Z" />
        {REGIONS.map((region) => {
          const geography = geographies.get(region.code)
          const active = selectedRegion === region.code
          return (
            <path
              key={region.code}
              d={region.d}
              className={`spain-map__region ${active ? 'is-active' : ''} ${geography?.available ? 'has-data' : ''}`}
              role="button"
              tabIndex={0}
              aria-label={`Seleccionar ${geography?.name ?? region.label}`}
              aria-pressed={active}
              onClick={() => geography && onSelect(geography)}
              onKeyDown={(event) => {
                if ((event.key === 'Enter' || event.key === ' ') && geography) {
                  event.preventDefault()
                  onSelect(geography)
                }
              }}
            >
              <title>{geography?.name ?? region.label}</title>
            </path>
          )
        })}
      </svg>
      <div className="spain-map__legend"><i /> Cobertura directa disponible</div>
    </div>
  )
}
