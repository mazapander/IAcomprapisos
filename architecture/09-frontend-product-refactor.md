# Refactor del frontend como producto de decisión

## Posicionamiento

IA Compra Pisos reduce la desventaja informativa del comprador frente a bancos, entidades e
intermediarios. El frontal deja de ser un formulario hipotecario único y se organiza por la
pregunta que la persona intenta resolver. El resultado buscado no es una aprobación crediticia,
sino más capacidad para contrastar y negociar.

## Arquitectura

- React 19, TypeScript y Vite en `frontend/`.
- Build reproducible con `package-lock.json` y etapa Node dentro del Docker multi-stage.
- Bundle generado servido por FastAPI desde `app/web`; el panel interno permanece en
  `/admin.html`.
- Sin servicios cartográficos, fuentes o trackers de terceros en tiempo de ejecución.
- Cálculos financieros y derivados siguen residiendo en FastAPI; React solo compone los
  contratos y presenta resultados.

La aplicación se organiza por responsabilidad, no por tamaño accidental del fichero:

```text
frontend/src/
├── app/                 # composición, catálogo de herramientas y contexto compartido
├── views/               # portada y espacio de trabajo
├── layout/              # cabecera y pie
├── features/            # observatorio, mercado, presupuesto, hipotecas y dudas
├── shared/components/   # controles de presentación reutilizables
├── api.ts               # cliente HTTP y contratos de entrada
└── main.tsx             # bootstrap de React, sin lógica de producto
```

En backend, `app/main.py` se limita a invocar la factoría de aplicación. La configuración de
FastAPI, middleware, router y estáticos vive en `app/core/application.py`; las rutas están en
`app/api/routes`; los cálculos del observatorio en
`app/analytics/national_observatory.py`; las ingestas y modelos permanecen aislados. Así, una
feature puede probarse sin montar la interfaz ni conectarse a la base de datos.

La regla de dependencias es descendente: `app` compone `views`; las vistas activan `features`;
las features reutilizan `shared` y los contratos HTTP. Ninguna feature conoce la portada, la
navegación o el bootstrap. Esta frontera evita que añadir una herramienta vuelva a convertir
la aplicación en un componente único.

## Flujos

### Seguir el mercado estatal

El observatorio agrupa precios, hipotecas y tipos/tasas. Permite consultar 5, 10 o 20 años,
seleccionar cada serie y ver su evolución, último valor, variación interanual, fuente y periodo.
No mezcla magnitudes con ejes ambiguos: cada gráfico representa una única serie y conserva su
unidad. El importe medio hipotecario solo se calcula al alinear importe y número de operaciones
del INE en el mismo mes. Una ausencia se muestra como falta de cobertura, no como estimación.

### Entender una zona

Un mapa territorial simplificado permite elegir una comunidad con clic y después una
provincia. La búsqueda accesible ofrece la alternativa por teclado. El catálogo de
`GET /markets/geographies` publica nombres, jerarquía y disponibilidad real. La interfaz
declara que aún no existe contrato municipal, evitando presentar el dato provincial como local.

### Calcular presupuesto

El formulario solicita importes mensuales comprensibles y completa la renta anual. El motor
combina capacidad de cuota, LTV, gastos de compra, ahorro y reserva elegida. El resultado explica
qué restricción está limitando el rango.

### Comparar ofertas

Se introducen entre dos y cuatro ofertas sobre una base común. Cada una puede ser fija,
variable o mixta e incluir TIN, TAE, plazo, diferencial, tramo fijo, comisiones y coste mensual
de vinculaciones. El ranking usa coste financiero comparable y muestra cuota inicial, cuota
estresada y diferencia frente al mercado. Ningún nombre de entidad o importe se persiste.

### Revisar una oferta

El formulario se divide en vivienda, oferta y hogar. El importe solicitado se calcula desde
precio y LTV; el Euríbor se recupera del contexto territorial; los campos de hipoteca mixta
solo aparecen cuando corresponden; TAE y referencia quedan como ajustes avanzados.

### Centro de dudas

Las preguntas se agrupan por necesidad y momento de compra. El texto se almacena únicamente
tras consentimiento específico; el contacto es opcional y requiere una aceptación adicional.
Esta taxonomía permite decidir qué comparadores, explicaciones y fuentes faltan.

## Analítica segura

Los nuevos eventos distinguen herramienta, paso y número agregado de ofertas. El esquema
rechaza propiedades fuera de la allowlist y no admite TIN, TAE, precio, renta, ahorro, nombre
de entidad ni texto libre. El consentimiento sigue siendo previo, revocable y propio.

## Próximas fases

1. Catálogo trazable de ofertas hipotecarias públicas, con fecha, condiciones y método de
   actualización; nunca mezclar publicidad con benchmark neutral.
2. Importación asistida de FEIN con confirmación campo a campo y borrado inmediato por defecto.
3. Cobertura municipal tras normalizar códigos INE y validar que cada indicador existe a ese
   nivel.
4. Informe descargable para llevar a la negociación, con tabla de diferencias y preguntas.
