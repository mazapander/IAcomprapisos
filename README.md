# IA Compra Pisos

Plataforma de datos y decisión que reduce la asimetría de información entre quien compra
una vivienda y las entidades con las que negocia. Combina un frontend React con FastAPI,
PostgreSQL y Alembic; las ingestas siguen preparadas para orquestarse desde n8n.

## Fuentes implementadas

| Source key | Fuente oficial | Dataset | Frecuencia |
|---|---|---|---|
| `ine_transmissions` | INE | Tabla 6150, compraventa de viviendas | Mensual |
| `ine_house_prices` | INE | Tabla 79563, índice de precios de vivienda | Trimestral |
| `ine_mortgages` | INE | Tabla 3200, hipotecas sobre viviendas | Mensual |
| `ine_household_income` | INE | Tablas 53689 y 53687, renta de hogares y fuentes de ingreso | Anual |
| `bde_euribor` | Banco de España | `be1901.csv`, Euríbor a un año | Mensual |
| `bde_mortgage_market` | Banco de España | `be1904.csv`, `be1906.csv` y `be1912.csv`: TEDR, TAE e importe de nuevas operaciones | Mensual |
| `mivau_appraisal` | MIVAU | Valor tasado de vivienda | Trimestral |
| `mivau_rent` | MIVAU | SERPAVI, renta de alquiler | Anual |

Las respuestas originales se conservan en `raw`, las observaciones normalizadas se
escriben en `analytics` y las ejecuciones se auditan en `control`.

`ine_household_income` incorpora tanto niveles de renta media/mediana como el peso de
salarios, pensiones, prestaciones por desempleo, otras prestaciones y otros ingresos.
`bde_mortgage_market` incorpora TEDR, TAE e importe de nuevas operaciones de vivienda. La
definición MIR del Banco de España incluye renegociaciones dentro
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
- Catálogo geográfico y cobertura: `GET /api/v1/markets/geographies`
- Observatorio estatal: `GET /api/v1/markets/observatory/national?years=10`
- Presupuesto sostenible: `POST /api/v1/mortgages/budget`
- Revisión de una oferta hipotecaria: `POST /api/v1/mortgages/review`

### Desarrollo del frontend

```bash
cd frontend
npm ci
npm run dev
```

Vite usa `http://localhost:5173` y redirige `/api` a FastAPI en el puerto 8000. `npm run
build` genera el bundle que FastAPI sirve desde `app/web`. La imagen Docker realiza este
build en una etapa Node separada, por lo que el despliegue continúa siendo un único servicio.

## Capa de producto

`GET /api/v1/markets/observatory/national` reúne el seguimiento estatal en tres bloques:
precios, actividad hipotecaria y tipos. Publica la serie histórica, último valor, cambio frente
al dato anterior y variación interanual. Para los tipos expresa la diferencia en puntos
porcentuales; para índices e importes utiliza variación porcentual. El importe medio hipotecario
se deriva únicamente cuando el número y el importe total del INE coinciden en el mismo periodo.
Cada serie mantiene fuente y fecha, y las series sin cobertura se devuelven como ausentes.

`GET /api/v1/markets/{geography_code}/summary` devuelve una ficha territorial lista
para web con precio, renta neta del hogar, peso de salarios, variación interanual de
hipotecas, TAE de nuevas hipotecas, volumen de financiación, Euríbor y esfuerzo de
compra estimado. También calcula en backend:

- proxy de spread hipotecario de mercado (TEDR variable menos Euríbor);
- esfuerzo de compra con tamaño, LTV y plazo configurables;
- price-to-income y price-to-rent;
- evolución del precio ajustada por renta;
- percentiles históricos de precio y ratios.

La respuesta conserva periodo, fuente, indicador y geografía efectiva de cada dato.
Si todavía no existe TEDR observado, el esfuerzo puede usar Euríbor más un spread
configurable, pero el TEDR continúa figurando como ausente. Nunca se presenta una
estimación como dato oficial.

```bash
curl 'http://localhost:8000/api/v1/markets/PROV:24/summary?home_size_m2=90&ltv_pct=80&term_years=25'
```

### Herramientas de decisión

`POST /api/v1/mortgages/budget` estima un precio de compra sostenible y explica si limita
más la capacidad de pago mensual o el ahorro disponible después de reservar un colchón.

`POST /api/v1/mortgages/review` calcula la cuota con el TIN y usa TAE y Euríbor solo para
comparaciones coherentes. Devuelve cuota, esfuerzo, LTV, efectivo necesario, ahorro restante,
colchón de emergencia, intereses totales y un estrés de tipos de dos puntos. Las alertas
explican problemas concretos de liquidez, endeudamiento o exposición a tipos; no emiten
una aprobación crediticia.

El contrato admite ofertas fijas, variables y mixtas. Para comparar ofertas suma por separado
intereses, comisiones iniciales y vinculaciones declaradas. La interfaz permite normalizar
entre dos y cuatro propuestas sobre la misma vivienda y utilizar la diferencia de coste como
argumento de negociación.

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

Consulta `architecture/07-security-data-integrity-audit.md` para el dictamen, las fuentes,
los cálculos validados y los riesgos abiertos, y `architecture/08-product-feature-roadmap.md`
para las mejoras propuestas. El posicionamiento, los flujos UX y las decisiones técnicas del
refactor React están en `architecture/09-frontend-product-refactor.md`.
