# Visión y alcance

## Objetivo
Construir una plataforma reproducible de datos públicos que permita evaluar el contexto de compra de vivienda por comunidad autónoma y provincia, dejando preparada la incorporación posterior de modelos estadísticos o de IA.

## MVP backend
- FastAPI como interfaz de control y consulta.
- PostgreSQL con schemas `raw`, `analytics` y `control`.
- Ejecución idempotente desde n8n mediante API key.
- Un módulo Python independiente por fuente.
- Historial de ejecuciones, errores, parámetros y conteos.
- Datos normalizados como observaciones de indicadores.

## Fuera del MVP
- Recomendación financiera personalizada.
- Scraping de portales privados.
- Entrenamiento y serving del modelo.
- Frontend público completo.

## Principios
Trazabilidad, idempotencia, separación de responsabilidades, versionado de fuentes, ausencia de fuga temporal y capacidad de recalcular analytics desde raw.
