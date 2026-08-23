# API objetivo y solución web

## API pública de consulta
- `GET /analytics/indicators`
- `GET /markets/geographies`
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

## Entradas de producto

1. Entender una zona mediante selección territorial visual.
2. Calcular un presupuesto de compra sostenible.
3. Comparar hasta cuatro ofertas en igualdad de condiciones.
4. Revisar una sola oferta mediante un formulario progresivo.
5. Plantear una duda o caso para ampliar la base de conocimiento.
6. Consultar métricas y dudas desde el panel interno.

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

El contrato admite hipotecas fijas, variables y mixtas. En una mixta calcula por separado
el tramo fijo, el capital pendiente al cambiar de fase, la cuota variable y el estrés del
índice de referencia. Comisiones y vinculaciones declaradas se suman a un coste comparable;
no se confunden con intereses ni con la TAE de la oferta.

`POST /api/v1/mortgages/budget` calcula un precio máximo orientativo combinando el límite
de esfuerzo, el LTV escogido, el efectivo disponible y un colchón de seguridad. Expone si
el factor limitante es la capacidad mensual o el ahorro.

El navegador utiliza almacenamiento local opt-in para recuperar un escenario. Los datos
financieros personales no se guardan en cookies ni se envían a terceros. Las cookies no
esenciales y la analítica de comportamiento quedan desactivadas hasta disponer de una
capa de consentimiento y una finalidad documentada.
