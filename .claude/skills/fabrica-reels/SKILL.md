---
name: fabrica-reels
description: Crea reels verticales (9:16) a partir de una frase y un código de estilo (/3d1, /cine9, /pixel2…). Úsala cuando el usuario diga "hazme un reel/vídeo /<estilo> sobre…", pida ideas de reels, guion, fotogramas, storyboard o prompts de imagen/vídeo para Instagram, TikTok o Shorts.
---

# Fábrica de Reels (versión propia)

Flujo en 3 pasos: **elige estilo → escribe idea y aprueba guion + fotogramas → recibe el vídeo**.
El catálogo de los 51 estilos está en `estilos.md` (mismo directorio). Léelo siempre antes de escribir el guion.

## Cómo se pide

```
Hazme un vídeo con el estilo /<código> . Mi idea: <una frase>
```
Opcional: `usa mi personaje` (+ imagen), `voz: <nombre>`, `idioma: <idioma>`, `duración: 30|45|60 s`.
Si no hay código de estilo, propón 3 estilos de `estilos.md` que encajen con la idea y deja elegir.

## Paso 1 — Brief (preguntar solo lo que falte)
- Estilo (código), idea, público, CTA (seguir, comentar palabra clave, link en bio, guardar).
- Personaje: imagen del usuario o personaje genérico del estilo.
- Voz: clonada (ElevenLabs) o voz de catálogo. Idioma del vídeo.
- **Por defecto: español latino** (voz es-MX, p. ej. `es-MX-JorgeNeural` / `es-MX-DaliaNeural`), montos en dólares con formato `$70,000`, vocabulario neutro latino ("tú", "video", "rendimiento", "asesoría"). Nunca voz de España salvo que se pida.

## Paso 2 — Guion + fotogramas (PARAR y pedir aprobación)
Entrega en este formato y espera un "ok" antes de producir:

1. **Gancho (0–2 s)**: una frase que abra un hueco de curiosidad o un dato chocante. Texto en pantalla ≤ 6 palabras.
2. **Guion por escenas** (tabla): `# | tiempo | voz en off | texto en pantalla | visual | SFX`.
   - 6–10 escenas para 30–45 s. Frases cortas (≤ 12 palabras), una idea por escena.
   - Cada 3–5 s algo cambia en pantalla (corte, zoom, objeto nuevo, cifra).
   - Cifras concretas y verificables; si el dato no es seguro, márcalo como `[verificar]`.
   - Giro o payoff antes del cierre; CTA en la última escena.
3. **Fotogramas clave**: un prompt de imagen por escena, construido con el *bloque visual* del estilo + la acción de la escena + `vertical 9:16, sin texto incrustado`.
4. **Pie de post**: caption (gancho + 2–3 líneas de valor + CTA), 3–5 hashtags.

## Paso 3 — Producción
Según las herramientas disponibles en la sesión:
- **Imágenes / clips**: generar cada fotograma con el prompt aprobado (skills de imagen/vídeo: `creative-claw:*`, `aitopia:*`, `social-media-skills:kling|runway|veo-3|flux|nano-banana`, o CoDesign `asset_generate`). Mantener el mismo personaje y paleta en todas las escenas (usar la imagen del personaje como referencia).
- **Voz**: ElevenLabs (voz clonada o de catálogo) con el texto de "voz en off".
- **Montaje**: Remotion (`remotion:*`) o CoDesign → MP4 1080×1920, 30 fps, subtítulos palabra a palabra resaltando la palabra activa, música de fondo a −18/−20 dB bajo la voz, SFX en cada corte/cifra.
- Si no hay herramientas de render, entregar el paquete listo para CapCut: guion, prompts, textos de subtítulo y lista de SFX/música.

## Reglas de calidad
- Primer fotograma = miniatura: personaje + objeto principal + contraste alto.
- Subtítulos dentro de la zona segura (evitar 15 % superior y 20 % inferior).
- Nada de marcas, personajes o estilos protegidos de terceros: personajes propios.
- Datos reales o marcados para verificar. Nada de promesas de resultados.

## Identidad visual de referencia (tokens)
Oscuro, minimalista, acento azul hielo:
```
--background:#070707  --surface:#111315  --foreground:#eef2f4  --muted:#9aa4aa
--accent:#d0e1e8      --accent-foreground:#0e191e
--border:rgba(255,255,255,.1)  --border-strong:rgba(255,255,255,.18)  --glow:rgba(208,225,232,.08)
Tipos: Space Grotesk (títulos) · Onest (texto) · JetBrains Mono (códigos /estilo, cifras)
```
