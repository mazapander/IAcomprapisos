# Banco de España — Euríbor a 12 meses

## Estado

Implementado en `app/ingestion/sources/bde_euribor.py`.

## Identificación oficial

- Organismo: Banco de España.
- Página temática: `https://www.bde.es/webbe/es/estadisticas/temas/tipos-interes.html`.
- Bloque: Tipos de referencia — tipos de interés legales, euríbor, míbor y otros tipos oficiales de referencia.
- Descarga CSV oficial: `https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/be1901.csv`.
- Dataset interno: `bde_be1901_reference_rates`.
- Frecuencia nativa usada: mensual.
- Geografía: España (`ES`).
- Unidad: porcentaje.

## Respuesta y parser

El CSV puede incluir filas descriptivas antes de la cabecera y usar delimitadores o formatos españoles. El parser:

1. Detecta el delimitador entre `;`, `,`, tabulador o `|`.
2. Busca una columna cuyo título contenga `Euríbor` y `un año`, `1 año` o `12 meses`.
3. Busca el periodo en las primeras columnas de cada fila.
4. Soporta fechas ISO, `MM/YYYY` y meses abreviados en español.
5. Convierte coma decimal y elimina `%`.
6. Ignora celdas vacías o marcadores sin dato.

La fila original y la cabecera detectada se conservan en raw para poder depurar cambios de formato.

## Mapeo canónico

| Serie oficial | Indicador analytics | Frecuencia | Unidad |
|---|---|---|---|
| Euríbor a un año | `euribor_12m_pct` | `monthly` | `percent` |

## Ejecución

```json
{
  "requested_by": "n8n-monthly",
  "parameters": {
    "date_from": "1999-01-01",
    "date_to": "2026-06-01"
  }
}
```

El parámetro opcional `url` permite probar una copia controlada o fixture sin cambiar el código, aunque producción debe utilizar la URL oficial por defecto.

## Persistencia

En `raw.source_records` se guarda:

- Página oficial.
- URL final de descarga.
- Estado HTTP.
- Content-Type.
- Periodo.
- Valor original normalizado como cadena.
- Cabecera detectada.
- Fila original.
- Fecha de recuperación.

En `analytics.indicator_observations` se guarda una observación mensual con `geography_code = ES`.

## Riesgos conocidos

- El Banco de España puede cambiar la estructura del CSV manteniendo el mismo enlace.
- Una cabecera multinivel podría requerir combinar varias filas; el test de contrato debe alertar si deja de localizarse la serie.
- Debemos capturar explícitamente la fecha de publicación cuando se implemente el calendario de disponibilidad point-in-time.
- El valor mensual no debe mezclarse con valores diarios de mercado sin distinguir indicador y frecuencia.
