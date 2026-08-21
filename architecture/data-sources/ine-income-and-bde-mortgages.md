# Renta de hogares y mercado hipotecario real

## INE — Atlas de Distribución de Renta de los Hogares

Source key: `ine_household_income`.

La ingesta usa dos tablas anuales del INE:

- Tabla `53689`: indicadores de renta media y mediana.
- Tabla `53687`: distribución porcentual por fuente de ingresos.

### Indicadores de renta

- `income_net_mean_person_eur`
- `income_net_mean_household_eur`
- `income_mean_equivalised_eur`
- `income_median_equivalised_eur`
- `income_gross_mean_person_eur`
- `income_gross_mean_household_eur`

La unidad es `eur_year`. Se conserva la frecuencia anual y el periodo se normaliza al
1 de enero del año estadístico. No se interpola ni se mensualiza el dato original.

### Composición de ingresos

- `income_share_salary_pct`
- `income_share_pensions_pct`
- `income_share_unemployment_benefits_pct`
- `income_share_other_benefits_pct`
- `income_share_other_income_pct`

La unidad es `percent`. Estos indicadores permiten separar una zona con renta elevada
y fuerte peso de salarios de otra cuya renta depende en mayor medida de pensiones o
prestaciones, información útil para futuros análisis de capacidad de compra y estabilidad
de la demanda.

El parser común del INE normaliza España, CCAA y provincias a los códigos canónicos
existentes (`ES`, `CCAA:*`, `PROV:*`). Las geografías insulares que no puedan mapearse
todavía se conservan en `raw` pero no se promocionan a `analytics`; deben resolverse al
incorporar una dimensión geográfica canónica de mayor granularidad.

## Banco de España — nuevas operaciones de crédito a vivienda

Source key: `bde_mortgage_market`.

Se incorporan dos tablas mensuales de Banco de España:

- `be1906.csv`: TAE de nuevas operaciones; para vivienda se publica como
  `mortgage_new_business_aprc_pct`.
- `be1912.csv`: importe de nuevas operaciones; el total de vivienda se publica como
  `mortgage_new_business_volume_million_eur`.

La TAE (`APRC`) incluye gastos en su definición y es más representativa para la
experiencia del comprador que observar únicamente el Euríbor. El importe se conserva en
millones de euros, sin dividirlo por el número de hipotecas del INE porque ambas fuentes
tienen definiciones estadísticas distintas.

### Matiz metodológico MIR

En las estadísticas de tipos de interés de las instituciones financieras monetarias
(MIR), las nuevas operaciones incluyen los nuevos acuerdos alcanzados durante el mes y
también las renegociaciones de contratos existentes. Por ese motivo:

- no se describe la serie como número de hipotecas nuevas;
- `includes_renegotiations=true` se conserva en los metadatos `raw` y `analytics`;
- el dato se utilizará como referencia del precio y del flujo de financiación realmente
  acordado por las entidades, no como sustituto de la estadística registral de hipotecas.

## Ejecución incremental

```json
{"requested_by":"n8n-annual","parameters":{"mode":"incremental"}}
```

para `ine_household_income`.

```json
{"requested_by":"n8n-monthly","parameters":{"mode":"incremental"}}
```

para `bde_mortgage_market`.

Ambas fuentes soportan también `date_from` y `date_to`. La fuente del Banco de España
permite sobrescribir `aprc_url` y `volume_url` para pruebas o para una edición alternativa
sin cambiar código.
