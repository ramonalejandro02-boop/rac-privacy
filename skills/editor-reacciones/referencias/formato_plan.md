# Formato del plan (JSON)

Coordenadas: `x`, `y` de 0 a 1. En `caja` y `recorte_fuente` son relativas al **cuadro completo** del clip.
En los eventos `zoom` (`x`, `y`) son relativas al clip **ya recortado** con `recorte_fuente`
(y_recortado = (y_cuadro − y0) / (y1 − y0)). En emojis/stickers/props son relativas a la pantalla final 1080×1920.

```json
{
  "tema": "auto",                       // caribe | atardecer | menta | noche | auto
  "quitar_silencios": true,
  "sfx_transiciones": false,
  "base": {
    "recorte_fuente": [0, 0.14, 1, 0.895],   // quita texto pegado arriba y bordes negros
    "titulo": "LA FRUTA Y SU LIBRO\n\"VIVE TU VIDA\" 📚😂",
    "subs_x": 0.63, "subs_ancho": 0.62,
    "claves": ["dinero", "libro"],      // palabras resaltadas en los subtítulos
    "eventos": [ ... ]                  // tiempos del CLIP ORIGINAL
  },
  "secuencia": [                        // orden del video final
    {"orig": [0.0, 3.2]},               // tramo del original (segundos del clip)
    {"orig": [14.5, 22.5], "silencios": false},   // sin quitar pausas (reacción)
    { ...escena... }
  ]
}
```

## Eventos de la base (sobre el original)
| tipo | campos |
|---|---|
| `zoom` | `t`, `dur`, `x`, `y`, `s` (1.0–2.0), opcional `rampa` (s), `lento` |
| `emoji` | `t`, `dur`, `emoji`, `x`, `y`, `size` (180–250) |
| `sticker` | `t`, `dur`, `texto`, `fondo` ("#FFE600" / "#FF3FA4" / "#FFFFFF" / "#00E5FF" → el tema los remapea), `color`, `rot`, `y` (~0.29) |
| `lluvia` | `t`, `dur`, `emoji` (varios), `n` |
| `rafaga` | `t`, `dur`, `emoji`, `x`, `y`, `n` |
| `temblor` | `t`, `dur`, `amp` |
| `flash` | `t`, `dur` |

Cualquier evento acepta `"sfx"` (`pop`, `boing`, `whoosh`, `ding`, `silbido`, `bajada`, `boom`, `scratch`), `"vol"`, `"temblor": true`, `"flash": true`.

## Escena (intervención del creador)
```json
{
  "congelar": 12.4,                        // segundo del clip para la foto
  "caja": [0.5, 0.352, 0.92, 0.62],        // recorte de la persona (cabeza y pecho)
  "texto": "¿EN QUÉ GASTA\nSU DINERO? 📚💸",
  "fondo": "#00E5FF",
  "voz": "Le preguntaron en qué desperdicia su dinero, y el hombre sacó un libro.",
  "claves": ["dinero", "libro"],
  "props": [
    {"emoji": "📚", "anim": "crece",   "x": 0.18, "y": 0.42, "t": 0.3, "size": 210},
    {"emoji": "💸", "anim": "pulso",   "x": 0.84, "y": 0.42, "t": 1.8, "size": 200},
    {"emoji": "🤔", "anim": "rebote",  "x": 0.84, "y": 0.72, "t": 3.6, "size": 190, "sfx": "pop", "vol": 0.5}
  ],
  "eventos": [{"t": 0.3, "tipo": "lluvia", "emoji": "🔥🥵", "dur": 3.5, "n": 14}],
  "temblor": false
}
```
Animaciones de props: `crece`, `pulso`, `rebote`, `desliza` (+ `desde`: "izq"/"der"), `orbita` (+ `radio`, `fase`), `cruza` (+ `dur_cruce`).
`"presentador": "grande"` en una escena pone al creador en grande (intro); por defecto va en la esquina.
