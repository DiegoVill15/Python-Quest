# Python Quest

Aplicación local para practicar Python mediante una aventura de 45 misiones. La IA crea ejercicios según el nivel y los errores anteriores del alumno, y explica los resultados de sus intentos.

![Python Quest: inicio y aventurero en 3D](docs/screenshots/inicio.jpg)

## Qué demuestra

- **IA con contexto:** recibe la etapa del currículo, las misiones anteriores, las dificultades recientes y las preferencias del alumno.
- **Evaluación verificable:** cada misión incluye dos ejemplos públicos, cuatro casos adicionales y una solución de referencia que debe pasar las pruebas antes de aceptar el ejercicio.
- **Retroalimentación guiada:** las pruebas automáticas deciden si la solución pasa; la IA explica el fallo sin entregar la solución completa. Si el proveedor falla durante la revisión, la aplicación muestra el resultado de las pruebas.
- **Progresión:** nueve mundos, lecciones por etapa, XP, monedas, trofeos y un guardarropa con personajes 3D.
- **Elección de proveedor:** conexiones por CLI o API, con las claves API almacenadas en el llavero del sistema.

Es un proyecto de portafolio para explorar la IA aplicada a la práctica de programación. Su eficacia educativa todavía no se ha medido con estudiantes.

## Capturas

| Mapa y progresión | Editor y ejercicio |
| --- | --- |
| ![Mapa de los nueve mundos](docs/screenshots/mapa.jpg) | ![Enunciado, ejemplos y editor de Python](docs/screenshots/mision.jpg) |

![Misiones recientes: continuar un reto activo o consultar un archivo](docs/screenshots/historial.jpg)

Las capturas se hicieron en una copia local del progreso, sin conexiones API ni preferencias personales. El código visible se escribió para la demostración; las capturas no implican llamadas nuevas a un proveedor de IA.

## Cómo se integra la IA

1. El currículo define el objetivo, las herramientas permitidas y los casos límite de cada etapa.
2. La IA devuelve un ejercicio en JSON con enunciado, pista, pruebas y solución de referencia.
3. La aplicación comprueba las construcciones de Python, ejecuta la referencia contra las pruebas y verifica que el reto aporte una operación o decisión nueva. Puede rechazar y reintentar una generación inconsistente.
4. El alumno escribe su programa. «Ejecutar» permite probarlo sin IA; «Enviar solución» ejecuta las seis pruebas y pide una explicación al proveedor.
5. El resultado actualiza el progreso y las dificultades que recibirá la siguiente misión.

Las comprobaciones detectan inconsistencias, pero no garantizan que todo enunciado generado sea correcto: la IA también puede equivocarse.

## Requisitos

- Python 3.10 o superior
- Node.js y npm solo para modificar el editor web
- Una conexión de IA: Codex CLI, Claude CLI, OpenCode CLI, OpenAI API, Anthropic API, Ollama Cloud, OpenRouter o una API HTTPS compatible con OpenAI.
- Un llavero del sistema disponible si utilizas una clave API (en Linux suele requerir Secret Service).

