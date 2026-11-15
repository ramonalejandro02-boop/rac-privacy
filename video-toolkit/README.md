# Kit de edición de video

Herramientas para editar video desde Claude Code: motion graphics, texto detrás de las personas, subtítulos automáticos, mejora de sonido y filtros estilo película.

## Instalación

```bash
bash video-toolkit/setup.sh
source ~/video-env/bin/activate
```

## Herramientas

| Qué hace | Comando |
|---|---|
| **Texto detrás de la persona** (video o foto) | `python scripts/text_behind.py in.mp4 out.mp4 --text "IMPARABLE" --color "#ffcc00" --start 1 --end 5` |
| **Filtro de película** | `scripts/film_look.sh in.mp4 out.mp4 teal-orange` (estilos: `teal-orange`, `kodak`, `noir`, `bleach`, `vintage`, `matrix`, `lut=archivo.cube`) |
| **Mejorar sonido** | `scripts/clean_audio.sh in.mp4 out.mp4 voz` (presets: `voz`, `podcast`, `ligero`, `musica`) |
| **Subtítulos automáticos** | `python scripts/subtitles.py in.mp4 --lang es --burn` → `.srt`, `.ass` animado, `.captions.json` |
| **Motion graphics** | `cd remotion && npx remotion studio` (editor visual) o `npx remotion render src/index.ts KineticTitle out/titulo.mp4 --props='{"title":"HOLA","subtitle":"...","accent":"#ff006e"}'` |

### Opciones útiles

- `text_behind.py`: `--engine rembg` (bordes más precisos, más lento), `--size 0.3` (tamaño), `--y 0.35` (posición vertical), `--font fonts/BebasNeue.ttf`, `--opacity 0.9`, `--shadow`. Varias líneas: `--text "LÍNEA 1\nLÍNEA 2"`.
- `film_look.sh`: variables `GRAIN=0-40`, `VIGNETTE=0`, `LETTERBOX=0` (sin franjas de cine), `HALATION=0`, `FPS24=1`.
- `clean_audio.sh`: `TARGET=-14` (redes), `-16` (podcast), `-23` (TV); `DENOISE=12` (fuerza de la reducción de ruido).
- Remotion `WordCaptions`: copia tu video a `remotion/public/video.mp4` y el `.captions.json` de `subtitles.py` a `remotion/public/captions.json`, y renderiza con `--props='{"videoSrc":"video.mp4","captionsFile":"captions.json","highlight":"#ffd60a"}'`.

### Flujo típico para un Reel

```bash
scripts/clean_audio.sh crudo.mp4 1_audio.mp4 voz
scripts/film_look.sh 1_audio.mp4 2_color.mp4 kodak
python scripts/text_behind.py 2_color.mp4 3_texto.mp4 --text "NUNCA PARES" --start 0.5 --end 3
python scripts/subtitles.py 3_texto.mp4 --lang es --burn
```

## Requisitos de red

- `subtitles.py` descarga el modelo Whisper desde **huggingface.co** la primera vez.
- `--engine rembg` descarga su modelo desde GitHub la primera vez.
