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

## Medición futura

La analítica de producto puede medir eventos como `review_started`, `review_completed` o
`market_compared`, pero no debe incluir importes, renta, deuda, dirección, identificadores
bancarios ni el contenido de una FEIN. Los conteos de alertas se agruparán en intervalos
y la geografía no será más precisa que provincia.

Antes de activar cookies no esenciales se incorporará una capa de consentimiento con
aceptación y rechazo equivalentes. La preferencia de consentimiento será el único dato
apropiado para una cookie funcional específica.

## Evolución con cuenta de usuario

Si el producto incorpora expedientes persistentes, requerirá una finalidad y plazo de
conservación explícitos, cifrado, control de acceso, descarga y borrado. Esa evolución no
debe reutilizar silenciosamente los escenarios anónimos del MVP.
