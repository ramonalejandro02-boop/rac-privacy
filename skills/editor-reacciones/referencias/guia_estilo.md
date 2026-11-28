# Guía de estilo (lo que el creador aprobó)

## Estructura que retiene
1. **Gancho con ellos (0–3 s):** la frase más fuerte, la pregunta que engancha o la cara de shock **sin revelar** todavía lo que vieron. Si el gancho no es el inicio del clip, después volvé al principio con un sticker "⏪ DESDE EL PRINCIPIO" (un solo sonido `scratch`, volumen 0.45).
2. **Ellos hablan** tramos largos (5–12 s). Que se entienda la historia.
3. **Intervenciones** (2–3): escena animada con la persona congelada como sticker, emojis actuando el chiste, texto grande y la voz clonada. Frases de 1–2 oraciones (4–7 s). Si el clip tiene suspenso (algo que se revela), una intervención antes de la revelación que lo aumente ("ya van cuatro veces que le dicen... y todavía no lo encuentra").
4. **Cierre:** última escena con pregunta para comentarios: "¿Y tú qué dices...? Déjalo en los comentarios."
5. Duración final **45–65 s**. Original ≤ ~55 %.

## Humor
- **Jerga dominicana:** tíguere, jeva, diache, dique, un chin, ¡qué embuste!, pariguayo, mi loco, pana, chercha, colmado, pica pollo, dar cotorra, vaina, manito. Tuteo ("¿y tú qué dices?"), no voseo.
- **Pícaro / doble sentido** suave está bien (🍑🪵😏), nunca explícito.
- El chiste sale de **lo que dijeron**: la contradicción ("le preguntaron por su dinero y salió con que el dinero ajeno no te importa"), lo absurdo, la reacción.
- **Prohibido:** afirmar hechos sobre personas reales (difamación: si alguien menciona a otra persona famosa, el chiste es sobre quien habla, nunca "confirmes" nada); burlarse del cuerpo, estatura, salud, discapacidad, raza u orientación de nadie (además Meta lo castiga como acoso). Groserías del original: en subtítulos tapalas (`p***`) editando `palabras.json`.
- **NUNCA repetir lo que dijeron** ("dijo que no le gusta la comida... ¡no le gusta la comida!" = aburrido).
  El comentario tiene que SUMAR: exageración absurda, comparación dominicana (colmado, motoconcho,
  la abuela, el tío en la boda), lo que no se ve (qué piensa el otro, qué pasa detrás), o un remate
  que termina distinto de lo esperado. Si el chiste funciona sin haber visto el clip, no sirve.
- La voz en off **comenta**, no narra lo que ya se ve (Meta baja el alcance de "narrar lo que está en pantalla").

## Ritmo y sonido
- Quitar silencios y muletillas (`"quitar_silencios": true`). Risas largas del original: dejá ~1 s.
- Efectos de sonido con intención (no en cada segundo): disco rayado al congelar en cada pausa,
  `whoosh` al volver al clip, `pop` en stickers, `boom` suave en los remates/zooms de golpe, piii en
  groserías. Volúmenes 0.3–0.45 para que no tapen las voces.
- Sin texto con "..." en la voz en off (la voz se frena).

## Visual
- Zooms (eventos `zoom`) a la cara de quien habla (`s` 1.4–1.7; en tomas abiertas 1.9–2.0 para que no sobre pared). Un zoom de golpe (`rampa` 0.08–0.15) en el remate.
- Emojis a los lados de las caras, nunca encima de una cara.
- Stickers cortos (2–5 palabras + emoji), en `y` ≈ 0.29.
- Recortar textos pegados de otras páginas (`recorte_fuente`) — Meta pide no mostrar marcas de terceros.
- El motor ya respeta las **zonas seguras de Facebook Reels** medidas en un video publicado (1080×1920): arriba 0–250 px, abajo desde y=1680, botones a la derecha x>900 entre y=1240 y 1680, y ~80 px de orilla por lado. Subtítulos en y≈1420 sin pasar de x=900. También cambia el **tema de colores** en cada video.

## Políticas de Meta (resumen, marzo 2026)
- Es original cuando el foco es **la presencia en pantalla del creador presentando algo nuevo** (comentario, análisis, chiste). Por eso el creador sale todo el video en la esquina y con su voz.
- Bajan el alcance: solo mirar o reaccionar con caras, pegar clips, narrar lo que se ve, ediciones mínimas (bordes, subtítulos, velocidad), marcas de agua de terceros.
- Si el dueño del programa registró el video en Rights Manager, el audio original se puede detectar igual: no prometas que no habrá reclamos.

## Descripción para publicar
1–2 líneas, sin links, pocas mayúsculas, crédito ("Clip: Alofoke Radio Show"), máximo 5 hashtags. Ej.:
`La Fruta escribió un libro: "Vive tu vida" 📚😂 ¿Tú lo comprarías? Clip: Alofoke Radio Show #lafruta #alofoke #humor #rd #farandula`
