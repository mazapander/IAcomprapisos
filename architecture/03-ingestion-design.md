# Diseño de ingestas

Cada origen vive en `app/ingestion/sources/<origen>.py` e implementa:

1. `extract(parameters)`: descarga y devuelve registros sin interpretar.
2. `transform(records)`: convierte raw a indicadores canónicos.

El servicio común se ocupa de ejecución, hash, idempotencia, escritura, upsert, errores y métricas. No deben duplicarse conexiones de base de datos ni lógica de auditoría dentro de los conectores.

## Contrato n8n

```http
POST /api/v1/ingestions/ine_transmissions
X-API-Key: <secret>
Content-Type: application/json

{"requested_by":"n8n-daily","parameters":{"from":"2025-01","to":"2026-06"}}
```

La primera versión ejecuta síncronamente y devuelve el resultado. En una fase posterior podrá responder `202 Accepted` y procesar en worker sin cambiar el contrato funcional.

## Orden inicial
1. Banco de España: Euríbor.
2. INE: compraventas.
3. INE/MIVAU: precios de compraventa.
4. SERPAVI: alquiler.
5. Hipotecas, renta, población, paro y construcción.
