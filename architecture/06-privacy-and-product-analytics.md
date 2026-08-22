# Privacidad y analítica de producto

## Decisión de diseño

Renta, ahorro, deudas, precio de compra y condiciones de una oferta hipotecaria no se
guardan en cookies ni se envían a plataformas publicitarias. Son datos necesarios para
el cálculo, pero no para identificar a la persona.

El MVP aplica estas reglas:

1. El escenario se envía por `POST`; nunca aparece en una URL.
2. `POST /mortgages/review` calcula la respuesta en memoria y no persiste la petición.
3. La recuperación del escenario usa `localStorage` solo tras una acción afirmativa.
4. El usuario puede borrar el escenario desde la propia interfaz.
5. No hay trackers, píxeles ni cookies de analítica habilitados por defecto.

## Medición consentida

La analítica propia mide eventos como `review_started`, `review_completed` o
`market_compared`, pero no incluye importes, renta, deuda, ahorro, precio, dirección,
identificadores bancarios ni el contenido de una FEIN. Esos campos no están permitidos por
el esquema de la API. Los conteos de alertas, esfuerzo y LTV se agrupan en intervalos y la
geografía no es más precisa que provincia.

La capa de consentimiento muestra aceptación y rechazo equivalentes. La cookie funcional
`iacp_consent` recuerda la preferencia y `iacp_visitor`, propia y HttpOnly, solo se crea al
aceptar. Al retirar el consentimiento se eliminan el identificador y sus eventos. Los datos
caducan según `PRODUCT_DATA_RETENTION_DAYS` y se purgan mediante el endpoint administrativo.

Las preguntas se guardan en una tabla separada únicamente cuando la persona acepta el
aviso junto al formulario. Su texto no se copia a la tabla de eventos. Antes de producción,
el responsable debe completar los avisos legales con su identidad, contacto, finalidad,
base jurídica, conservación y procedimiento de ejercicio de derechos.

## Evolución con cuenta de usuario

Si el producto incorpora expedientes persistentes, requerirá una finalidad y plazo de
conservación explícitos, cifrado, control de acceso, descarga y borrado. Esa evolución no
debe reutilizar silenciosamente los escenarios anónimos del MVP.
