# Fuentes de mercado: precios, hipotecas, valor tasado y SERPAVI

## INE — Índice de Precios de Vivienda

- Source key: `ine_house_prices`.
- Tabla oficial: `79563`.
- Endpoint: `https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/79563`.
- Frecuencia: trimestral.
- Geografía: España y CCAA.
- Base vigente desde el primer trimestre de 2026: 2025 = 100.
- Indicadores: `house_price_index`, `house_price_index_new`, `house_price_index_used`.

Se conserva la frecuencia trimestral. El periodo se representa con el primer día del trimestre, sin interpolación mensual.

## INE — Hipotecas sobre viviendas

- Source key: `ine_mortgages`.
- Tabla oficial: `3200`.
- Endpoint: `https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/3200`.
- Frecuencia: mensual.
- Geografía: España y provincias.
- Indicadores: `mortgages_housing_total`, `mortgages_housing_amount_thousand_eur`.

El importe publicado por esta tabla se conserva en miles de euros. No se convierte a importe medio: esa métrica se calculará posteriormente dividiendo importe total entre número de hipotecas, con controles para valores nulos y cero.

La tabla nacional `24457` de tipos de interés hipotecarios queda registrada como ampliación futura, porque no ofrece desglose provincial.

## MIVAU — Valor tasado de la vivienda

- Source key: `mivau_appraisal`.
- Frecuencia esperada: trimestral.
- Indicador: `appraisal_price_eur_m2`.
- Formatos soportados: CSV y XLSX.
- URL: se suministra como `parameters.url` en cada ejecución.

MIVAU distribuye esta estadística mediante publicaciones y ficheros versionados. La URL de descarga no se fija en el código para evitar que una edición nueva rompa el histórico. n8n deberá resolver o configurar la URL oficial de la edición y pasarla al backend.

Parámetros opcionales:

- `sheet_name` para seleccionar hoja XLSX.
- `geographic_level`, por defecto `province`.

## MIVAU — SERPAVI

- Source key: `mivau_rent`.
- Frecuencia: anual.
- Indicadores: `rent_monthly_median_eur`, `rent_price_median_eur_m2`.
- Formatos soportados: CSV y XLSX.
- URL: se suministra como `parameters.url`.
- Nivel por defecto: municipio; admite provincia, CCAA y municipio mediante `geographic_level`.

SERPAVI se conserva como dato anual. La futura tabla mensual de snapshots podrá propagar el último valor conocido, pero deberá marcarlo como `forward_fill` y conservar el año original.

## Contratos de n8n

```json
{"requested_by":"n8n-quarterly","parameters":{"date_from":"2007-01-01"}}
```

para `ine_house_prices` e `ine_mortgages`.

```json
{"requested_by":"n8n-release","parameters":{"url":"https://.../fichero-oficial.xlsx","sheet_name":"Datos","geographic_level":"province"}}
```

para `mivau_appraisal` y `mivau_rent`.

## Controles pendientes antes de producción

1. Verificar cada nueva edición MIVAU contra una fixture real.
2. Sustituir geografía `NAME:*` por aliases canónicos cuando el fichero no incluya código INE.
3. Registrar `published_at` y `available_at` desde el calendario oficial.
4. Añadir checks de cobertura territorial y periodos ausentes.
