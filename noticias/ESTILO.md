# Reglas de los videos de noticias

## Estilo visual: rotar siempre
Cada video usa un estilo distinto al anterior (catálogo: `.claude/skills/fabrica-reels/estilos.md` en la rama de la fábrica de reels).

| # | Video | Estilo |
|---|---|---|
| 01 | Licencias por primera vez | Collage de periódico + mapa (/ilustracion5 + /ilustracion6) |
| 02 | Congreso 4.0 con el PNUD | Keynote oscura (/cine10) |
| 03 | Transferencias de Gobernación | Periódico |
| 04 | Gabinete Social | Periódico |
| 05 | Permiso de operación en línea | Periódico |

Siguientes a usar, en orden: pizarra blanca (/cine4), plano técnico (/cine7), papel recortado (/ilustracion3), terminal retro (/cine9), pixel art (/pixel1-3), papel crema infografía (/ilustracion4), keynote oscura, periódico… sin repetir dos veces seguidas.

## Audio
- Sin música. Solo voz (es-HN-CarlosNeural, voseo) y efectos de sonido.
- Sin silencios: pasar cada frase por `herramientas/tighten.py` (recorta pausas internas a 0.09 s y bordes), 0.06 s entre escenas, cierre de 1 s máximo.
- -14 LUFS.

## Guion
- Sin muletillas: nada de "Y…", "También…", "Además…", "La meta:", "Ojo con esto".
- Arrancar con algo que la gente vive o siente (gancho emocional), cerrar con una pregunta que invite a comentar.

## Lo que NO lleva
- Fecha en pantalla.
- Línea de fuente dentro del video.
- Nombres de organizaciones beneficiarias (solo montos o descripciones genéricas).
