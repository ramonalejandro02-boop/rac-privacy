---
name: video-toolkit
description: Edición de video con el kit del repositorio (video-toolkit/). Úsala cuando el usuario quiera editar un video o foto, poner texto detrás de una persona, subtítulos automáticos o animados, mejorar/limpiar el audio o la voz, efectos de voz, aplicar un filtro o look de película (color grading, grano, LUT, franjas de cine), cortar silencios, pasar a vertical, montar al ritmo de la música, efectos (cámara lenta, estabilizar, glitch, zoom), o crear motion graphics / títulos 3D / rótulos / transiciones con Remotion.
---

# Kit de video

Todo vive en `video-toolkit/`. Lee `video-toolkit/README.md` para la referencia completa de opciones.

## Cómo llega el material
El usuario siempre envía **primero el video principal** (la persona hablando; su audio manda) y **después las tomas de apoyo** (B-roll). No mezcles su orden: el primer archivo es el principal y los siguientes son de apoyo. Si no está claro cuál es cuál, pregunta antes de editar.

## Antes de empezar
1. Si no existe `~/video-env/bin/python`, ejecuta `bash video-toolkit/setup.sh` (tarda unos minutos).
2. Usa siempre `~/video-env/bin/python` para los scripts de Python.
3. Trabaja sobre copias: nunca sobrescribas el archivo original del usuario.

## Elegir herramienta
- Texto detrás de la persona → `scripts/text_behind.py` (mediapipe para video; `--engine rembg` para fotos o bordes con pelo).
- Look de cine → `scripts/film_look.sh` (elige estilo según el ánimo: `teal-orange` acción/moderno, `kodak` cálido, `noir` dramático, `bleach` crudo, `vintage` nostálgico).
- Audio → `scripts/clean_audio.sh` (`voz` por defecto; `podcast` para ruido fuerte).
- Subtítulos → `scripts/subtitles.py` (necesita huggingface.co; si falla, díselo al usuario y no inventes la transcripción).
- Insertar tomas de apoyo sobre el principal (conserva su audio) → `scripts/broll.py`. Colócalas donde ilustren lo que se dice; si hay transcripción, usa los tiempos de las palabras clave con `--at`. No tapes los primeros 2 s (el gancho con la cara). `--pip` deja a la persona en un recuadro.
- Quitar pausas y silencios → `scripts/auto_cut.sh` (o exportar XML a Premiere/DaVinci con `EXPORT=`).
- Horizontal a vertical siguiendo a la persona → `scripts/reframe.py`.
- Montaje al ritmo de una canción → `scripts/beat_sync.py` (también genera `beats.json` para sincronizar animaciones en Remotion).
- Separar un video largo en escenas → `scripts/scenes.sh`.
- Cámara lenta, estabilizar, zoom de impacto, glitch, fondo desenfocado vertical, 4K, etc. → `scripts/effects.sh` (sin argumentos lista los efectos).
- Voz de locutor, tráiler, radio, teléfono, robot, cambio de tono → `scripts/voice_fx.py`. Ruido muy difícil → `clean_audio.sh ... ia`.
- Títulos animados / motion graphics → proyecto Remotion en `video-toolkit/remotion` (componentes en `src/`; añade composiciones en `src/Root.tsx`). Plantillas: KineticTitle, Title3D, LowerThird, Counter, TransitionsReel, AudioVisualizer, WordCaptions. Las fuentes deben ser locales en `public/fonts` (woff2 para CSS, ttf para textos 3D de drei) porque el Chrome del render puede no tener internet. El 3D y los light leaks necesitan `swangle` (ya en `remotion.config.ts`). Si un render 3D falla una vez sin error claro, reinténtalo.

## Verificar
Extrae un fotograma con `ffmpeg -i out.mp4 -vf "select=eq(n\,60)" -frames:v 1 check.png` y míralo antes de entregar. Para audio, mide con `ffmpeg -i out.mp4 -af ebur128 -f null -`.

Orden recomendado para un video completo: cortar silencios del principal → audio → color (principal y tomas de apoyo con el mismo estilo) → insertar tomas de apoyo → texto detrás → motion graphics → subtítulos (los subtítulos siempre al final para que no reciban el filtro de color).
