# Auditoría de seguridad, integridad y cálculos

Fecha de revisión: 21 de agosto de 2026. Alcance: backend, ingestas, modelo de
indicadores, calculadora hipotecaria, web pública, analítica consentida y despliegue.

## Dictamen ejecutivo

El núcleo INE/Banco de España es funcional después de las correcciones de esta
auditoría. La publicación completa sigue condicionada a validar con una descarga real
versionada las dos fuentes MIVAU, probar migraciones y restauración sobre PostgreSQL y
completar los textos legales del responsable. Ningún valor de ejemplo se considera dato
real si no tiene observación, periodo y procedencia en la respuesta.

Se corrigieron tres errores capaces de mostrar resultados incorrectos:

- el lector de `be1901.csv` podía elegir una serie numérica distinta del Euríbor;
- la cuota francesa utilizaba TAE en lugar de TIN;
- la tabla 6150 del INE no reconocía las etiquetas actuales `General` y `Vivienda
  segunda mano`, por lo que omitía total y vivienda usada.

## Evidencia de fuentes y verificación en vivo

La verificación descargó las fuentes oficiales y contrastó serie, unidad, frecuencia,
geografía y valor. La fecha es la del ensayo, no la fecha estadística.

| Fuente | Contrato validado | Muestra oficial observada | Estado |
|---|---|---|---|
| Banco de España 19.1 | `BE_19_1`, Euríbor 12 meses, mensual, % | junio 2026: 2,798 % | Validado |
| Banco de España 19.4 | `BE_19_4.2` TEDR vivienda total y `BE_19_4.3` hasta 1 año | junio 2026: 2,8877 % y 3,0505 % | Validado |
| Banco de España 19.6 | `BE_19_6.1`, TAE vivienda, mensual, % | junio 2026: 2,9395 % | Validado |
| Banco de España 19.12 | `BE_19_12.2`, importe vivienda, millones de euros | junio 2026: 8.088 M€ | Validado |
| INE 53689/53687 | renta anual y composición, provincia | León 2023: 33.378 €/hogar y 51,5 % salarios | Validado |
| INE 3200 | hipotecas, número e importe en miles de euros | León, datos mensuales hasta mayo 2026 | Validado |
| INE 6150 | compraventa, número, provincia y categoría | León junio 2026: total 615, nueva 110, usada 505, libre 569, protegida 46 | Validado tras corregir etiquetas |
| INE 79563 | IPV trimestral, base 2025, CCAA | 56 observaciones transformadas; no existe dato provincial de León | Validado |
| MIVAU valor tasado | fichero configurable | no hay versión/URL fijada en el repositorio | Pendiente |
| SERPAVI alquiler | fichero configurable; euros/m²/mes y euros/mes | metodología oficial revisada, contrato de fichero no ensayado | Pendiente |

El ejemplo inicial de León (32.400 € y 61 %) no coincide con la última observación
oficial comprobada y no debe codificarse como dato de producto.

Fuentes primarias:

