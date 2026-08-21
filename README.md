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
- Ficha territorial de producto: `GET /api/v1/markets/PROV:24/summary`
- Revisión de una oferta hipotecaria: `POST /api/v1/mortgages/review`

## Capa de producto

`GET /api/v1/markets/{geography_code}/summary` devuelve una ficha territorial lista
para web con precio, renta neta del hogar, peso de salarios, variación interanual de
hipotecas, TAE de nuevas hipotecas, volumen de financiación, Euríbor y esfuerzo de
compra estimado. También calcula en backend:

- spread hipotecario (TAE menos Euríbor);
- esfuerzo de compra con tamaño, LTV y plazo configurables;
- price-to-income y price-to-rent;
- evolución del precio ajustada por renta;
- percentiles históricos de precio y ratios.

La respuesta conserva periodo, fuente, indicador y geografía efectiva de cada dato.
Si todavía no existe TAE observada, el esfuerzo puede usar Euríbor más un spread
configurable, pero la TAE continúa figurando como ausente. Nunca se presenta una
estimación como dato oficial.

```bash
curl 'http://localhost:8000/api/v1/markets/PROV:24/summary?home_size_m2=90&ltv_pct=80&term_years=25'
```

### Asistente de decisión hipotecaria

`POST /api/v1/mortgages/review` cruza el escenario aportado por la persona con la TAE y
el Euríbor observados. Devuelve cuota, esfuerzo, LTV, efectivo necesario, ahorro restante,
colchón de emergencia, intereses totales y un estrés de tipos de dos puntos. Las alertas
explican problemas concretos de liquidez, endeudamiento o exposición a tipos; no emiten
una aprobación crediticia.

La web pública guarda el escenario únicamente en `localStorage` y solo cuando la persona
marca expresamente «Guardar este escenario». El formulario no usa cookies para renta,
ahorro, deuda o condiciones de la oferta, y el endpoint no persiste el cuerpo de la
petición.

La medición propia se activa únicamente tras consentimiento. Registra el embudo de uso,
resultados por tramos y geografía máxima de provincia; el contrato de la API rechaza campos
financieros. Las dudas enviadas voluntariamente se almacenan por separado para revisión.
El panel interno está en `/admin.html` y sus datos requieren `X-API-Key`. Consulta
`deploy/README.md` para publicar el servicio, configurar el proxy y automatizar la retención.

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
- `product.visitors`: identificadores anónimos con consentimiento y caducidad.
- `product.events`: eventos permitidos del embudo, sin importes financieros.
- `product.questions`: dudas enviadas expresamente y su estado de revisión.

Consulta `architecture/` para la visión, el modelo de datos, las fichas de fuentes y las
fases de desarrollo.