**Uso local y personal:** el programa ejecuta código con los permisos de tu usuario. No lo expongas como servicio público ni multiusuario; consulta [los límites de seguridad](#seguridad-y-datos).

## Iniciar

```sh
git clone https://github.com/DiegoVill15/Python-Quest.git
cd Python-Quest
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

En Windows usa `py -3.12 -m venv .venv`, `.venv\Scripts\pip install -r requirements.txt` y `.venv\Scripts\python app.py`.
Usa una versión instalada de Python desde 3.10. Abre <http://127.0.0.1:5001>. Los retos y el progreso se guardan en `data/`.
No necesitas Node.js para iniciar: el repositorio incluye la interfaz ya compilada.
El código de cada misión activa se guarda en el navegador para recuperarlo al recargar la página.
El botón «Ejecutar» prueba tu código con una entrada que escribas o con un ejemplo público. Muestra la salida y los errores sin usar IA ni cambiar el progreso. «Enviar solución» sí revisa las seis pruebas de la misión.
«Misiones recientes» abre los últimos cinco retos creados. «Continuar» recupera el borrador de una misión activa; «Ver archivo» permite consultar la lección, el enunciado y los ejemplos de un reto anterior, sin volver a enviarlo ni ganar recompensas.
La campaña tiene nueve mundos de cinco misiones (45 en total). Las tres nuevas aldeas enseñan herramientas numéricas, limpieza de texto, pertenencia, control de bucles, orden, recorridos anidados y un proyecto integrador de expedición. Cada mundo se desbloquea al completar el anterior. Puedes reiniciar una aldea sin perder XP, trofeos ni mundos desbloqueados.
Cada misión completada por primera vez entrega 30 XP y 10 monedas. En la ventana del guardarropa puedes ponerle nombre a tu aventurero, probar ropa y objetos en 3D, girar el personaje, comprar piezas y equiparlas. Los objetos raros, legendarios y míticos requieren completar los mundos indicados. Reiniciar una aldea conserva el equipo y no vuelve a entregar monedas por etapas ya premiadas.
El currículo mantiene una única ficha por etapa con prerrequisitos, objetivos, herramientas permitidas y prohibidas, entrada, casos límite, errores habituales y ejemplos ejecutables. Al arrancar se validan las 45 etapas y sus salidas; las soluciones generadas se comprueban contra las herramientas enseñadas.
Cada misión empieza con el editor vacío. Las etapas añaden conceptos y pasos nuevos; la IA recibe los enunciados anteriores, errores recientes y preferencias resumidas para adaptar la siguiente misión. Los comentarios nuevos se compactan durante esa misma generación; no se hace una llamada adicional.
En «Conexión de IA» selecciona la CLI o añade una clave API. Inicia la sesión de la CLI por tu cuenta (`codex login`, `claude login` u `opencode auth login`). OpenCode Go se elige mediante su ID de modelo en OpenCode. Al abrir «Conexión de IA» o cambiar de proveedor se cargan automáticamente los modelos de Codex, Claude, OpenCode o una API. El desplegable conserva todas las opciones después de elegir; pulsa «Usar este modelo» para guardar. Codex usa `app-server` y Claude su protocolo de inicialización, sin enviar prompts; las opciones dependen de la sesión y la versión instalada. La opción «Escribir ID manualmente…» permite usar otro modelo o continuar si el listado no está disponible. El inicio de sesión de ChatGPT en Codex es distinto de una clave OpenAI API.
Las claves API se guardan en el llavero del sistema y no en `data/state.json`; si el llavero no está disponible, la conexión no se guarda. Cada reto y revisión consume uso o créditos del proveedor seleccionado. Los errores de sintaxis se muestran sin llamar a la IA.

Para Ollama Cloud u OpenRouter, abre «Añadir una conexión API», elige el proveedor y pega su clave. Las direcciones del servidor ya están configuradas y los modelos se cargan automáticamente. [Ollama Cloud](https://ollama.com/settings/keys) usa `https://ollama.com/v1`, sin instalar Ollama localmente. Su [plan Free](https://ollama.com/pricing) incluye uso inicial limitado y acceso a modelos de inicio; el catálogo puede mostrar modelos que necesiten saldo adicional. Ollama Cloud no admite JSON forzado: enviamos el esquema en el prompt y rechazamos respuestas que no sean JSON válido.

[OpenRouter](https://openrouter.ai/settings/keys) usa `https://openrouter.ai/api/v1`. El desplegable muestra las variantes `:free` y `openrouter/free`, que elige automáticamente un modelo gratuito. Se aplican límites de uso y disponibilidad; escribir manualmente un modelo de pago puede consumir créditos. No se cambia de proveedor ni se compra saldo automáticamente.

Python Quest acepta conexiones locales y las del dispositivo Mac dentro de tu red Tailscale. El servidor Python sigue escuchando solo en `127.0.0.1`; Tailscale Serve reenvía el tráfico de la red privada.

## Abrir desde Windows con Tailscale

Con Tailscale activo en ambos equipos, abre `http://<IP-Tailscale-de-la-Mac>:5000` en Windows. En la Mac consulta la dirección actual con `tailscale ip -4`. También puedes usar el nombre del equipo que muestra `tailscale serve status`. La instalación de este proyecto y sus datos permanecen en la Mac; el navegador de Windows guarda sus propios borradores del editor.

Si Tailscale Serve no está configurado, en la Mac ejecuta `tailscale serve --bg --tcp=5000 tcp://127.0.0.1:5001`. Usa **Serve**, no Funnel: Serve comparte el puerto solo con dispositivos autorizados en tu red Tailscale.

## Modificar la interfaz

El editor CodeMirror y las imágenes de Kenney se sirven desde `static/`, sin depender de una CDN. Después de cambiar `static/app.js`, reconstruye el archivo servido por Flask:

```sh
npm ci
npm run build
```

Los recursos de `static/assets/kenney/` son de [Kenney UI Pack Pixel Adventure](https://kenney.nl/assets/ui-pack-pixel-adventure), licencia CC0. Los personajes 3D y el bastón de `static/assets/kaykit/` proceden de la versión gratuita 2.0 de [KayKit Adventurers](https://kaylousberg.itch.io/kaykit-adventurers), también CC0. Las demás piezas visuales del guardarropa son adaptaciones propias.

## Seguridad y datos

Esta versión ejecuta código escrito por el usuario y una solución de referencia creada por la IA. Los límites de tiempo y salida no aíslan el código del sistema: un programa puede acceder a archivos y recursos con los permisos de tu usuario. Permite acceso solo a tus dispositivos de confianza; no la publiques en Internet ni como servicio multiusuario. La opción de API compatible acepta únicamente servidores HTTPS públicos.

El contexto del ejercicio y el código enviado para revisión se comparten con el proveedor de IA seleccionado. No incluyas contraseñas ni datos sensibles en el editor o en tus comentarios.

El progreso se guarda en `data/state.json` y los borradores en el navegador. `data/`, el entorno de Python, las dependencias instaladas, los registros y los archivos `.env` están excluidos del repositorio. Las claves API se guardan en el llavero del sistema.

## Probar

```sh
.venv/bin/python -m unittest discover -s tests
npm ci
npm test
```

Las pruebas usan respuestas simuladas de los proveedores y no necesitan claves API ni consumen créditos. GitHub Actions ejecuta las pruebas y comprueba que la interfaz compilada esté actualizada.

## Estructura

- `app.py`: servidor Flask y rutas de la aplicación.
- `quest/curriculum.py`: currículo y lecciones de las 45 etapas.
- `quest/codex_teacher.py` y `quest/schemas/`: instrucciones y formatos JSON para la IA.
- `quest/providers.py`: conexiones, modelos, claves y uso reportado por el proveedor.
- `quest/service.py`, `quest/grader.py` y `quest/store.py`: validación, ejecución, progreso y persistencia.
- `static/` y `templates/`: interfaz con CodeMirror y personajes con Three.js.
- `tests/`: comprobaciones del currículo, la evaluación, las conexiones, el progreso y la navegación.

## Licencia

El código del proyecto se distribuye bajo la [licencia MIT](LICENSE), a nombre de Diego Villalobos. Los recursos de Kenney y KayKit conservan sus licencias CC0 y sus avisos en `static/assets/`. Las dependencias conservan sus propias licencias.
