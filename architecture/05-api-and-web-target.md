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
