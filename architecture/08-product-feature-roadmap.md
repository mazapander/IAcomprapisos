# Sugerencias de mejora de producto

Priorización propuesta tras la auditoría. Las funciones que tratan datos personales
deben mantener consentimiento, minimización y borrado desde el diseño.

## P0 — confianza para publicar

1. **Estado y frescura por dato.** Mostrar fuente, periodo, fecha de actualización,
   cobertura geográfica y si el dato es oficial, estimado o no disponible.
2. **Monitor de fuentes.** Alertar por retraso, cambio de esquema, unidad inesperada,
   salto anómalo o descenso de cobertura antes de promover una ingesta.
3. **Explicación de cada cálculo.** Desplegable con fórmula, valores usados y supuestos;
   distinguir TIN, TAE, TEDR y Euríbor en lenguaje sencillo.
4. **Comparador FEIN.** La comparación manual estructurada ya cubre hasta cuatro ofertas,
   modalidades mixtas, comisiones y vinculaciones. El siguiente incremento debe importar una
   FEIN con confirmación campo a campo, sin guardar el documento por defecto.
5. **Panel operativo.** Fallos de ingesta, frescura, cobertura, dudas sin resolver,
   consentimiento y eliminaciones; nunca importes individuales.

## P1 — mejores decisiones hipotecarias

6. **Escenarios de tipos.** Fijo frente a variable y mixto, curvas configurables,
   revisión anual/semestral y amortización anticipada.
7. **Coste total de compra.** Impuestos y gastos por comunidad, seguros y productos
   vinculados, diferenciando estimaciones de importes introducidos por el usuario.
8. **Presupuesto sostenible.** Colchón, gastos de vida, dependientes, pérdida temporal de
   ingresos y límite personal; resultado explicativo, no aprobación crediticia.
9. **Comparación territorial.** Precio/renta, esfuerzo, alquiler frente a compra,
   percentil histórico y tendencia para territorios equivalentes.
10. **Alertas personales opcionales.** Cambios en Euríbor, mercado o esfuerzo guardado,
    con consentimiento separado, frecuencia elegida y baja inmediata.
11. **Catálogo neutral de ofertas públicas.** Condiciones publicadas por entidades con fecha,
    requisitos, vinculaciones y metodología de actualización. Debe distinguir publicidad,
    ejemplo representativo y oferta personalizada, y nunca favorecer a un proveedor por pago.

## P2 — aprendizaje y servicio

12. **Centro de dudas trazable.** Taxonomía de preguntas, respuesta editorial enlazada a
    fuentes y fecha de revisión, sin reutilizar texto personal como analítica.
13. **Embudo respetuoso.** Medir comprensión, abandono y utilidad por tramos amplios;
    pruebas A/B solo tras consentimiento y con umbral mínimo de agregación.
14. **Exportación de informe.** PDF/JSON descargable localmente con supuestos, fuentes y
    comparativa, sin copia de servidor salvo petición expresa.
15. **Accesibilidad y lectura fácil.** WCAG 2.2 AA, navegación por teclado, contraste,
    lenguaje alternativo y pruebas con usuarios.
16. **API de datos pública.** Versionada, con metadatos y caché, límites de uso y
    changelog; separar endpoints estadísticos de los administrativos.

## Métricas de éxito recomendadas

- porcentaje de fichas con todos los datos dentro de su SLA de frescura;
- porcentaje de cálculos reproducibles con fuente y periodo visibles;
- comprensión declarada y utilidad, no solo clics o tiempo de sesión;
- dudas resueltas y recurrencia por categoría;
- tasa de retirada de consentimiento y cumplimiento efectivo del borrado;
- cero eventos con importes financieros o texto libre en la tabla analítica.
