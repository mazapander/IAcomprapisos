# INE — Compraventa de viviendas

## Estado

Implementado en `app/ingestion/sources/ine_transmissions.py`.

## Identificación oficial

- Organismo: Instituto Nacional de Estadística.
- Operación: Estadística de Transmisiones de Derechos de la Propiedad.
- Tabla: `6150` — Compraventa de viviendas según régimen y estado.
- Página humana: `https://www.ine.es/jaxiT3/Tabla.htm?t=6150`.
- Endpoint JSON utilizado: `https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/6150`.
- Parámetro por defecto: `tip=AM`.
- Frecuencia nativa: mensual.
- Unidad: viviendas/transacciones.
- Cobertura geográfica: total nacional, comunidades autónomas y provincias.
- Cobertura visible en la tabla en la revisión de julio de 2026: desde 2007M01 hasta 2026M04.

## Dimensiones

La tabla contiene:

1. Comunidad autónoma o provincia.
2. Régimen y estado:
   - Viviendas: total.
   - Vivienda nueva.
   - Vivienda usada.
   - Vivienda libre.
   - Vivienda protegida.
3. Periodo mensual.

## Forma esperada de la respuesta

El endpoint devuelve una lista de series. Cada serie contiene metadatos (`COD`, `Nombre`, unidad y escala, según disponibilidad) y una colección `Data` de observaciones. Las observaciones incluyen el valor y campos temporales que pueden variar entre respuestas de Tempus.

El parser acepta:

- `Nombre` o `name`.
- `COD` o `code`.
- `Data` o `data`.
- Periodos `YYYYMmm`, combinación año/mes o timestamp `Fecha`.
- Valores numéricos o cadenas con coma decimal.

## Mapeo canónico

| Categoría INE | Indicador analytics | Unidad |
|---|---|---|
| Viviendas: Total | `housing_sales_total` | `transactions` |
| Vivienda nueva | `housing_sales_new` | `transactions` |
| Vivienda usada | `housing_sales_used` | `transactions` |
| Vivienda libre | `housing_sales_free_market` | `transactions` |
| Vivienda protegida | `housing_sales_protected` | `transactions` |

## Geografía

- Nacional: `ES`.
- Comunidad autónoma: `CCAA:<código INE>`.
- Provincia: `PROV:<código INE>`.

La normalización se hace sobre nombres y códigos publicados en la tabla. La dimensión geográfica definitiva deberá poblar `analytics.geographies` y sustituir progresivamente los mapas internos por aliases versionados.

## Persistencia

Cada observación original se guarda en `raw.source_records`, incluyendo:

- URL concreta consultada.
- Código y nombre de serie.
- Metadatos completos de la serie.
- Observación original.
- Fecha de recuperación.

La transformación produce una observación mensual en `analytics.indicator_observations` sin modificar su frecuencia nativa.

## Parámetros de ejecución

```json
{
  "requested_by": "n8n-monthly",
  "parameters": {
    "date_from": "2020-01-01",
    "date_to": "2026-04-01",
    "tip": "AM"
  }
}
```

## Riesgos conocidos

- El texto de `Nombre` puede cambiar y debe vigilarse mediante tests de contrato.
- Los datos recientes pueden ser provisionales.
- INE puede revisar valores históricos; raw conservará cada respuesta y analytics mantendrá el último valor procesado.
- Debe añadirse una comprobación de cobertura para asegurar que se reciben las 72 geografías esperadas y las cinco categorías.
