# Plan de desarrollo

## Fase 0 — Fundaciones
Estructura FastAPI, Docker, PostgreSQL, Alembic, schemas, seguridad básica, registro de fuentes, historial de ejecuciones y documentación de arquitectura.

## Fase 1 — Ingestas oficiales
Implementar y validar Euríbor e INE compraventas. Añadir fixtures, tests de parsing, backfill e idempotencia. Después incorporar IPV/valor tasado, hipotecas y SERPAVI.

## Fase 2 — Calidad y operación
Checks de completitud, frescura, duplicados y anomalías; reintentos; timeouts; catálogo de datasets; endpoint de status por fuente; workflow n8n programado; alertas de fallo.

## Fase 3 — Analytics territorial
Series derivadas, variación interanual, medias móviles, compraventas por población, price-to-rent, esfuerzo hipotecario y vistas materializadas por CCAA/provincia.

## Fase 4 — Motor de scoring
Definir objetivo y horizonte, construir snapshots point-in-time, baseline interpretable, backtesting temporal y explicación por componentes. El resultado será una puntuación, no una recomendación financiera automática.

## Fase 5 — Solución web
Frontend React/Vite con:
- resumen nacional;
- mapa y ranking por CCAA/provincia;
- ficha territorial y comparador;
- evolución de indicadores;
- desglose del score y factores;
- frescura/calidad de cada fuente;
- panel administrativo de ejecuciones y errores.

## Criterio de finalización
Una provincia podrá consultarse en una fecha determinada con datos trazables, estado de frescura y una puntuación versionada y explicable, comparándola con su historia y otras zonas.
