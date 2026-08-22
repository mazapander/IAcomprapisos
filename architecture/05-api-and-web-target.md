# API objetivo y solución web

## API pública de consulta
- `GET /analytics/indicators`
- `GET /markets/ccaa`
- `GET /markets/provinces`
- `GET /markets/{geography_code}/summary`
- `GET /markets/{geography_code}/series`
- `GET /scores/{geography_code}`
- `GET /scores/{geography_code}/explanation`

## API operativa
- `GET /ingestions/sources`
- `POST /ingestions/{source}`
- `GET /ingestions/runs`
- `GET /status/sources`
- `POST /admin/reprocess`

## Pantallas finales
1. Dashboard nacional.
2. Ranking territorial de oportunidad y riesgo.
3. Comparador de hasta cuatro territorios.
4. Detalle de CCAA/provincia.
5. Calidad y frescura de datos.
6. Ejecuciones de ingesta para administración.

El frontend no calculará indicadores ni scores. Consumirá contratos versionados de FastAPI para garantizar consistencia y permitir otros clientes.

## Contrato de ficha territorial implementado

`GET /api/v1/markets/{geography_code}/summary` compone las observaciones normalizadas
en una ficha de mercado y una sección de derivados. El cálculo vive en
`app/analytics/derived.py`, de forma que web, n8n y futuros clientes móviles comparten
las mismas fórmulas.

Los supuestos de esfuerzo (`home_size_m2`, `ltv_pct`, `term_years` y spread de respaldo)
forman parte de la respuesta. Cada dato observado incluye su indicador, fuente, periodo
y geografía efectiva; esto hace visible cuándo un indicador macroeconómico nacional se
usa como respaldo para una ficha provincial o municipal.

La cobertura parcial es válida y se declara con `coverage`: el endpoint entrega `null`
en vez de fabricar valores cuando faltan renta, TAE o alquiler. Los indicadores
`income_net_mean_household_eur`, `income_share_salary_pct`,
`mortgage_new_business_aprc_pct` y `mortgage_new_business_volume_million_eur` alimentan
directamente la ficha. Sus aliases preservan el contrato público ante futuras revisiones
del catálogo.

## Asistente hipotecario y privacidad

`POST /api/v1/mortgages/review` transforma datos voluntarios del escenario en métricas
explicables: cuota, esfuerzo, LTV, entrada y gastos, colchón, coste total, spread y estrés
de tipos. El endpoint es determinista, no persiste la petición y separa el dato oficial
de las hipótesis del usuario.

El navegador utiliza almacenamiento local opt-in para recuperar un escenario. Los datos
financieros personales no se guardan en cookies ni se envían a terceros. Las cookies no
esenciales y la analítica de comportamiento quedan desactivadas hasta disponer de una
capa de consentimiento y una finalidad documentada.
