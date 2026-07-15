# Consumo estructurado e ingestas incrementales

## Capas

- `raw.source_records`: auditoría y payload original. No consumir directamente desde modelos.
- `analytics.indicators`: catálogo semántico y reglas de agregación.
- `analytics.indicator_observations`: tabla larga canónica para modelos, BI, APIs y n8n.
- `control.ingestion_runs`: control operativo.

## APIs de consumo

### Catálogo

`GET /api/v1/analytics/catalog`

Describe código, nombre, unidad, frecuencia nativa, agregación, fuente y dataset.

### Observaciones en formato largo

`GET /api/v1/analytics/observations`

Filtros repetibles:

- `indicator_code`
- `geography_code`
- `source`
- `date_from`
- `date_to`
- `order`
- `limit`
- `offset`

Ejemplo:

```text
/api/v1/analytics/observations?indicator_code=housing_sales_total&geography_code=PROV:48&date_from=2020-01-01&order=asc
```

### Serie cronológica

`GET /api/v1/analytics/series/{indicator_code}/{geography_code}`

Ejemplo:

```text
/api/v1/analytics/series/housing_sales_total/PROV:48
```

### Último valor de cada serie

`GET /api/v1/analytics/latest`

Ejemplo:

```text
/api/v1/analytics/latest?source=ine_transmissions&geography_code=PROV:48
```

## Ingesta incremental desde n8n

Body recomendado:

```json
{
  "requested_by": "n8n-monthly",
  "parameters": {
    "mode": "incremental"
  }
}
```

El backend consulta el máximo `period` ya almacenado para la fuente. Si existe, añade automáticamente `date_from` con ese periodo. Se vuelve a procesar el último periodo como solape para recoger revisiones provisionales y se insertan los periodos nuevos.

La restricción única analítica es:

```text
indicator_code + geography_code + period + source
```

Por ello la misma observación se actualiza mediante `upsert` y no se duplica.

En raw, el hash ignora campos volátiles como `retrieved_at`. Una descarga idéntica no crea otra fila; una revisión del valor sí se conserva como nueva versión raw.

Si todavía no existen observaciones para la fuente, `mode=incremental` cae automáticamente a carga completa.

## Flujo n8n recomendado

1. Schedule Trigger mensual.
2. HTTP Request POST a `/api/v1/ingestions/{source}` con `mode=incremental`.
3. IF con `status == succeeded`.
4. En caso de fallo, enviar alerta con `error` y `id`.

n8n no escribe en PostgreSQL: el backend gestiona descarga, transformación, idempotencia y transacción.
