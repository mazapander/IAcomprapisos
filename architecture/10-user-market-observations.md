# Observaciones de mercado aportadas por usuarios

## Finalidad

La aplicación permite aportar voluntariamente valores que complementan las fuentes oficiales:
precio solicitado, tasación, precio negociado y precio escriturado. El objetivo es calcular,
cuando exista muestra suficiente, medianas y brechas territoriales que ayuden a compradores a
interpretar una oferta.

## Minimización y separación

`product.market_observations` no almacena dirección, referencia catastral, URL del anuncio,
coordenadas, identidad, correo, ingresos ni documentos. Tampoco se enlaza con el visitante de
analítica. La observación conserva únicamente:

- código oficial de CCAA o provincia;
- tipología y tramo de antigüedad comparable con MIVAU;
- superficie, periodo mensual y rol del aportante;
- importes conocidos y versión del consentimiento específico;
- estado, creación y caducidad.

La caducidad usa `PRODUCT_DATA_RETENTION_DAYS`. El borrado se ejecuta desde el endpoint interno
`POST /api/v1/product/admin/purge-expired`.

## Uso analítico previsto

Las métricas individuales se calculan como apoyo y no se publican directamente. La futura capa
agregada debe usar mediana, percentiles, recuento y umbral mínimo de muestra por territorio,
tipología, antigüedad y periodo. Las diferencias principales son:

- prima solicitada sobre tasación;
- descuento entre precio solicitado y negociado;
- precio escriturado frente a tasación;
- valores por metro cuadrado de cada fase.

Antes de publicar agregados se deben revisar duplicados, valores extremos, consistencia temporal
y riesgo de reidentificación en territorios con poca muestra.