- [Banco de España, capítulo 19](https://www.bde.es/webbe/es/estadisticas/otras-clasificaciones/publicaciones/boletin-estadistico/capitulo-19.html)
- [Banco de España, tabla 19.1](https://www.bde.es/webbe/es/estadisticas/compartido/datos/pdf/a1901.pdf)
- [Banco de España, tabla 19.4](https://www.bde.es/webbe/es/estadisticas/compartido/datos/pdf/a1904.pdf)
- [Banco de España, tabla 19.6](https://www.bde.es/webbe/es/estadisticas/compartido/datos/pdf/a1906.pdf)
- [Banco de España, tabla 19.12](https://www.bde.es/webbe/es/estadisticas/compartido/datos/pdf/a1912.pdf)
- [INE, tabla 53689](https://www.ine.es/jaxiT3/Tabla.htm?t=53689), [53687](https://www.ine.es/jaxiT3/Tabla.htm?t=53687), [3200](https://www.ine.es/jaxiT3/Tabla.htm?t=3200), [6150](https://www.ine.es/jaxiT3/Tabla.htm?t=6150) y [79563](https://www.ine.es/jaxiT3/Tabla.htm?t=79563)
- [SERPAVI, metodología y resultados 2024](https://publicaciones.transportes.gob.es/downloadcustom/sample/4078)
- [ECB, definición MIR](https://data.ecb.europa.eu/data/datasets/MIR/data-information)

## Cálculos revisados

La cuota usa amortización francesa y el TIN anual:

`cuota = principal * r * (1+r)^n / ((1+r)^n - 1)`, donde `r = TIN / 1200` y
`n = años * 12`. Con tipo cero se usa `principal / n`. El caso de referencia
100.000 €, TIN 3 % y 25 años produce 474,21 €/mes.

La TAE se utiliza solo para comparar el coste de ofertas. No sustituye al TIN para la
cuota. El interés total mostrado es `cuota * n - principal` y excluye comisiones y gastos.
El [simulador del Banco de España](https://clientebancario.bde.es/pcb/es/menu-horizontal/podemosayudarte/simuladores/calculo-de-la-tae-de-un-prestamo-hipotecario.html)
confirma esta separación.

Otros contratos:

- esfuerzo: `(cuota + deudas mensuales) / renta neta mensual`;
- LTV: `principal / precio`;
- spread de oferta variable: `TIN - Euríbor`; no se calcula para tipo fijo;
- proxy de spread de mercado: `TEDR hasta 1 año - Euríbor`;
- price-to-income: precio estimado de la vivienda / renta neta anual del hogar;
- price-to-rent: precio / alquiler anual;
- evolución real por renta: precio y renta se alinean por año antes de dividir;
- percentiles: solo se publican con al menos ocho observaciones históricas.

El estrés de +2 puntos solo se aplica a hipotecas variables. Es un supuesto educativo,
no una predicción ni un criterio de aprobación bancaria.

## Controles incorporados

### Seguridad

- clave administrativa obligatoria y prohibición del valor por defecto en producción;
- historial de ingestas protegido con `X-API-Key`;
- descargas configurables limitadas a HTTPS y dominios oficiales permitidos; se bloquean
  credenciales en URL e IP privadas, reduciendo SSRF;
- documentación OpenAPI desactivada en producción;
- cabeceras CSP, HSTS en producción, `DENY`, `nosniff`, política de referente y permisos;
- dependencias bloqueadas con hashes; `pip-audit` sin vulnerabilidades conocidas y
  Bandit sin hallazgos en esta revisión;
- el endpoint de cálculo no persiste ni devuelve el escenario financiero completo.

### Integridad y transformación

- rechazo de valores no finitos, porcentajes fuera de rango, importes negativos,
  geografías mal formadas y duplicados contradictorios en un lote;
- todo indicador transformado debe existir en catálogo y respetar fuente y unidad;
- series del Banco de España identificadas por alias oficial, no solo por posición;
- Euríbor identificado por código oficial y rechazo de CSV ambiguo;
- cálculos interanuales exigen el mismo mes del año anterior;
- se conservan payload, URL, periodo, serie y fecha de recuperación para auditoría.

## Riesgos abiertos antes de producción

| Prioridad | Riesgo | Cierre exigido |
|---|---|---|
| Bloqueante | MIVAU/SERPAVI sin descarga real versionada ni fixture contractual | fijar edición, checksum, hoja/columnas y prueba de integración |
| Bloqueante | identidad y textos legales del responsable incompletos | revisión jurídica y publicación de privacidad/cookies/aviso legal |
| Alta | migraciones y restricciones no verificadas contra PostgreSQL real | CI efímera con `alembic upgrade head` y pruebas de unicidad/FK |
| Alta | sin prueba de copia y restauración | backup cifrado y simulacro documentado |
| Alta | límite de peticiones depende del proxy | rate limiting por ruta, alertas y prueba de carga |
| Media | CSP requiere `unsafe-inline` por la web embebida | extraer JS/CSS y usar ficheros o nonce |
| Media | `rows_written` cuenta elementos procesados, no inserts/updates reales | devolver contadores de upsert de base de datos |
| Media | no hay alarma automática de frescura | SLA por indicador y aviso de retraso/cambio de esquema |

## Procedimiento reproducible

```bash
pip install --require-hashes -r requirements-dev.lock
ruff check app tests
pytest -q
bandit -q -r app
pip-audit
```

La aceptación final debe incluir además un PostgreSQL desechable, ejecución completa de
migraciones, ingesta de fixtures y comparación de los indicadores persistidos.
