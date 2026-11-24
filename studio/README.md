# Estudio de transformación de videos

Convierte un clip en un video nuevo y estilizado:

- **Motion graphics detrás de la persona.** La IA separa a la persona del fondo y pone un fondo animado (rayos, anillos, partículas) que **pulsa con la voz**.
- **Borde de luz (glow)** alrededor de la persona.
- **Cámara inteligente**: sigue la cara y hace **zoom de énfasis** cuando la voz sube.
- **Color grading**: contraste, saturación y look cálido o cinematográfico, con viñeta.
- **Subtítulos automáticos** (Whisper) estilo TikTok, con la palabra activa resaltada y animación "pop".
- Reencuadre a **9:16**, 16:9 o 1:1, y volumen normalizado para redes (-14 LUFS).

## Instalar (en una sesión nueva)
```bash
bash studio/instalar.sh
```

## Usar
```bash
python3 studio/transformar.py entrada.mp4 salida.mp4 --estilo farandula
```

| Opción | Valores |
|---|---|
| `--estilo` | `farandula` (morado/dorado), `neon`, `drama` (rojo/negro), `noticiero` (azul) |
| `--formato` | `9:16` (por defecto), `16:9`, `1:1`, `original` |
| `--fondo` | `motion` (gráficos), `blur` (fondo original desenfocado), `original` |
| `--inicio` / `--duracion` | recortar el fragmento (segundos) |
| `--espejo` | voltear horizontalmente |
| `--zoom 1.2` | acercamiento base |
| `--sin-subs`, `--sin-glow` | desactivar subtítulos o glow |
| `--subs-json` | usar subtítulos propios `[{"t":"palabra","a":0.5,"b":0.9}]` |

Velocidad aproximada en CPU: unos 3 cuadros por segundo a 1080x1920.

## Efectos por palabra clave (`efectos.py`)

Cuando se dice una palabra clave aparece un efecto sincronizado: emoji animado, sticker de texto, lluvia o ráfaga de emojis, zoom al que habla, temblor, flash y efecto de sonido (pop, boing, whoosh, ding, silbido, bajada, boom; todos sintetizados, sin licencias).

```bash
# automático: diccionario de palabras clave -> emojis y sonidos
python3 studio/efectos.py entrada.mp4 salida.mp4 --auto
# con plan creativo (mejor resultado)
python3 studio/efectos.py entrada.mp4 salida.mp4 --plan studio/planes/ejemplo_picaro.json
```

Tipos de evento en el plan: `emoji`, `sticker`, `lluvia`, `rafaga`, `zoom`, `temblor`, `flash`, `sfx`.
Cualquier evento acepta `"sfx"`, `"temblor": true` y `"flash": true`. Ver `planes/ejemplo_picaro.json`.

## Montaje con escenas animadas y voz en off (`montaje.py`)

Intercala el original (unos 5 s con efectos) con **escenas propias** de unos 4 s: la imagen se congela con sonido de disco rayado, la persona aparece recortada como sticker sobre un fondo animado, los emojis actúan el chiste y una **voz en off** (Piper, voz es_MX) lo narra con subtítulos. Después vuelve el original. También sirve para cortar los silencios.

```bash
python3 studio/montaje.py entrada.mp4 salida.mp4 --plan studio/planes/montaje_picaro.json
```

En cada escena se define: `congelar` (segundo), `caja` (recorte de la persona [x0,y0,x1,y1] de 0 a 1), `texto`, `voz`, `estilo`, `props` (emoji con animación `rebote`, `desliza`, `orbita`, `crece`, `cruza` o `pulso`) y `eventos`.

## Tu voz clonada en las voces en off

```bash
python3 studio/montaje.py entrada.mp4 salida.mp4 --plan plan.json --mi-voz mi_voz.m4a
```
`mi_voz` = 15 a 30 s de tu voz hablando natural (una nota de voz de WhatsApp sirve). Usa Chatterbox Multilingual (MIT, local, mantiene tu acento y le agrega una marca de agua inaudible de audio generado por IA).

## Presentador en pantalla (`--presentador`)

```bash
python3 studio/montaje.py entrada.mp4 salida.mp4 --plan studio/planes/montaje_presentador.json \
    --presentador mi_video.mov --presentador-espejo --mi-voz mi_voz.m4a
```
Te recorta de tu video (fondo negro o normal) y te pone en grande en la intro (`"presentador": "grande"` en la escena) y en la esquina durante el resto. Detecta cuándo movés la boca: con voz en off usa tus cuadros "hablando" y mientras hablan otros, tus cuadros "escuchando". Descarta solo los cuadros con objetos encima de tu cabeza.

## Temas de diseño (`"tema"` en el plan)

`caribe`, `atardecer`, `menta`, `noche`, o `auto` (por defecto: elige uno distinto según el video).
Cada tema trae su paleta de stickers, el color de la pastilla de los subtítulos y fondos animados
con patrones distintos (`ondas`, `burbujas`, `puntos`, `rayos`) para la base y para cada escena.
Letras: Inter Display Bold (stickers y títulos) y ExtraBold con borde fino y sombra suave (subtítulos).
