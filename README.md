# IA Compra Pisos

Plataforma de datos para recopilar, normalizar y consultar indicadores del mercado
residencial español. El backend utiliza FastAPI, PostgreSQL y Alembic y está preparado
para ser orquestado desde n8n.

## Fuentes implementadas

| Source key | Fuente oficial | Dataset | Frecuencia |
|---|---|---|---|
| `ine_transmissions` | INE | Tabla 6150, compraventa de viviendas | Mensual |
| `ine_house_prices` | INE | Tabla 79563, índice de precios de vivienda | Trimestral |
| `ine_mortgages` | INE | Tabla 3200, hipotecas sobre viviendas | Mensual |
| `ine_household_income` | INE | Tablas 53689 y 53687, renta de hogares y fuentes de ingreso | Anual |
| `bde_euribor` | Banco de España | `be1901.csv`, Euríbor a un año | Mensual |
| `bde_mortgage_market` | Banco de España | `be1906.csv` y `be1912.csv`, TAE e importe de nuevas operaciones de vivienda | Mensual |
| `mivau_appraisal` | MIVAU | Valor tasado de vivienda | Trimestral |
| `mivau_rent` | MIVAU | SERPAVI, renta de alquiler | Anual |

Las respuestas originales se conservan en `raw`, las observaciones normalizadas se
escriben en `analytics` y las ejecuciones se auditan en `control`.

`ine_household_income` incorpora tanto niveles de renta media/mediana como el peso de
salarios, pensiones, prestaciones por desempleo, otras prestaciones y otros ingresos.
`bde_mortgage_market` incorpora la TAE de nuevas operaciones de crédito a la vivienda y
su importe mensual. La definición MIR del Banco de España incluye renegociaciones dentro
de las nuevas operaciones; este matiz se conserva en los metadatos.

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
curl -X POST http://iacomprapisos:8000/api/v1/ingestions/ine_household_income \
  -H "X-API-Key: change-me" \
  -H "Content-Type: application/json" \
  -d '{"requested_by":"n8n-annual","parameters":{"mode":"incremental"}}'
```

```bash
curl -X POST http://iacomprapisos:8000/api/v1/ingestions/bde_mortgage_market \
  -H "X-API-Key: change-me" \
  -H "Content-Type: application/json" \
  -d '{"requested_by":"n8n-monthly","parameters":{"mode":"incremental"}}'
```

```bash
curl -X POST http://iacomprapisos:8000/api/v1/ingestions/bde_euribor \
  -H "X-API-Key: change-me" \
  -H "Content-Type: application/json" \
  -d '{"requested_by":"n8n-monthly","parameters":{"date_from":"1999-01-01"}}'
```

## Estructura de datos

- `raw.source_records`: payload original, hash, URL y metadatos de disponibilidad.
- `analytics.indicators`: catálogo y reglas de frecuencia/agregación.
- `analytics.indicator_observations`: valores normalizados sin alterar la frecuencia nativa.
- `control.ingestion_runs`: historial, estado, parámetros, conteos y errores.

Consulta `architecture/` para la visión, el modelo de datos, las fichas de fuentes y las
fases de desarrollo.
