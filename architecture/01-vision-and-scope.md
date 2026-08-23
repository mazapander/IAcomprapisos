# Visión y alcance

## Objetivo
Reducir la asimetría de información entre quien compra una vivienda y las entidades con
las que negocia. La plataforma transforma datos públicos, condiciones hipotecarias y
supuestos personales en contexto comparable para que la persona pueda mantener una
conversación de tú a tú con bancos e intermediarios.

El problema macro no es la ausencia de otra calculadora: quien compra toma una decisión
enorme con información dispersa, mientras la otra parte dispone de precios, modelos y miles
de operaciones. En un mercado de vivienda tensionado, el producto debe acercar ambos puntos.

En el plano micro debe responder, como mínimo, a estas preguntas:

- ¿cuánto puedo comprar sin quedarme sin margen?;
- ¿qué está ocurriendo en la zona que estoy valorando?;
- ¿es competitiva la oferta que me han hecho?;
- ¿qué oferta es mejor cuando igualo plazo, comisiones y vinculaciones?;
- ¿qué diferencias concretas puedo usar para negociar?

## Plataforma
- FastAPI como interfaz de control y consulta.
- PostgreSQL con schemas `raw`, `analytics` y `control`.
- Ejecución idempotente desde n8n mediante API key.
- Un módulo Python independiente por fuente.
- Historial de ejecuciones, errores, parámetros y conteos.
- Datos normalizados como observaciones de indicadores.
- Frontend React orientado por casos de uso, no por endpoints ni campos técnicos.
- Comparación de ofertas fijas, variables y mixtas con estrés de tipos.
- Recogida consentida de dudas para priorizar información que el comprador no encuentra.

## Fuera del alcance actual
- Recomendación financiera personalizada.
- Scraping de portales privados.
- Entrenamiento y serving del modelo.
- Catálogo en tiempo real de ofertas comerciales de todas las entidades.
- Lectura automática de FEIN o documentos bancarios.
- Cobertura municipal hasta disponer de fuentes normalizadas a ese nivel.

## Principios

Trazabilidad, comparabilidad, explicación antes que scoring, idempotencia, separación de
responsabilidades, versionado de fuentes, ausencia de fuga temporal, privacidad por defecto y
capacidad de recalcular analytics desde raw. Nunca se presentará una estimación o un respaldo
nacional como si fuera un dato oficial del municipio o provincia elegidos.
