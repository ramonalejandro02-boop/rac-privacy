import json, subprocess, numpy as np, cv2, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
K8 = '/tmp/claude-0/-home-user-rac-privacy/a3ca4fc8-3265-5323-bb3b-e159b4c774c4/scratchpad/k8'
TIM = json.load(open(K8 + '/timing.json'))
S = TIM['scenes']; TOTAL = TIM['total']
FB = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
FBI = '/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf'
FBOLD = '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
_fc = {}
def font(path, size):
    k = (path, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]
clamp = lambda x, a, b: max(a, min(b, x))
prog = lambda t, a, b: clamp((t - a) / (b - a), 0, 1)
easeOut = lambda x: 1 - (1 - clamp(x, 0, 1)) ** 3
def ease(x):
    x = clamp(x, 0, 1); return 2 * x * x if x < .5 else 1 - (-2 * x + 2) ** 2 / 2
def back(x):
    x = clamp(x, 0, 1); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def wT(k, p, n=0):
    ws = [w for w in S[k]['words'] if w['w'].lower().strip(',.:').startswith(p)]
    return ws[n]['s'] if len(ws) > n else 1e9

# ---------- image assets ----------
SEL = '/tmp/sd/sel/'
IM = {}
def load(name):
    if name in IM: return IM[name]
    im = cv2.cvtColor(cv2.imread(SEL + name + '.png'), cv2.COLOR_BGR2RGB)
    im = cv2.resize(im, (W, H), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    bl = cv2.GaussianBlur(im, (0, 0), 1.6); im = np.clip(im * 1.55 - bl * 0.55, 0, 255)  # sharpen after upscale
    d = cv2.imread(SEL + name + '_d.png', 0); d = cv2.resize(d, (W, H)).astype(np.float32) / 255
    d = cv2.GaussianBlur(d, (0, 0), 6)
    IM[name] = (im, d); return IM[name]
GX, GY = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))

