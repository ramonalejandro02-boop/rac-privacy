# Reglas de los videos de noticias

## Estilo visual: rotar siempre con la skill Fábrica de Reels
Usar siempre un estilo distinto de `.claude/skills/fabrica-reels/estilos.md`. DESCARTAR los estilos de muchos colores que parecen circo/piñata (pop sticker, /cine15 concurso de ritmo, /pixel6 synthwave, /cartoon2d3 mascota pastel, /3d5 bloques de colores, /cine16 juguete de bloques). Preferir estilos sobrios de pocos colores.

Cada video usa un estilo distinto al anterior (catálogo: `.claude/skills/fabrica-reels/estilos.md` en la rama de la fábrica de reels).

| # | Video | Estilo |
|---|---|---|
| 01 | Licencias por primera vez | Collage de periódico + mapa (/ilustracion5 + /ilustracion6) |
| 02 | Congreso 4.0 con el PNUD | Keynote oscura (/cine10) |
| 03 | Transferencias de Gobernación | Periódico |
| 04 | Gabinete Social | Periódico |
| 05 | Permiso de operación en línea | Periódico |

Siguientes a usar: ver el orden de rotación en `CATALOGO_ESTILOS.md` (empieza por pop sticker e isométrico amarillo/negro).

## Audio
- Sin música. Solo voz (es-HN-CarlosNeural, voseo).
- Efectos de sonido: MÁXIMO 3 en todo el video, suaves, solo en momentos clave. Nada de sonidos continuos (marcador, borrador, tic-tac) ni uno por cada animación.
- Sin silencios: pasar cada frase por `herramientas/tighten.py` (recorta pausas internas a 0.09 s y bordes), 0.06 s entre escenas, cierre de 1 s máximo.
- -14 LUFS.

## Diseño
- No saturar: pocas cosas por escena, mucho espacio libre. Nada de relleno decorativo.

## Guion
- Sin muletillas: nada de "Y…", "También…", "Además…", "La meta:", "Ojo con esto".
- Arrancar con algo que la gente vive o siente (gancho emocional), cerrar con una pregunta que invite a comentar.

## Lo que NO lleva
- Fecha en pantalla.
- Línea de fuente dentro del video.
- Nombres de organizaciones beneficiarias (solo montos o descripciones genéricas).

## Cambiar de estilo = cambiar TODO
Un estilo nuevo no es solo otra paleta. Cada video nuevo lleva diseño, objetos, ideas de escena y tipo de animación distintos
(ej.: periódico = sellos y notas con cinta; pop sticker = stickers con borde blanco, rayos girando, rebotes elásticos, golpe de zoom con destello).
