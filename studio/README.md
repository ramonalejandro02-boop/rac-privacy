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
