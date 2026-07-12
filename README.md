# IA Compra Pisos

Plataforma de datos para recopilar, normalizar y consultar indicadores del mercado residencial español. El backend utiliza FastAPI, PostgreSQL y Alembic y está preparado para ser orquestado desde n8n.

## Fuentes implementadas

| Source key | Fuente oficial | Dataset | Frecuencia |
|---|---|---|---|
| `ine_transmissions` | INE | Tabla 6150, compraventa de viviendas | Mensual |
| `bde_euribor` | Banco de España | `be1901.csv`, Euríbor a un año | Mensual |

Las respuestas originales se conservan en `raw`, las observaciones normalizadas se escriben en `analytics` y las ejecuciones se auditan en `control`.

## Arranque

```bash
cp .env.example .env
docker compose up --build
```

- API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- Salud: `GET /api/v1/health`
- Fuentes registradas: `GET /api/v1/ingestions/sources`
- Lanzar ingesta: `POST /api/v1/ingestions/{source}`
- Consultar ejecuciones: `GET /api/v1/ingestions/runs`
- Consultar indicadores: `GET /api/v1/analytics/indicators`

## Ejemplos n8n / curl

```bash
curl -X POST http://localhost:8000/api/v1/ingestions/ine_transmissions \
  -H "X-API-Key: change-me" \
  -H "Content-Type: application/json" \
  -d '{"requested_by":"n8n-monthly","parameters":{"date_from":"2020-01-01"}}'
```

```bash
curl -X POST http://localhost:8000/api/v1/ingestions/bde_euribor \
  -H "X-API-Key: change-me" \
  -H "Content-Type: application/json" \
  -d '{"requested_by":"n8n-monthly","parameters":{"date_from":"1999-01-01"}}'
```

## Estructura de datos

- `raw.source_records`: payload original, hash, URL y metadatos de disponibilidad.
- `analytics.indicators`: catálogo y reglas de frecuencia/agregación.
- `analytics.indicator_observations`: valores normalizados sin alterar la frecuencia nativa.
- `control.ingestion_runs`: historial, estado, parámetros, conteos y errores.

Consulta `architecture/` para la visión, el modelo de datos, las fichas de fuentes y las fases de desarrollo.