def camera(name, u, z0, z1, px=0, py=0, k=0.06, cx=W / 2, cy=H / 2, shake=0, t=0):
    im, d = load(name)
    z = z0 + (z1 - z0) * u
    dz = d - 0.5
    # near pixels zoom more (k) and shift more (px,py)
    zz = z * (1 + k * dz * u)
    sx = cx + (GX - cx) / zz - px * u * dz * 2 + shake * math.sin(t * 57)
    sy = cy + (GY - cy) / zz - py * u * dz * 2 + shake * math.cos(t * 49)
    return cv2.remap(im, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# ---------- shot list ----------
t_perder = wT(0, 'perder')
t_si2 = wT(1, 'si')
t_todo = wT(1, 'todo')
t_prim = wT(2, 'primero')
t_luego = S[3]['start']
t_ylleg = wT(3, 'y')
SHOTS = [  # (start, end, image, params)
    (0.0, t_perder - 0.08, 'D_pov_11', dict(z0=1.0, z1=1.22, k=0.25, py=-40, shake=3, cx=540, cy=430)),
    (t_perder - 0.08, S[1]['start'] - 0.05, 'B_spin_11', dict(z0=1.12, z1=1.0, k=0.2, px=60, shake=5)),
    (S[1]['start'] - 0.05, t_si2 - 0.1, 'C_hands_11', dict(z0=1.0, z1=1.14, k=0.18, px=-40)),
    (t_si2 - 0.1, t_todo - 0.1, 'A_visor_23', dict(z0=1.06, z1=1.2, k=0.2, py=30, cy=900)),
    (t_todo - 0.1, S[2]['start'] - 0.05, 'B_spin_23', dict(z0=1.0, z1=1.1, k=0.25, px=-50, shake=4)),
    (S[2]['start'] - 0.05, t_prim - 0.1, 'E_profile_23', dict(z0=1.15, z1=1.02, k=0.22, px=70)),
    (t_prim - 0.1, t_luego - 0.05, 'F_approach_11', dict(z0=1.0, z1=1.18, k=0.3, py=-40, cy=800)),
    (t_luego - 0.05, t_ylleg - 0.05, 'G_apex_11', dict(z0=1.04, z1=1.16, k=0.25, px=-60)),
    (t_ylleg - 0.05, S[4]['start'] - 0.05, 'H_exit_23', dict(z0=1.25, z1=1.0, k=0.15, px=30, cx=520, cy=560)),
    (S[4]['start'] - 0.05, S[5]['start'] - 0.05, 'I_eye_23', dict(z0=1.0, z1=1.3, k=0.18, cx=560, cy=1060)),
    (S[5]['start'] - 0.05, TOTAL + 1, 'M_kart', dict(z0=1.12, z1=1.0, k=0.2, py=40)),
]
CUTS = [s[0] for s in SHOTS[1:]]

# ---------- overlay drawing ----------
def glow_text(layer, txt, xy, size, fill, path=FB, anchor='mm', stroke=0, glow=0, scale=1.0, alpha=1.0, rot=0):
    if alpha <= 0: return
    f = font(path, max(8, int(size * scale)))
    tmp = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(tmp)
    if glow:
        g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        gd.text(xy, txt, font=f, fill=(0, 0, 0, 200), anchor=anchor, stroke_width=int(size * 0.09), stroke_fill=(0, 0, 0, 200))
        g = g.filter(ImageFilter.GaussianBlur(glow)); tmp = Image.alpha_composite(tmp, g); d = ImageDraw.Draw(tmp)
    d.text(xy, txt, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    if rot: tmp = tmp.rotate(rot, center=xy, resample=Image.BICUBIC)
    if alpha < 1:
        a = tmp.split()[3].point(lambda v: int(v * alpha)); tmp.putalpha(a)
    layer.alpha_composite(tmp)

def reticle(layer, x, y, col, t, size=70, alpha=1.0):
    if alpha <= 0: return
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    pul = (t * 1.3) % 1; c = col + (int(255 * alpha),)
    s = size * (0.6 + 0.4 * back(alpha))
    d.ellipse([x - s, y - s, x + s, y + s], outline=c, width=7)
    r2 = s + 20 + pul * 40; d.ellipse([x - r2, y - r2, x + r2, y + r2], outline=col + (int(140 * (1 - pul) * alpha),), width=4)
    for a in range(4):
        an = a * math.pi / 2; d.line([x + math.cos(an) * (s - 18), y + math.sin(an) * (s - 18), x + math.cos(an) * (s + 16), y + math.sin(an) * (s + 16)], fill=c, width=6)
    d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=c)
    gl = g.filter(ImageFilter.GaussianBlur(10)); layer.alpha_composite(gl); layer.alpha_composite(g)

def pill(layer, txt, x, y, bg, fg, size=46, alpha=1.0):
    if alpha <= 0: return
    f = font(FB, size); d0 = ImageDraw.Draw(layer); bb = d0.textbbox((0, 0), txt, font=f)
    w = bb[2] - bb[0] + size * 1.2; h = size * 1.7
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    x0 = clamp(x - w / 2, 30, W - 30 - w)
    d.rounded_rectangle([x0, y - h / 2, x0 + w, y + h / 2], radius=h / 2, fill=bg + (int(240 * alpha),))
    d.text((x0 + w / 2, y + 2), txt, font=f, fill=fg + (int(255 * alpha),), anchor='mm')
    layer.alpha_composite(g)

def dashed(layer, pts, col, alpha):
    d = ImageDraw.Draw(layer)
    for i in range(0, len(pts) - 1, 2):
        d.line([pts[i], pts[i + 1]], fill=col + (int(255 * alpha),), width=10)

def caption(layer, t):
    sc = next((s for s in S if s['start'] - 0.05 <= t <= s['end'] + 0.25), None)
    if not sc: return
    ws = sc['words']; idx = next((i for i, w in enumerate(ws) if t < w['e']), len(ws) - 1)
    st = (idx // 3) * 3; ch = ws[st:st + 3]; f = font(FB, 64)
    d = ImageDraw.Draw(layer); txts = [w['w'].strip(',.:') for w in ch]
    widths = [d.textlength(s + ' ', font=f) for s in txts]; x = W / 2 - sum(widths) / 2; y = 1590
    for k, s in enumerate(txts):
        i = st + k; on = i == idx and t >= ch[k]['s'] - 0.05
        col = (255, 214, 10, 255) if on else ((255, 255, 255, 255) if i < idx else (255, 255, 255, 150))
        d.text((x, y), s, font=f, fill=col, anchor='lm', stroke_width=7, stroke_fill=(0, 0, 0, 230)); x += widths[k]

RED = (255, 59, 48); GRN = (48, 209, 88); YEL = (255, 214, 10); WHITE = (255, 255, 255, 255)

def overlays(layer, t, shot_i, ls):
    if shot_i == 0:  # hook: reticle near the nose
        a = easeOut(prog(t, 0.05, 0.3))
        glow_text(layer, 'SI MIRAS', (W / 2, 1130), 150, WHITE, glow=18, scale=1 + 0.3 * (1 - a), alpha=a)
        glow_text(layer, 'AQUÍ...', (W / 2, 1290), 170, RED + (255,), glow=18, scale=1 + 0.3 * (1 - easeOut(prog(t, 0.25, 0.5))), alpha=easeOut(prog(t, 0.25, 0.5)))
        reticle(layer, 540, 430, RED, t, 70, easeOut(prog(t, 0.4, 0.7)))
        af = easeOut(prog(t, 0.55, 0.95)); d = ImageDraw.Draw(layer)
        if af > 0:
            y1 = 1030 - (1030 - 545) * af; d.line([540, 1030, 540, y1], fill=RED + (255,), width=12); d.polygon([(512, y1 + 30), (568, y1 + 30), (540, y1 - 8)], fill=RED + (255,))
    if shot_i == 1:
        a = easeOut(prog(ls, 0, 0.18))
        glow_text(layer, 'PIERDES', (W / 2, 360), 160, WHITE, glow=18, scale=1 + 0.4 * (1 - a), alpha=a)
        glow_text(layer, 'LA CURVA', (W / 2, 520), 160, RED + (255,), glow=18, scale=1 + 0.4 * (1 - easeOut(prog(ls, 0.1, 0.3))), alpha=easeOut(prog(ls, 0.1, 0.3)))
    if shot_i == 2:
        a = easeOut(prog(ls, 0.05, 0.3))
        glow_text(layer, 'TUS MANOS', (W / 2, 330), 128, WHITE, glow=16, alpha=a, scale=1 + 0.2 * (1 - a))
        glow_text(layer, 'SIGUEN A', (W / 2, 460), 128, WHITE, glow=16, alpha=easeOut(prog(ls, 0.2, 0.45)))
        glow_text(layer, 'TUS OJOS', (W / 2, 590), 140, YEL + (255,), glow=16, alpha=easeOut(prog(ls, 0.4, 0.65)), scale=1 + 0.3 * (1 - easeOut(prog(ls, 0.4, 0.65))))
    if shot_i == 3:
        a = easeOut(prog(ls, 0.1, 0.4))
        pill(layer, '×  MIRA MUY CERCA', W / 2, 360, RED, (255, 255, 255), 50, a)
        # eye-line arrows pointing down
        d = ImageDraw.Draw(layer)
        for ex in (430, 650):
            f2 = easeOut(prog(ls, 0.3, 0.8)); y1 = 980 + 380 * f2
            if f2 > 0:
                d.line([ex, 990, ex, y1], fill=RED + (230,), width=9)
                d.polygon([(ex - 22, y1 - 10), (ex + 22, y1 - 10), (ex, y1 + 24)], fill=RED + (230,))
    if shot_i == 4:
        a = easeOut(prog(t, wT(1, 'tarde') - 0.15, wT(1, 'tarde') + 0.1))
        glow_text(layer, 'TARDE.', (W / 2, 520), 230, RED + (255,), path=FBI, glow=22, scale=1 + 0.5 * (1 - a), alpha=a, rot=6)
    if shot_i == 5:
        a = easeOut(prog(ls, 0.05, 0.3))
        glow_text(layer, 'MIRA', (W / 2, 330), 170, WHITE, glow=18, alpha=a, scale=1 + 0.3 * (1 - a))
        glow_text(layer, 'LEJOS', (W / 2, 500), 190, GRN + (255,), glow=18, alpha=easeOut(prog(ls, 0.2, 0.45)), scale=1 + 0.3 * (1 - easeOut(prog(ls, 0.2, 0.45))))
    if shot_i == 6:
        a = easeOut(prog(t, wT(2, 'frenar') - 0.35, wT(2, 'frenar')))
        reticle(layer, 330, 1440, GRN, t, 66, a); pill(layer, '1 · DÓNDE FRENAR', 380, 1300, GRN, (4, 33, 13), 46, a)
    if shot_i == 7:
        a = easeOut(prog(ls, 0.15, 0.45))
        reticle(layer, 290, 440, GRN, t, 62, a); pill(layer, '2 · EL VÉRTICE', 380, 300, GRN, (4, 33, 13), 46, a)
    if shot_i == 8:
        a = easeOut(prog(t, wT(3, 'salida') - 0.35, wT(3, 'salida')))
        f = easeOut(prog(ls, 0.2, 1.4))
        pts = [(560 + (820 - 560) * i / 24, 560 + (1060 - 560) * i / 24) for i in range(int(25 * f))]
        dashed(layer, pts, GRN, 0.9)
        reticle(layer, 820, 1070, GRN, t, 62, a); pill(layer, '3 · LA SALIDA', 760, 1220, GRN, (4, 33, 13), 46, a)
    if shot_i == 9:
        a = easeOut(prog(ls, 0.05, 0.3))
        glow_text(layer, 'TUS OJOS VAN', (W / 2, 300), 110, WHITE, glow=16, alpha=a)
        glow_text(layer, 'UN PASO', (W / 2, 440), 170, YEL + (255,), glow=18, alpha=easeOut(prog(ls, 0.25, 0.5)), scale=1 + 0.3 * (1 - easeOut(prog(ls, 0.25, 0.5))))
        glow_text(layer, 'ADELANTE', (W / 2, 610), 170, YEL + (255,), glow=18, alpha=easeOut(prog(ls, 0.45, 0.7)), scale=1 + 0.3 * (1 - easeOut(prog(ls, 0.45, 0.7))))
    if shot_i == 10:
        a = easeOut(prog(t, wT(5, 'mauro') - 0.25, wT(5, 'mauro') + 0.15))
        glow_text(layer, 'PILOTO', (W / 2, 1300), 50, YEL + (255,), path=FBOLD, glow=10, alpha=a)
        glow_text(layer, 'MAURO OSORTO', (W / 2, 1395), 112, WHITE, glow=18, alpha=a, scale=1 + 0.2 * (1 - a))
        b = easeOut(prog(t, wT(5, 'síguelo') - 0.25, wT(5, 'síguelo') + 0.2))
        if b > 0: pill(layer, 'SÍGUELO  →', W / 2, 1580, RED, (255, 255, 255), int(64 * (0.7 + 0.3 * back(b))), b)

# ---------- grade ----------
VIG = None
def grade(fr, t):
    global VIG
    if VIG is None:
        r = np.sqrt(((GX - W / 2) / (W * 0.62)) ** 2 + ((GY - H * 0.46) / (H * 0.62)) ** 2)
        VIG = np.clip(1 - 0.55 * np.clip(r - 0.45, 0, 1) ** 1.4, 0, 1)[..., None]
    fr = fr * VIG
    fr = 255 * ((fr / 255) ** 0.96)
    rng = np.random.default_rng(int(t * 1000)); n = rng.normal(0, 7, (H // 2, W // 2, 1)).astype(np.float32)
    fr = fr + cv2.resize(n, (W, H))[..., None]
    # top/bottom dark gradient for text legibility
    return np.clip(fr, 0, 255)
TOPG = None
def legibility(fr):
    global TOPG
    if TOPG is None:
        y = np.arange(H, dtype=np.float32)[:, None, None]
        TOPG = 1 - 0.55 * np.clip(1 - y / 760, 0, 1) ** 1.5 - 0.6 * np.clip((y - 1380) / 540, 0, 1) ** 1.3
    return fr * TOPG

def render(t):
    i = max(k for k, s in enumerate(SHOTS) if t >= s[0]); s0, s1, name, prm = SHOTS[i]
    u = prog(t, s0, s1); ls = t - s0
    fr = camera(name, ease(u) * 0.3 + u * 0.7, prm.get('z0', 1), prm.get('z1', 1.1), prm.get('px', 0), prm.get('py', 0), prm.get('k', 0.1),
                prm.get('cx', W / 2), prm.get('cy', H / 2), prm.get('shake', 0), t)
    if i == 4:  # freeze + desaturate on "tarde"
        a = prog(t, wT(1, 'tarde') - 0.15, wT(1, 'tarde') + 0.1)
        g = fr.mean(axis=2, keepdims=True); fr = fr * (1 - 0.85 * a) + g * 0.85 * a; fr[..., 0] += 25 * a
    if i == 10:
        y = np.arange(H, dtype=np.float32)[:, None, None]; fr = fr * (1 - 0.7 * np.clip((y - 1050) / 500, 0, 1))
    # cut: flash + directional blur on first frames
    if ls < 0.16 and i > 0:
        f = 1 - ls / 0.16; k = int(1 + 40 * f) | 1
        fr = cv2.blur(fr, (k, 1)); fr = fr + 255 * 0.55 * f ** 2
    fr = legibility(grade(fr, t))
    img = Image.fromarray(fr.astype(np.uint8)).convert('RGBA')
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    overlays(layer, t, i, ls)
    if 1 < i < 10: caption(layer, t)
    d = ImageDraw.Draw(layer); d.rectangle([0, H - 12, W, H], fill=(255, 255, 255, 50)); d.rectangle([0, H - 12, W * t / TOTAL, H], fill=YEL + (255,))
    img.alpha_composite(layer)
    return img.convert('RGB')

if __name__ == '__main__':
    import sys
    if sys.argv[1] == 'stills':
        for t in map(float, sys.argv[2:]): render(t).save(f'/tmp/sd/st_{t}.jpg', quality=88)
    else:
        N = int(TOTAL * FPS)
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                               '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '/tmp/sd/video.mp4'], stdin=subprocess.PIPE)
        for n in range(N):
            ff.stdin.write(np.asarray(render(n / FPS)).tobytes())
            if n % 150 == 0: print('frame', n, N, flush=True)
        ff.stdin.close(); ff.wait()
        json.dump(CUTS, open('/tmp/sd/cuts.json', 'w'))
