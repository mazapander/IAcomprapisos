# IA Compra Pisos

Plataforma de datos para recopilar, normalizar y consultar indicadores del mercado residencial español. El MVP ofrece un backend FastAPI orquestable desde n8n, persistencia PostgreSQL y separación entre datos originales (`raw`) y datos preparados (`analytics`).

## Arranque

```bash
cp .env.example .env
docker compose up --build
```

- API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- Salud: `GET /api/v1/health`
- Lanzar ingesta: `POST /api/v1/ingestions/{source}`
- Consultar ejecuciones: `GET /api/v1/ingestions/runs`

Consulta `architecture/` para el diseño, modelo de datos y fases.
