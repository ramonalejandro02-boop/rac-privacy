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
| 05 | Permiso de operación en línea | Periódico → pizarra blanca (/cine4), versión final |
| 06 | Amnistía ENEE | Espías de los 60 (/cine5) |
| 07 | Reformas electorales | Art Déco (/cine6) |
| 08 | Gabinete Social: ¿atenderá a la gente? | Maqueta blanca con proyección (/cine1) |
| 09 | Gabinete Social: cómo funcionará | Dibujo de una sola línea (/cine3) y tablero de nodos (/interfaz2) |
| 10 | Licencias siguen en todos los departamentos | Papel recortado (/ilustracion3) |
| 11 | Desempleo +37.6% | Infografía papel crema con figuritas (/ilustracion4) |
| 12 | Inflación 6.98%, la más alta de Centroamérica | Objetos realistas de estudio (/3d3) |
| 13 | Bajan los combustibles: ¿llega la rebaja a la comida? | Producto desmontado, estudio negro con despiece y líneas guía (/cine2) |
| 14 | Reserva estratégica de granos ante El Niño | Miniatura tilt-shift: maqueta vista desde arriba, cámara que viaja (/cine18) |
| 15 | Fin del congelamiento de la tarifa eléctrica | Cuarto de noche con paneles holográficos y foco que se apaga (/3d2) |
| 16 | Poder de compra: el lempira vale menos | Mundo vóxel de bloques 3D con números en píxeles extruidos (/3d6) |
| 17 | Basura en el mercado El Rápido (SPS) | Libro desplegable de papel sobre mesa de madera, piezas pop-up y páginas que pasan (/cine17) |

Siguientes a usar: ver el orden de rotación en `CATALOGO_ESTILOS.md` (empieza por pop sticker e isométrico amarillo/negro).

## Audio
- Sin música. Solo voz (es-HN-CarlosNeural, voseo).
- Efectos de sonido: MÁXIMO 3 en todo el video, suaves, solo en momentos clave. Nada de sonidos continuos (marcador, borrador, tic-tac) ni uno por cada animación.
- Ritmo: voz a velocidad -4% (pausada). `herramientas/tighten.py` deja pausas internas de máx. 0.22 s; 0.38 s entre escenas; cierre de 1.4 s. Sin silencios largos, pero con respiro (que no vaya muy rápido).
- -14 LUFS.

## Diseño
- LEGIBILIDAD PRIMERO: tres zonas fijas que no se pisan — títulos arriba (≈230-470 px), arte al centro (≈500-1330 px), subtítulos abajo (≈1400-1580 px) sin nada encima. Todo texto sobre fondo sólido con contraste. Revisar fotogramas buscando textos tapados antes de renderizar.
- Lo visual puede ser rico: más animaciones y efectos que expliquen, siempre con coherencia (movimiento con sentido: fila impaciente, punto que recorre el tiempo, rayitas de énfasis, vibración al confirmar).
- Lo que NO se satura es el SONIDO.

## Guion
- Sin muletillas: nada de "Y…", "También…", "Además…", "La meta:", "Ojo con esto".
- Arrancar con algo que la gente vive o siente (gancho emocional).
- NUNCA pedir interacción explícita (Meta lo castiga como cebo): nada de "Comentá", "Compartí", "Etiquetá", botones SÍ/NO para votar ni "👇" en el pie de post. Cerrar con una frase que invite sola a contar la experiencia, p. ej. "Todos tenemos alguna historia de cuando sacamos la licencia."

## Lo que NO lleva
- Fecha en pantalla.
- Línea de fuente dentro del video.
- Nombres de organizaciones beneficiarias (solo montos o descripciones genéricas).

## Cambiar de estilo = cambiar TODO
Un estilo nuevo no es solo otra paleta. Cada video nuevo lleva diseño, objetos, ideas de escena y tipo de animación distintos
(ej.: periódico = sellos y notas con cinta; pop sticker = stickers con borde blanco, rayos girando, rebotes elásticos, golpe de zoom con destello).

## Personas reales
- No afirmar quejas, delitos ni fallas de una persona si no hay fuente. Plantearlo como pregunta y dejar que el público cuente su experiencia en los comentarios.
- No mencionar a CONAFEPH ni sus gestiones o reclamos propios en los videos de noticias.

## Estilos PROHIBIDOS (ya usados en otros chats — no repetir)
Pop sticker · isométrico/maqueta amarillo-negro (y /3d4) · caricatura 2D con diálogos (y familia /cartoon2d*) · pro negro/rojo F1 · negro con formas curvas · silueta que camina · plano técnico/blueprint (/cine7) · negro + naranja neón · dibujado a mano animation-studio · cuento 2D ilustrado · mecánica con insertos 3D · bloques naranja/navy · terminal retro (/cine9) · pixel art (familia /pixel*, /cine13, /cine14) · chat que se escribe solo (/interfaz4) · maniquíes 3D (/3d1) · neón radiografía · oscuro corporativo · fondos con casitas · libreta dibujada · 3D primera persona · imágenes IA con paralaje.
Tampoco los de muchos colores tipo circo (/pixel6, /cine15, /3d5, /cine16).

## Estilos DISPONIBLES (Fábrica de Reels, sin usar)
/ilustracion1 rayos X · /ilustracion2 épica oscura · /cine8 vidriera · /cine11 dibujos de los años 30 · /cine12 comedia de ciencia ficción · /3d7 vóxel de cine · /interfaz3 neón paso a paso.
Ya usados en estos videos de noticias (se pueden repetir más adelante, sin seguidos): periódico, keynote oscura, pizarra blanca, espías 60s, Art Déco, maqueta blanca con proyección, una sola línea, tablero de nodos, papel recortado, infografía papel crema, objetos realistas de estudio.

## Zona segura de Facebook Reels (1080×1920, medida en captura real)
- Arriba 0–250 px: lo tapa la barra del celular / perfil. Títulos desde y ≥ 280.
- Abajo desde y = 1680: nombre de la cuenta y texto. Nada importante debajo de 1670.
- Derecha x > 900 entre y = 1240 y 1680: botones de me gusta, comentar, compartir y guardar.
- Lados: Facebook recorta ~60–70 px por lado. Todo lo importante dentro de x 80–1000.
- Subtítulos a y ≈ 1420, dentro de x 80–900 (centro ≈ 490, ancho máx. ≈ 800) para no chocar con los botones.
- Nunca inventar precios, cifras o datos de ejemplo (p. ej. un recibo): si no hay dato real, usar íconos (↑) o texto genérico.
