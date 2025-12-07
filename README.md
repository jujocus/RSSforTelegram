# RSS

Modifica el .py para especificar el RSS de google news, y el .yml en .github/workflows para cambiarle el nombre.

1. Crea un canal.
2. Crea un bot con @BotFather, un bot de telegram que te permite generar el tuyo propio. Te dará el token del bot.
3. Escribe al canal que has creado.
4. Ve a https://api.telegram.org/bot<TU_TOKEN>/getUpdates para ver el ID de tu canal, empieza por -
5. Una vez con el token y el id, ve a github, settings en tu repositorio y en security en la izquierda, ve a "Secrets and variables"
6. Genera dos secrets, TELEGRAM_CHAT_ID y TELEGRAM_TOKEN, con sus respectivos valores
7. Finalmente, ve a Actions, a la izquierda verás el nombre de la acción del .yml.
8. Dale a run workflow, y ya está. Correrá cada 24 horas.
