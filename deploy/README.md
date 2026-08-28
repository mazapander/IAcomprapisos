# Despliegue público

## 1. Preparar el servidor

El compose de producción espera una red Docker externa llamada `apps` y una instancia de
PostgreSQL accesible desde ella. Crear la red una sola vez si todavía no existe:

```bash
docker network create apps
cp .env.production.example .env.production
```

Cambiar al menos `API_KEY`, `DATABASE_URL` y `PUBLIC_BASE_URL`. Generar la clave con
`openssl rand -hex 32`. El arranque ejecuta las migraciones antes de servir tráfico.

```bash
docker compose -f deploy/docker-compose.production.yml up -d --build
```

## 2. Publicar con Nginx Proxy Manager

Crear un Proxy Host para el dominio público con destino `iacomprapisos`, puerto `8000`,
esquema `http`, certificado Let's Encrypt y `Force SSL`. Nginx Proxy Manager debe estar
conectado a la red `apps`. La web y los endpoints públicos quedan disponibles en el mismo
origen; no hay que habilitar CORS.

El producto público no debe pasar por Authelia. El panel `/admin.html` puede publicarse en
el mismo dominio porque sus datos exigen `X-API-Key`, aunque es preferible restringir esa
ruta adicionalmente en el proxy o servirla bajo un host interno.

## 3. Desplegar desde GitHub Actions

El workflow manual `Deploy production` necesita un Environment de GitHub llamado
`production` con estos secrets:

- `DEPLOY_HOST`, `DEPLOY_PORT`, `DEPLOY_USER` y `DEPLOY_SSH_KEY`;
- `DEPLOY_KNOWN_HOSTS`, obtenido una vez con `ssh-keyscan -p PUERTO HOST` y verificado;
- `DEPLOY_PATH`, ruta absoluta del proyecto en el servidor.

`.env.production` se crea únicamente en el servidor y el workflow no lo sobrescribe.

## 4. Operación y privacidad

- Salud: `GET /api/v1/health`.
- Métricas internas: `/admin.html` o `GET /api/v1/product/admin/metrics`.
- Dudas recibidas: `GET /api/v1/product/admin/questions`.
- Observaciones de mercado consentidas: `GET /api/v1/product/admin/market-observations`.
- Dudas pendientes de aviso n8n: `GET /api/v1/product/admin/questions/notifications/pending`.
- Resultado del aviso: `POST /api/v1/product/admin/questions/{id}/notification-result` con
  `{"delivered": true}` o `{"delivered": false, "error": "..."}`.
- Borrado por caducidad: `POST /api/v1/product/admin/purge-expired`.

Los tres endpoints internos requieren `X-API-Key`. Programar el borrado diariamente desde
n8n o cron. La retención se configura con `PRODUCT_DATA_RETENTION_DAYS`.

Antes de abrir el dominio al público hay que completar el aviso legal, la política de
privacidad y la política de cookies con la identidad y los datos de contacto reales del
responsable del tratamiento. La interfaz ya ofrece aceptar y rechazar en el mismo nivel.

## 5. Avisos de nuevas consultas con n8n

Crear un workflow periódico cada 2-5 minutos:

1. HTTP Request `GET http://iacomprapisos:8000/api/v1/product/admin/questions/notifications/pending`
   con la cabecera `X-API-Key`.
2. Dividir la respuesta en items y enviar un mensaje de Telegram con categoría, etapa,
   territorio, correo cuando exista consentimiento y texto de la consulta.
3. Si Telegram responde correctamente, llamar a
   `POST /api/v1/product/admin/questions/{{$json.id}}/notification-result` con
   `{"delivered": true}`.
4. En la rama de error, llamar al mismo endpoint con
   `{"delivered": false, "error": "{{$json.error.message}}"}`. La consulta permanece
   pendiente y se reintentará en la siguiente ejecución.

La API no entrega el correo cuando no existe consentimiento de contacto. El endpoint de
acuse cambia la consulta de `new` a `notified`, evitando que vuelva a aparecer en el lote.
