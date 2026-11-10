"""v2: voice-over + synced captions + animated explainer inserts.

usage: python3 -I render2.py OUT.mp4 [--preview u1,u2,...]
"""
import os, sys, json, math, subprocess
import numpy as np, cv2, soundfile as sf, scipy.signal as ss
S = "/tmp/claude-0/-home-user-rac-privacy/75c0bf54-1720-5939-92f1-61063ac8fdf1/scratchpad"
os.environ["FX_SRC"] = f"{S}/in/raw.mp4"
sys.path.insert(0, S)
import fx
from fx import (W, H, Image, ImageDraw, ImageFilter, font, text_sprite, paste, glass, with_alpha,
                clamp, prog, ease_out_cubic, ease_in_out, ease_out_back, ease_out_expo, lerp, window,
                ORANGE, WHITE, F_BLACK, F_XB, F_SB)

OUT = sys.argv[1]
PREVIEW = [float(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 and sys.argv[2] == "--preview" else None
OFPS = 30
LEAD, TAIL = 0.25, 0.35
SR = 48000

SCRIPT = json.load(open(f"{S}/script.json"))
TIM = json.load(open(f"{S}/vo/timing.json"))

# ---------------------------------------------------------------- timeline
SEGS = []
u = 0.0
for sc in SCRIPT:
    vd = TIM[sc["id"]]["dur"]
    seg = dict(sc)
    if sc["type"] == "foot":
        sd = sc["src"][1] - sc["src"][0]
        od = max(sd, LEAD + vd + TAIL)
        seg["rate"] = sd / od
    else:
        od = LEAD + vd + 0.6
    seg["start"], seg["dur"], seg["vo_start"] = u, od, u + LEAD
    seg["words"] = [dict(w, s=w["s"] + u + LEAD, e=w["e"] + u + LEAD) for w in TIM[sc["id"]]["words"]]
    SEGS.append(seg)
    u += od
TOTAL = u
SEG = {s["id"]: s for s in SEGS}
BOUNDS = [s["start"] for s in SEGS[1:]]
print("total", round(TOTAL, 2), [(s["id"], round(s["start"], 2), round(s["dur"], 2), round(s.get("rate", 1), 2)) for s in SEGS], flush=True)

def word_time(seg_id, word):
    for w in SEG[seg_id]["words"]:
        if fx_norm(w["w"]) == word: return w["s"]
    raise KeyError(word)
def fx_norm(w): return "".join(c for c in w.lower() if c.isalnum())
def out_to_src(seg, uo): return seg["src"][0] + (uo - seg["start"]) * seg["rate"]

# footage event times (in source time), derived from the voice
RING_SRC = out_to_src(SEG["A"], word_time("A", "punto")) - 0.1
LABEL_SRC = out_to_src(SEG["B"], word_time("B", "martillo")) - 0.15
BLOWS_SRC = out_to_src(SEG["B"], word_time("B", "miles")) - 0.2
END_SRC = out_to_src(SEG["D"], word_time("D", "prevenir")) - 0.05
END2_SRC = out_to_src(SEG["D"], word_time("D", "ahorrar")) - 0.05
CAP_HIDE_FROM = word_time("D", "prevenir") - 0.05

# ---------------------------------------------------------------- captions (voice-synced)
CAP_SIZE, CAP_MAXW, CAP_CX, CAP_Y = 64, 820, 515, 1470

def pages_for(seg):
    pages, cur = [], []
    for w in seg["words"]:
        cur.append(w)
        txt = " ".join(x["w"].replace("*", "") for x in cur)
        if len(txt) >= 24 or w["w"].rstrip("*")[-1:] in ",.:":
            pages.append(cur); cur = []
    if cur: pages.append(cur)
    out = []
    for i, p in enumerate(pages):
        a = p[0]["s"] - 0.06
        b = pages[i + 1][0]["s"] - 0.06 if i + 1 < len(pages) else p[-1]["e"] + 0.45
        out.append((a, b, p))
    return out

PAGES = [pg for s in SEGS for pg in pages_for(s)]

def layout(words):
    f = font(F_XB, CAP_SIZE)
    space = f.getlength(" ") * 1.35 + 4
    items = []
    for w in words:
        raw = w["w"]; kw = "*" in raw
        items.append((raw.replace("*", ""), kw, f.getlength(raw.replace("*", "")), w))
    lines, cur, cw = [], [], 0
    for it in items:
        if cur and cw + space + it[2] > CAP_MAXW:
            lines.append((cur, cw)); cur, cw = [], 0
        cw = cw + (space if cur else 0) + it[2]; cur.append(it)
    lines.append((cur, cw))
    out = []
    for li, (ws, lw) in enumerate(lines):
        x = CAP_CX - lw / 2
        for txt, kw, ww, w in ws:
            out.append((txt, kw, x + ww / 2, CAP_Y + li * CAP_SIZE * 1.2, ww, w))
            x += ww + space
    return out

PAGE_LAYOUT = [(a, b, layout(p)) for a, b, p in PAGES]

def draw_captions(cv, uo):
    if uo >= CAP_HIDE_FROM: return
    d = ImageDraw.Draw(cv)
    for a, b, items in PAGE_LAYOUT:
        if not (a <= uo < b): continue
        env = min(prog(uo, a, a + 0.08), 1 - prog(uo, b - 0.08, b)) if b - a > 0.2 else 1
        for idx, (txt, kw, cx, cy, ww, w) in enumerate(items):
            if uo < w["s"] - 0.04: continue
            nxt = items[idx + 1][5]["s"] - 0.04 if idx + 1 < len(items) else w["e"] + 0.15
            p = prog(uo, w["s"] - 0.04, w["s"] + 0.14)
            sc = 0.6 + 0.4 * (ease_out_back(p, 2.2) if p < 1 else 1)
            active = w["s"] - 0.04 <= uo < nxt
            if active:
                pw = ww * sc / 2 + 16
                d.rounded_rectangle((cx - pw, cy - CAP_SIZE * 0.62, cx + pw, cy + CAP_SIZE * 0.55), 16,
                                    fill=with_alpha(ORANGE, env))
                spr = text_sprite(txt, F_XB, CAP_SIZE, fill=WHITE, stroke=0, shadow=False)
                paste(cv, spr, cx, cy, alpha=env, scale=sc * 1.04, anchor="cm")
            else:
                spr = text_sprite(txt, F_XB, CAP_SIZE, fill=ORANGE if kw else WHITE, stroke=6, stroke_fill=(0, 0, 0, 255))
                paste(cv, spr, cx, cy, alpha=env * clamp(p * 2.5), scale=sc, anchor="cm")

# ---------------------------------------------------------------- footage
def draw_end2(cv, t):
    if t < END_SRC: return
    p1 = prog(t, END_SRC, END_SRC + 0.45); p2 = prog(t, END2_SRC, END2_SRC + 0.45)
    e1, e2 = ease_out_expo(p1), ease_out_expo(p2)
    paste(cv, text_sprite("PREVENIR", F_BLACK, 150, fill=WHITE), W / 2, 820, alpha=clamp(p1 * 2),
          scale=lerp(1.25, 1.0, e1), anchor="cm", blur=(1 - e1) * 10)
    if p2 > 0:
        paste(cv, text_sprite("ES AHORRAR", F_BLACK, 150, fill=ORANGE), W / 2, 985, alpha=clamp(p2 * 2),
              scale=lerp(1.25, 1.0, e2), anchor="cm", blur=(1 - e2) * 10)
    sp = ease_out_cubic(prog(t, END2_SRC + 0.4, END2_SRC + 0.9))
    if sp > 0:
        s = text_sprite("Mantenimiento a tiempo = menos reparaciones", F_SB, 34, fill=(255, 255, 255, 230))
        paste(cv, s, W / 2, 1110 + (1 - sp) * 20, alpha=sp, anchor="cm")

def render_foot(seg, uo):
    t = out_to_src(seg, uo)
    i = min(int(round(t * fx.FPS)), fx.N - 1)
    f = fx.frames[i]; sp = fx.spot(i)
    world = fx.grade(f)
    bl = fx.draw_behind(t)
    if bl is not None:
        m = fx.fg_mask(f)
        arr = np.asarray(bl).astype(np.float32) / 255
        a = arr[..., 3:4] * (1 - m[..., None])
        world = world * (1 - a) + arr[..., :3] * a
    wo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sid = seg["id"]
    if sid == "A": fx.draw_ring(wo, t - RING_SRC + 3.2, sp)
    if sid == "B":
        fx.draw_tool_label(wo, t - LABEL_SRC + 6.6, sp)
        fx.draw_impacts(wo, t - BLOWS_SRC + 10.2, sp)
    fx.draw_sin(wo, t)
    arr = np.asarray(wo).astype(np.float32) / 255
    world = world * (1 - arr[..., 3:4]) + arr[..., :3] * arr[..., 3:4]
    z, x0, y0 = fx.camera(t, sp)
    scr = fx.apply_cam(world, z, x0, y0) * fx.VIG
    dk = 0.45 * ease_in_out(prog(t, END_SRC - 0.15, END_SRC + 0.4))
    if dk: scr = scr * (1 - dk)
    if 13.6 <= t: scr = scr + (1 - scr) * 0.30 * (1 - prog(t, 13.6, 13.95))
    so = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if sid == "A": fx.draw_hook(so, t)
    if sid == "B": fx.draw_blows_card(so, t - BLOWS_SRC + 10.35)
    if sid == "C": fx.draw_progress(so, t)
    if sid == "D": draw_end2(so, t)
    arr = np.asarray(so).astype(np.float32) / 255
    return scr * (1 - arr[..., 3:4]) + arr[..., :3] * arr[..., 3:4]

# ---------------------------------------------------------------- motion-graphics backgrounds
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
BG = np.dstack([lerp(11, 17, yy / H), lerp(18, 28, yy / H), lerp(32, 46, yy / H)]) / 255
dots = ((xx % 54 < 3) & (yy % 54 < 3)).astype(np.float32)[..., None] * 0.05
BG = np.clip(BG + dots, 0, 1).astype(np.float32)
NAVY = (13, 20, 34)

def mg_base(ul):
    # slow drifting glow
    cx = W * (0.3 + 0.15 * math.sin(ul * 0.6)); cy = H * 0.45
    g = np.exp(-(((xx - cx) / 520) ** 2 + ((yy - cy) / 700) ** 2))[..., None]
    img = BG + g * np.array([0.10, 0.06, 0.02], np.float32)
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

def mg_title(cv, ul, kicker, lines):
    kp = ease_out_cubic(prog(ul, 0.0, 0.4))
    paste(cv, text_sprite(kicker, F_XB, 30, fill=ORANGE, tracking=5, shadow=False), 90 - (1 - kp) * 40, 300, alpha=kp)
    d = ImageDraw.Draw(cv)
    d.rectangle((90, 348, 90 + 90 * kp, 354), fill=with_alpha(ORANGE, kp))
    y = 375
    for i, (txt, col, size) in enumerate(lines):
        p = ease_out_expo(prog(ul, 0.1 + i * 0.12, 0.7 + i * 0.12))
        paste(cv, text_sprite(txt, F_BLACK, size, fill=col, shadow=True), 86, y + (1 - p) * 60, alpha=clamp(p * 1.5))
        y += size * 1.0

def pill(cv, x, y, txt, alpha, fill=ORANGE, size=30, anchor="lm", tcol=WHITE):
    if alpha <= 0: return
    spr = text_sprite(txt, F_XB, size, fill=tcol, tracking=2, shadow=False)
    bw = spr[0].width - 2 * spr[1]
    w = bw + 48; h = size + 34
    x0 = x - (w / 2 if anchor[0] == "c" else 0)
    glass(cv, (x0, y - h / 2, x0 + w, y + h / 2), r=h / 2, alpha=alpha, fill=fill[:3] + (235,), border=(255, 255, 255, 80))
    paste(cv, spr, x0 + 24, y, alpha=alpha, anchor="lm")

def wl(seg, word):  # local time of a word inside an MG segment
    return word_time(seg["id"], word) - seg["start"]

RNG = np.random.default_rng(7)
NOISE = RNG.uniform(-1, 1, 400)

def mg_corrosion(seg, ul):
    cv = mg_base(ul)
    mg_title(cv, ul, "¿POR QUÉ APARECE?", [("LA", WHITE, 120), ("CORROSIÓN", ORANGE, 120)])
    d = ImageDraw.Draw(cv)
    X0, X1, CX = 110, 770, 360
    ta, to, tc = wl(seg, "agua"), wl(seg, "oxígeno"), wl(seg, "corrosión")
    # rust extent
    rp = ease_in_out(prog(ul, tc - 0.25, tc + 1.4))
    wr = 270 * rp
    def bulge(x):
        if wr < 1: return 0.0
        q = 1 - ((x - CX) / wr) ** 2
        return max(q, 0) * 20 * rp
    xs = np.arange(X0, X1 + 1, 6)
    ent = [ease_out_cubic(prog(ul, 0.25 + k * 0.12, 0.75 + k * 0.12)) for k in range(3)]
    # steel
    if ent[0] > 0:
        oy = (1 - ent[0]) * 80
        top = 1005 + oy
        for k in range(0, 225, 3):
            c = int(lerp(112, 58, k / 225))
            d.rectangle((X0, top + k, X1, top + k + 3), fill=(c, c + 6, c + 14, int(255 * ent[0])))
        d.rectangle((X0, top, X1, top + 4), fill=(175, 182, 192, int(255 * ent[0])))
    # rust under coating
    if wr > 1:
        pts = []
        for x in xs:
            if abs(x - CX) <= wr:
                q = 1 - ((x - CX) / wr) ** 2
                dep = 42 * q * rp + 4 * NOISE[int(x) % 400]
                pts.append((x, 1005 + max(dep, 2)))
        if len(pts) > 2:
            poly = [(CX - wr, 1003)] + pts + [(CX + wr, 1003)]
            d.polygon(poly, fill=(178, 84, 30, 255))
            for j in range(40):
                rx = CX + (NOISE[j * 7 % 400]) * wr * 0.9; ry = 1012 + abs(NOISE[j * 3 % 400]) * 26 * rp
                d.ellipse((rx - 4, ry - 3, rx + 4, ry + 3), fill=(120, 50, 18, 255))
    # primer + paint with blister
    for k, (y0, y1, col, nm) in enumerate([(975, 1005, (154, 160, 168), "PRIMER"), (930, 975, (34, 165, 146), "PINTURA")]):
        e = ent[1 + k]
        if e <= 0: continue
        oy = (1 - e) * 80
        topl = [(x, y0 + oy - bulge(x)) for x in xs]
        botl = [(x, y1 + oy - bulge(x) * (0.6 if k == 0 else 1)) for x in xs[::-1]]
        d.polygon(topl + botl, fill=col + (int(255 * e),))
    # crack
    cp = ease_out_cubic(prog(ul, ta - 0.55, ta - 0.1))
    if cp > 0:
        w2 = 26 * cp
        d.polygon([(CX - w2, 925 - bulge(CX - w2)), (CX + w2, 925 - bulge(CX + w2)), (CX + 4 * cp, 1006), (CX - 4 * cp, 1006)], fill=NAVY + (255,))
    # side labels
    for k, (nm, yv) in enumerate([("PINTURA", 952), ("PRIMER", 990), ("ACERO", 1110)]):
        lp = ease_out_cubic(prog(ul, 0.7 + k * 0.1, 1.0 + k * 0.1))
        if lp <= 0: continue
        d.line((X1 + 10, yv, X1 + 10 + 40 * lp, yv), fill=(255, 255, 255, int(150 * lp)), width=3)
        paste(cv, text_sprite(nm, F_XB, 30, fill=(255, 255, 255, 230), tracking=2, shadow=False), X1 + 62, yv, alpha=lp, anchor="lm")
    # water drops
    for j in range(3):
        t0 = ta - 0.15 + j * 0.16
        p = prog(ul, t0, t0 + 0.5)
        if 0 < p < 1:
            y = lerp(640, 930, p ** 2); x = CX + (j - 1) * 6
            r = 16 * (1 - 0.5 * prog(p, 0.85, 1))
            d.ellipse((x - r, y - r, x + r, y + r), fill=(79, 168, 255, 255))
            d.polygon([(x - r * 0.75, y - r * 0.5), (x + r * 0.75, y - r * 0.5), (x, y - r * 2.1)], fill=(79, 168, 255, 255))
    pill(cv, CX + 70, 720, "H₂O", window(ul, ta - 0.1, tc + 0.4, 0.2, 0.3), fill=(40, 120, 220, 255))
    # oxygen bubbles
    for j in range(5):
        t0 = to - 0.2 + j * 0.12
        p = prog(ul, t0, t0 + 0.9)
        if 0 < p < 1:
            y = lerp(660, 920, ease_in_out(p)); x = CX - 150 + j * 40 + 30 * math.sin(p * 6 + j) - 120 * ease_in_out(p) * ((j - 2) / 3)
            x = lerp(x, CX, ease_in_out(p) ** 2)
            al = int(255 * (1 - prog(p, 0.85, 1)))
            d.ellipse((x - 22, y - 22, x + 22, y + 22), outline=(200, 230, 255, al), width=3)
            paste(cv, text_sprite("O₂", F_XB, 20, fill=(200, 230, 255, 255), shadow=False), x, y, alpha=al / 255, anchor="cm")
    pill(cv, CX - 250, 720, "O₂", window(ul, to - 0.1, tc + 0.4, 0.2, 0.3), fill=(90, 110, 140, 255))
    # spread arrows + label
    if rp > 0.05:
        al = int(255 * min(1, rp * 3))
        for sgn in (-1, 1):
            ax = CX + sgn * (wr + 26); ay = 1030
            d.polygon([(ax, ay - 16), (ax + sgn * 22, ay), (ax, ay + 16)], fill=(255, 122, 26, al))
        lp = ease_out_back(prog(ul, tc + 0.1, tc + 0.5))
        if lp > 0:
            d.line((CX, 1060, CX, lerp(1060, 1255, clamp(lp))), fill=(255, 255, 255, 200), width=3)
            pill(cv, CX, 1290, "CORROSIÓN BAJO LA PINTURA", clamp(lp), anchor="cm")
    return cv

def mg_scaler(seg, ul):
    cv = mg_base(ul)
    mg_title(cv, ul, "CÓMO FUNCIONA", [("MARTILLO", WHITE, 100), ("DE AGUJAS", ORANGE, 100)])
    top = cv
    cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    dur = seg["dur"]
    tx = lerp(250, 830, ease_in_out(prog(ul, 0.3, dur - 0.2)))
    front = tx - 30
    # steel + rust
    for k in range(0, 160, 3):
        c = int(lerp(120, 60, k / 160))
        d.rectangle((90, 1185 + k, 990, 1188 + k), fill=(c, c + 6, c + 14, 255))
    d.rectangle((90, 1183, 990, 1187), fill=(180, 186, 196, 255))
    pts = [(x, 1150 + 8 * NOISE[x % 400]) for x in range(int(max(front, 90)), 991, 8)]
    if len(pts) > 1:
        d.polygon([(pts[0][0], 1185)] + pts + [(990, 1185)], fill=(168, 80, 30, 255))
        for j in range(60):
            rx = 100 + (j * 47) % 880
            if rx > front:
                ry = 1160 + (j * 13) % 22
                d.ellipse((rx - 5, ry - 3, rx + 5, ry + 3), fill=(110, 48, 18, 255))
    # flakes
    for j in range(int(ul / 0.025)):
        ts = j * 0.025
        age = ul - ts
        if age > 0.75 or ts < 0.3: continue
        x0 = lerp(250, 830, ease_in_out(prog(ts, 0.3, dur - 0.2))) + 45 * NOISE[j % 400]
        vx = 320 * NOISE[(j * 3) % 400]; vy = -380 - 320 * abs(NOISE[(j * 5) % 400])
        x = x0 + vx * age; y = 1160 + vy * age + 0.5 * 2000 * age ** 2
        if y > 1180: continue
        s = 5 + 4 * abs(NOISE[(j * 11) % 400]); a = age * 12 + j
        poly = [(x + s * math.cos(a + q * 2.1), y + s * math.sin(a + q * 2.1)) for q in range(3)]
        d.polygon(poly, fill=(190, 95, 35, int(255 * (1 - age / 0.75))))
    # tool
    bob = 16 * abs(math.sin(ul * 2 * math.pi * 9))
    ent = ease_out_cubic(prog(ul, 0.15, 0.6)); oy = (1 - ent) * -300
    for n in range(9):
        nx = tx - 48 + n * 12
        d.line((nx, 990 + bob + oy, nx, 1148 + bob + oy - (n % 2) * 4), fill=(60, 64, 70, 255), width=7)
    d.rounded_rectangle((tx - 62, 975 + bob + oy, tx + 62, 1000 + bob + oy), 6, fill=(70, 74, 82, 255))
    d.rounded_rectangle((tx - 78, 700 + bob + oy, tx + 78, 985 + bob + oy), 18, fill=(150, 156, 166, 255))
    d.rounded_rectangle((tx - 78, 790 + bob + oy, tx + 78, 820 + bob + oy), 4, fill=(255, 122, 26, 255))
    d.rounded_rectangle((tx + 70, 740 + bob + oy, tx + 175, 790 + bob + oy), 12, fill=(55, 60, 68, 255))
    d.rounded_rectangle((tx + 125, 770 + bob + oy, tx + 180, 945 + bob + oy), 18, fill=(55, 60, 68, 255))
    hose = [(tx + 152 + 120 * q ** 1.5 * 2.2, 945 + oy + bob * (1 - q) + 160 * math.sin(q * 2.4)) for q in np.linspace(0, 1, 24)]
    d.line(hose, fill=(30, 32, 36, 255), width=16, joint="curve")
    # sparks
    if bob < 4:
        for n in range(4):
            sx = tx - 40 + n * 27
            d.line((sx, 1150, sx + 12 * NOISE[(n + int(ul * 30)) % 400], 1128), fill=(255, 220, 160, 230), width=3)
    # chips
    top.alpha_composite(cv, (0, 70)); cv = top
    t1, t2 = wl(seg, "óxido"), wl(seg, "químicos")
    pill(cv, 90, 660, "IMPACTO MECÁNICO", clamp(prog(ul, t1 - 0.15, t1 + 0.1)))
    pill(cv, 520, 660, "SIN QUÍMICOS", clamp(prog(ul, t2 - 0.2, t2 + 0.05)), fill=(34, 165, 146, 255))
    return cv

def mg_process(seg, ul):
    cv = mg_base(ul)
    mg_title(cv, ul, "PASO A PASO", [("EL PROCESO", WHITE, 120)])
    d = ImageDraw.Draw(cv)
    steps = [("Remover óxido", "Martillo de agujas"), ("Limpiar la superficie", "Sin polvo, grasa ni humedad"),
             ("Primer anticorrosivo", "Protege el acero"), ("Pintura final", "Acabado y protección")]
    act = [0.35, wl(seg, "limpia") - 0.1, wl(seg, "primer") - 0.1, wl(seg, "pintura") - 0.1]
    done_t = act[1:] + [seg["dur"] - 0.35]
    YS = [640, 850, 1060, 1270]; CXc = 170
    # rail
    d.line((CXc, YS[0], CXc, YS[-1]), fill=(255, 255, 255, 50), width=6)
    cur = max([k for k in range(4) if ul >= act[k]], default=-1)
    if cur >= 0:
        ky = YS[cur] if cur == 0 else lerp(YS[cur - 1], YS[cur], ease_in_out(prog(ul, act[cur], act[cur] + 0.35)))
        d.line((CXc, YS[0], CXc, ky), fill=ORANGE, width=6)
        # highlight card
        hy = ky
        glass(cv, (110, hy - 82, 975, hy + 82), r=30, alpha=ease_out_cubic(prog(ul, act[0], act[0] + 0.3)),
              fill=(255, 255, 255, 22), border=(255, 122, 26, 160))
        d = ImageDraw.Draw(cv)
    for k, (t1, t2) in enumerate(steps):
        y = YS[k]
        ent = ease_out_cubic(prog(ul, 0.2 + k * 0.1, 0.6 + k * 0.1))
        if ent <= 0: continue
        on = ul >= act[k]; done = ul >= done_t[k]
        pp = ease_out_back(prog(ul, act[k], act[k] + 0.3)) if on else 0
        r = 44 * (1 + 0.15 * pp * (1 - prog(ul, act[k] + 0.3, act[k] + 0.6)))
        if on:
            d.ellipse((CXc - r, y - r, CXc + r, y + r), fill=(255, 122, 26, int(255 * ent)))
        else:
            d.ellipse((CXc - r, y - r, CXc + r, y + r), fill=NAVY + (255,), outline=(255, 255, 255, int(120 * ent)), width=4)
        if done:
            cp = prog(ul, done_t[k], done_t[k] + 0.25)
            pts = [(CXc - 18, y + 1), (CXc - 5, y + 15), (CXc + 20, y - 14)]
            q = clamp(cp * 2); q2 = clamp(cp * 2 - 1)
            path = [pts[0], (lerp(pts[0][0], pts[1][0], q), lerp(pts[0][1], pts[1][1], q))]
            if q2 > 0: path.append((lerp(pts[1][0], pts[2][0], q2), lerp(pts[1][1], pts[2][1], q2)))
            d.line(path, fill=WHITE, width=7, joint="curve")
        else:
            paste(cv, text_sprite(str(k + 1), F_BLACK, 40, shadow=False), CXc, y, alpha=ent, anchor="cm")
        a1 = ent * (1 if on else 0.45)
        paste(cv, text_sprite(t1, F_XB, 50, fill=WHITE, shadow=False), 250 + (1 - ent) * 40, y - 22, alpha=a1, anchor="lm")
        paste(cv, text_sprite(t2, F_SB, 30, fill=(205, 212, 222, 255), shadow=False), 250 + (1 - ent) * 40, y + 30, alpha=a1 * 0.9, anchor="lm")
    return cv

MG = {"corrosion": mg_corrosion, "scaler": mg_scaler, "process": mg_process}

def render_mg(seg, uo):
    ul = uo - seg["start"]
    cv = MG[seg["scene"]](seg, ul)
    return np.asarray(cv.convert("RGB")).astype(np.float32) / 255

# ---------------------------------------------------------------- frame assembly
def base_frame(uo):
    seg = next(s for s in SEGS[::-1] if uo >= s["start"])
    img = render_foot(seg, uo) if seg["type"] == "foot" else render_mg(seg, uo)
    return img

WT = 0.18
def whip(img, p, direction):
    """p 0..1 strength. direction -1 = moving out to left, +1 = coming in from right"""
    shift = int(W * 0.55 * p) * (-1 if direction < 0 else 1)
    img = np.roll(img, shift, axis=1)
    k = int(1 + 140 * p)
    if k > 1: img = cv2.blur(img, (k, 1))
    return img

def frame(uo):
    img = base_frame(uo)
    for b in BOUNDS:
        if b - WT <= uo < b:
            img = whip(img, (prog(uo, b - WT, b)) ** 2, -1)
        elif b <= uo < b + WT:
            img = whip(img, (1 - prog(uo, b, b + WT)) ** 2, +1)
    so = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_captions(so, uo)
    arr = np.asarray(so).astype(np.float32) / 255
    img = img * (1 - arr[..., 3:4]) + arr[..., :3] * arr[..., 3:4]
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)

# ---------------------------------------------------------------- audio
def build_audio(path):
    orig = subprocess.run(["ffmpeg", "-v", "error", "-i", fx.SRC, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                          capture_output=True, check=True).stdout
    orig = np.frombuffer(orig, np.float32)
    n = int(round(TOTAL * SR))
    bg = np.zeros(n, np.float32)
    def take(start_s, length, gain):
        i0 = int(start_s * SR); seg = np.resize(np.roll(orig, -i0), length) * gain
        f = min(int(0.04 * SR), length // 2)
        seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        return seg
    for s in SEGS:
        i0 = int(s["start"] * SR); L = min(int(s["dur"] * SR), n - i0)
        if s["type"] == "foot": bg[i0:i0 + L] += take(s["src"][0], L, 1.0)
        else: bg[i0:i0 + L] += take(5.0, L, 0.55)
    bg *= 0.07 / (np.sqrt(np.mean(bg ** 2)) + 1e-9)
    vo = np.zeros(n, np.float32)
    for s in SEGS:
        v, _ = sf.read(f"{S}/vo/{s['id']}.wav", dtype="float32")
        i0 = int(s["vo_start"] * SR); L = min(len(v), n - i0)
        vo[i0:i0 + L] += v[:L]
    env = (np.abs(vo) > 0.02).astype(np.float32)
    k = int(0.25 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    env = np.clip(env * 3, 0, 1)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    duck = 1.0 - 0.62 * env
    # whooshes
    sos = ss.butter(2, [400, 5000], btype="band", fs=SR, output="sos")
    wh = np.zeros(n, np.float32)
    rng = np.random.default_rng(3)
    for b in BOUNDS:
        L = int(0.5 * SR); i0 = int((b - 0.3) * SR)
        noise = ss.sosfilt(sos, rng.standard_normal(L)).astype(np.float32)
        e = np.sin(np.linspace(0, np.pi, L)) ** 3
        seg = noise * e; seg *= 0.10 / (np.abs(seg).max() + 1e-9)
        wh[i0:i0 + L] += seg[: max(0, min(L, n - i0))]
    mix = bg * duck + vo * 0.95 + wh
    fo = int(0.6 * SR); mix[-fo:] *= np.linspace(1, 0, fo)
    sf.write(path, np.clip(mix, -1, 1), SR)

if PREVIEW:
    for uo in PREVIEW:
        Image.fromarray(frame(uo)).save(f"{OUT}_{uo:05.2f}.jpg", quality=88)
    sys.exit()

wav = OUT + ".mix.wav"
build_audio(wav)
NF = int(round(TOTAL * OFPS))
enc = subprocess.Popen([
    "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(OFPS), "-i", "-",
    "-i", wav, "-map", "0:v", "-map", "1:a",
    "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
for j in range(NF):
    enc.stdin.write(frame(j / OFPS).tobytes())
    if j % 90 == 0: print("frame", j, "/", NF, flush=True)
enc.stdin.close(); enc.wait()
print("done", OUT)
