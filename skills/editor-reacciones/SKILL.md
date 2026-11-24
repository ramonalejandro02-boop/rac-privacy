---
name: editor-reacciones
description: Edita clips de farándula y en vivos (YouTube, podcasts, realities) como videos de reacción de 1 minuto para Facebook/Instagram Reels, con la cara del creador como presentador, su voz clonada en voz en off, escenas animadas con chistes, subtítulos, temas de color y zonas seguras. Úsala SIEMPRE que haya un clip listo para editar, cuando otro proceso (por ejemplo la captura de clips de un en vivo) termine de guardar un clip, o cuando el usuario pida "edítalo", "hacé el video", "sacá el reel" o "pasalo por el estudio".
---

# Editor de reacciones

Convertís un clip ajeno en un video **propio** de ~1 minuto: gancho con ellos, ellos hablan, el creador interviene 2–3 veces con escenas animadas y su voz clonada, y cierra con una pregunta para comentarios. Todo el motor está en `scripts/`.

> Si esta sesión ya tiene otra skill trabajando (por ejemplo, capturando clips de un en vivo), **no la interrumpas**: cuando termine de guardar cada clip, aplicá este flujo a ese clip. Seguí sacando clips con la otra skill y editando con esta, uno por uno.

## 0. Primera vez (instalación)

Rutas: `ESTUDIO = <carpeta de esta skill>/scripts`. Python del estudio: `~/.estudio/venv/bin/python` (Windows: `~\.estudio\venv\Scripts\python.exe`). Llamalo `PY`.

1. Si no existe `~/.estudio/venv`, corré `python3 $ESTUDIO/instalar.py` (tarda: descarga ~3 GB de modelos). Si falta ffmpeg y no se instala solo, decile al usuario el comando que imprime.
2. Si `~/.estudio/config.json` no tiene `voz` y `presentador`, pedíselos al usuario **una sola vez**:
   - `voz`: audio de 15–30 s con su voz real, sin música (una nota de voz sirve). Usá solo los primeros 15 s más limpios (`ffmpeg -t 15`).
   - `presentador`: video suyo hablando o simulando hablar (idealmente con el fondo ya quitado/negro). Si viene en espejo (letras al revés), `--espejo`.
   - `PY $ESTUDIO/instalar.py --config --voz RUTA --presentador RUTA [--espejo]`
3. La voz y el video del usuario son **privados**: nunca los subas a ningún lado.

## 1. Analizar el clip

```
PY $ESTUDIO/analizar.py CLIP.mp4 TRABAJO/
```
Leé `TRABAJO/transcripcion.txt` y `info.json` y **mirá** `TRABAJO/hoja.png`. Después pedí cuadros con cuadrícula de los momentos clave:
```
PY $ESTUDIO/analizar.py CLIP.mp4 TRABAJO/ --cuadros 2 9.5 16 --sin-transcribir
```
y miralos (`TRABAJO/cuadros.png`). Averiguá:
- **De qué va** y cuál es el chiste natural (la contradicción, la reacción, lo absurdo).
- **Quién habla** y dónde está en cada toma (x, y de 0 a 1 según la cuadrícula; cabeza y pecho).
- **Cortes de toma** (`info.json`) y **texto pegado** de la página que subió el clip (arriba o abajo): hay que recortarlo con `recorte_fuente`. También los bordes negros (`contenido_y`).
- Si el clip es largo, elegí la **mejor ventana**: el video final debe durar **45–65 s**.

## 2. Escribir el plan

Copiá `scripts/planes/ejemplo.json` y adaptalo (formato completo en `referencias/formato_plan.md`). Seguí **todas** las reglas de `referencias/guia_estilo.md`. Lo esencial:
- **Arranca con ellos** (la frase más fuerte o la pregunta que engancha), nunca con el presentador.
- **Ellos hablan bastante** y después interviene el creador: 2–3 escenas de 4–7 s. El original no debe pasar del **~55 %** del video.
- **Pocos sonidos**: 2–3 efectos en todo el video. `"sfx_transiciones": false`.
- `"quitar_silencios": true`. En las reacciones donde la pausa es el chiste, `"silencios": false` en ese tramo.
- Chistes en **jerga dominicana**, pícaros pero **sin difamar** (nunca afirmes hechos de personas reales) y **sin burlarse del cuerpo, la salud o una discapacidad** de nadie.
- `"tema": "auto"` (cambia los colores en cada video) o uno de `caribe`, `atardecer`, `menta`, `noche`.

## 3. Revisar recortes de las escenas (antes de renderizar)

```
PY $ESTUDIO/verificar.py recortes CLIP.mp4 TRABAJO/recortes.png 12.4:0.5,0.35,0.92,0.62 29.6:...
```
Miralos. Si la persona sale cortada, con huecos, o con un objeto del fondo pegado (manchas encima de la cabeza), cambiá el segundo `congelar` o ajustá la `caja` y repetí.

## 4. Renderizar

```
PY $ESTUDIO/montaje.py CLIP.mp4 SALIDA.mp4 --plan PLAN.json --palabras TRABAJO/palabras.json --usar-config
```
Tarda ~8–12 min por minuto de video (la voz clonada se guarda en caché: repetir es más rápido). Corrélo en segundo plano si la herramienta lo permite. Para re-renderizar sin cambiar los eventos del original, reutilizá la base: el log imprime la carpeta temporal; pasá `--base CARPETA/base.mp4`.

## 5. Verificar (obligatorio antes de entregar)

1. **Audio por partes** (la carpeta temporal la imprime el montaje):
   `PY $ESTUDIO/verificar.py audio SALIDA.mp4 CARPETA_TEMPORAL/`
   Cada parte debe tener sus palabras completas. Si una palabra se corta en el borde de un tramo, uní o mové los tramos `orig`. Si a la voz clonada le faltan palabras, revisá el texto.
2. **Zonas seguras de Reels**: `PY $ESTUDIO/revisar_zonas.py SALIDA.mp4 TRABAJO/zonas.png 1 10 20 30 40` y mirá que ningún texto, cara ni emoji caiga en lo rojo.
3. **Mirá cuadros** de cada escena y de las partes del original: que se vean las caras (si en una toma abierta sobra pared, subí `s` del zoom a ~1.9).

Si algo falla, corregí el plan y re-renderizá. **No entregues sin verificar.**

## 6. Entregar

- Guardá el video en la carpeta `salida` de `~/.estudio/config.json` (por defecto `~/Desktop/videos_editados`), con un nombre que diga de qué trata.
- Decile al usuario, en español y con tono cercano: tabla corta de cómo quedó (gancho, ellos, cada intervención con su frase), qué corregiste en la verificación, el porcentaje aproximado de original vs. contenido propio, y una **descripción para publicar** (1–2 líneas, sin links, pocas mayúsculas, crédito al programa, máximo 5 hashtags).
- Si hay algo dudoso (una frase del original que no se entiende, un riesgo legal), decilo.
