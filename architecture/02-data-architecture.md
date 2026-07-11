# Arquitectura de datos

## Schemas

### `raw`
Conserva cada registro recibido con payload JSONB, hash, fuente, dataset, periodo, geografía y ejecución. No contiene lógica de negocio y permite reprocesar sin volver a descargar.

### `analytics`
Contiene dimensiones y observaciones normalizadas. El grano base es: `indicador + geografía + periodo + fuente`. Esta estructura soporta datos mensuales, trimestrales y anuales sin crear una tabla por proveedor.

### `control`
Metadatos operativos: ejecuciones, estado, parámetros, filas, timestamps y errores. Alimentará el panel de status.

## Identificadores geográficos
Se usarán códigos INE normalizados. Niveles previstos: país, CCAA, provincia, municipio y sección censal. `geographies.parent_code` permite jerarquía.

## Indicadores iniciales
- `housing_sales_total`
- `housing_sales_new`
- `housing_sales_used`
- `house_price_index`
- `appraisal_price_eur_m2`
- `rent_price_eur_m2`
- `rental_household_share_pct`
- `euribor_12m_pct`
- `mortgage_interest_rate_pct`
- `mortgages_total`
- `average_mortgage_amount_eur`

## Evolución
Cuando el modelo requiera features se añadirá `analytics.feature_snapshots`, preservando `available_at` para impedir data leakage. Las predicciones se almacenarán en tablas versionadas por modelo, horizonte y fecha de cálculo.
