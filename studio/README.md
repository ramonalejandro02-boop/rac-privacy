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
