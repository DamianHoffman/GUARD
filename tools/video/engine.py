"""Tiny motion-graphics toolkit for the GUARD demo video (Skia, pure Python).

Style: a dark rounded card floating on a light dotted background, grids of small squares,
quiet typography. Strictly black / white / grey.
"""
import math
import re
from pathlib import Path

import numpy as np
import skia

W, H, FPS = 1600, 1200, 60
HERE = Path(__file__).resolve().parent
BRAND = HERE.parent.parent / "docs" / "assets" / "brand"

BG, DOTS = "#D9D9D6", "#C3C3BE"
CARD, CARD_LINE = "#0E0F12", "#1C1D21"
WHITE, TEXT, MUTED, FAINT = "#FFFFFF", "#F4F4F5", "#8B8C92", "#5A5B61"
CELL_EMPTY, CELL_DIM, CELL_OK = "#15161A", "#212226", "#55565C"
CX, CY, CW, CH = 160, 232, 1280, 736          # the card
L, R = CX + 56, CX + CW - 56                   # inner left / right
INK = "#0B0B0C"

# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def seg(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else (1.0 if t >= b else 0.0)


def lerp(a, b, x):
    return a + (b - a) * x


def out_cubic(x):
    return 1 - (1 - x) ** 3


def out_expo(x):
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def in_out(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def out_back(x, s=1.4):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def rgb(hexstr):
    h = hexstr.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(c1, c2, x):
    a, b = rgb(c1), rgb(c2)
    return "#%02x%02x%02x" % tuple(round(lerp(a[i], b[i], clamp(x))) for i in range(3))


def color(hexstr, a=1.0):
    r, g, b = rgb(hexstr)
    return skia.ColorSetARGB(round(clamp(a) * 255), r, g, b)


def paint(hexstr, a=1.0, stroke=None, dash=None):
    p = skia.Paint(AntiAlias=True, Color=color(hexstr, a))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if dash:
        p.setPathEffect(skia.DashPathEffect.Make(list(dash), 0))
    return p


_FONTS = {}
_FILES = {"reg": "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
          "med": "/usr/share/fonts/opentype/inter/Inter-Medium.otf",
          "semi": "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
          "mono": "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf",
          "monomed": "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf"}


def F(kind, size):
    key = (kind, size)
    if key not in _FONTS:
        f = skia.Font(skia.Typeface.MakeFromFile(_FILES[kind]), size)
        f.setSubpixel(True)
        _FONTS[key] = f
    return _FONTS[key]


def text(c, s, x, y, font, hexcolor=TEXT, a=1.0, align="l"):
    if a <= 0.003:
        return 0
    w = font.measureText(s)
    if align == "r":
        x -= w
    elif align == "c":
        x -= w / 2
    c.drawString(s, x, y, font, paint(hexcolor, a))
    return w


def rrect(c, x, y, w, h, r, fill=None, a=1.0, stroke=None, line=None, dash=None):
    rect = skia.Rect.MakeXYWH(x, y, w, h)
    if fill:
        c.drawRoundRect(rect, r, r, paint(fill, a))
    if stroke:
        c.drawRoundRect(rect, r, r, paint(line or WHITE, a, stroke=stroke, dash=dash))


def num(n):
    return f"{n:,}".replace(",", "\u202f")


# ---------------------------------------------------------------- background + card
def _make_bg():
    s = skia.Surface(W, H)
    c = s.getCanvas()
    c.clear(color(BG))
    step = 15
    for gy in range(0, H // step + 2):
        for gx in range(0, W // step + 2):
            x, y = gx * step + (step / 2 if gy % 2 else 0), gy * step
            d = math.hypot((x - W / 2) / (W * 0.58), (y - H / 2) / (H * 0.58))
            r = 0.55 + 1.35 * clamp(1 - d) ** 1.4
            c.drawCircle(x, y, r, paint(DOTS, 0.9))
    return s.makeImageSnapshot()


def _make_shadow():
    pad = 260
    s = skia.Surface(CW + 2 * pad, CH + 2 * pad)
    c = s.getCanvas()
    p = paint("#000000", 0.42)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 46))
    c.drawRoundRect(skia.Rect.MakeXYWH(pad, pad + 40, CW, CH), 40, 40, p)
    p2 = paint("#000000", 0.18)
    p2.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12))
    c.drawRoundRect(skia.Rect.MakeXYWH(pad, pad + 12, CW, CH), 40, 40, p2)
    return s.makeImageSnapshot(), pad


_BG = _SHADOW = None


def background(c):
    global _BG
    if _BG is None:
        _BG = _make_bg()
    c.drawImage(_BG, 0, 0)


def card(c, appear=1.0, dy=0.0, a=1.0):
    """The dark card. `appear` 0..1 scales it up slightly while fading in."""
    global _SHADOW
    if _SHADOW is None:
        _SHADOW = _make_shadow()
    if a <= 0.003:
        return
    img, pad = _SHADOW
    sc = lerp(0.955, 1.0, out_expo(appear))
    c.save()
    c.translate(CX + CW / 2, CY + CH / 2 + dy)
    c.scale(sc, sc)
    c.translate(-CW / 2, -CH / 2)
    c.drawImage(img, -pad, -pad, skia.SamplingOptions(), paint("#000000", a))
    rrect(c, 0, 0, CW, CH, 40, fill=CARD, a=a)
    rrect(c, 0.5, 0.5, CW - 1, CH - 1, 40, stroke=1, line="#FFFFFF", a=0.05 * a)
    c.restore()


def header(c, left, right, a, dy=0.0):
    text(c, left, L, CY + 82 + dy, F("semi", 27), TEXT, a)
    text(c, right, R, CY + 82 + dy, F("reg", 22), "#6F7076", a, "r")


# ---------------------------------------------------------------- shapes
def cell(c, x, y, s, state="empty", a=1.0, flash=0.0, grow=1.0):
    """Small square. states: empty, dim, ok, bad (hollow outline), hot (white)."""
    if grow < 1:
        x, y, s = x + s * (1 - grow) / 2, y + s * (1 - grow) / 2, s * grow
    if state == "empty":
        rrect(c, x, y, s, s, 4, fill=CELL_EMPTY, a=a)
    elif state == "dim":
        rrect(c, x, y, s, s, 4, fill=CELL_DIM, a=a)
    elif state == "ok":
        rrect(c, x, y, s, s, 4, fill=mix(CELL_OK, "#D6D6DA", flash), a=a)
    elif state == "hot":
        rrect(c, x, y, s, s, 4, fill=WHITE, a=a)
    elif state == "bad":
        rrect(c, x, y, s, s, 4, fill=CELL_EMPTY, a=a)
        rrect(c, x + 1.2, y + 1.2, s - 2.4, s - 2.4, 3.5, stroke=2.4, line=mix("#B8B8BC", WHITE, flash), a=a)


def tooltip(c, x, y, l1, l2, l3, a, w=330):
    if a <= 0.003:
        return
    h = 142
    sh = paint("#000000", 0.45 * a)
    sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y + 10, w, h), 16, 16, sh)
    rrect(c, x, y, w, h, 16, fill="#17181C", a=a)
    rrect(c, x + 0.5, y + 0.5, w - 1, h - 1, 16, stroke=1, line="#2E2F35", a=a)
    text(c, l1, x + 24, y + 38, F("mono", 17), MUTED, a)
    text(c, l2, x + 24, y + 82, F("semi", 31), WHITE, a)
    rrect(c, x + 24, y + 106, 12, 12, 2.5, fill="#6A6B71", a=a)
    text(c, l3, x + 46, y + 118, F("reg", 19), "#A5A6AB", a)


def dot_label(c, x, y, label, count, state, a):
    cell(c, x, y - 15, 15, state, a)
    w = text(c, label, x + 27, y, F("reg", 21), "#B4B5BA", a)
    if count is not None:
        text(c, str(count), x + 27 + w + 12, y, F("mono", 19), FAINT, a)
    return 27 + w + (40 if count is not None else 0) + 34


def kpis(c, items, t, t0, a, dy=0.0):
    """Row of 4 figures like the reference video. items: (target|str, fmt, label, sub, sub_state)."""
    cw = (R - L) / 4
    y0 = CY + CH - 156
    for i, (val, fmt, label, sub, st) in enumerate(items):
        x = L + i * cw
        ai = a * out_cubic(seg(t, t0 + i * 0.1, t0 + i * 0.1 + 0.5))
        if i:
            c.drawRect(skia.Rect.MakeXYWH(x - 28, y0 - 40, 1.2, 128), paint("#25262B", ai))
        if isinstance(val, str):
            v = val
        else:
            v = fmt(val * out_cubic(seg(t, t0 + i * 0.1 + 0.1, t0 + i * 0.1 + 1.6)))
        text(c, v, x, y0 + 2 + dy, F("med", 40), TEXT, ai)
        text(c, label, x, y0 + 38 + dy, F("reg", 21), "#76777D", ai)
        if sub:
            cell(c, x, y0 + 61 + dy, 12, st, ai)
            text(c, sub, x + 22, y0 + 74 + dy, F("reg", 19), "#A5A6AB", ai)


# ---------------------------------------------------------------- icons
def lock(c, cx, cy, s, hexcolor, a, closed=1.0):
    bw, bh = s * 0.86, s * 0.62
    x, y = cx - bw / 2, cy - bh / 2 + s * 0.16
    p = skia.Path()
    lift = (1 - closed) * s * 0.20
    r = s * 0.27
    p.moveTo(cx - r, y - lift)
    p.lineTo(cx - r, y - s * 0.12 - lift)
    p.arcTo(skia.Rect.MakeXYWH(cx - r, y - s * 0.12 - r * 1.1 - lift, 2 * r, 2 * r * 1.1), 180, 180, False)
    p.lineTo(cx + r, y - lift)
    c.drawPath(p, paint(hexcolor, a, stroke=max(2.0, s * 0.11)))
    rrect(c, x, y, bw, bh, s * 0.12, fill=hexcolor, a=a)


def check(c, cx, cy, s, hexcolor, a, p=1.0, stroke=4.0):
    path = skia.Path()
    path.moveTo(cx - s * 0.5, cy + s * 0.02)
    path.lineTo(cx - s * 0.12, cy + s * 0.4)
    path.lineTo(cx + s * 0.55, cy - s * 0.4)
    m = skia.PathMeasure(path, False)
    dst = skia.Path()
    m.getSegment(0, m.getLength() * clamp(p), dst, True)
    c.drawPath(dst, paint(hexcolor, a, stroke=stroke))


def file_icon(c, x, y, s, hexcolor, a):
    p = skia.Path()
    p.moveTo(x, y)
    p.lineTo(x + s * 0.62, y)
    p.lineTo(x + s, y + s * 0.38)
    p.lineTo(x + s, y + s * 1.2)
    p.lineTo(x, y + s * 1.2)
    p.close()
    c.drawPath(p, paint(hexcolor, a, stroke=2.2))
    c.drawLine(x + s * 0.62, y, x + s * 0.62, y + s * 0.38, paint(hexcolor, a, stroke=2.2))
    c.drawLine(x + s * 0.62, y + s * 0.38, x + s, y + s * 0.38, paint(hexcolor, a, stroke=2.2))


def arrow(c, x1, y, x2, hexcolor, a, p=1.0, stroke=3.0):
    xe = lerp(x1, x2, clamp(p))
    c.drawLine(x1, y, xe, y, paint(hexcolor, a, stroke=stroke))
    if p > 0.85:
        ah = clamp((p - 0.85) / 0.15)
        c.drawLine(xe - 12 * ah, y - 9 * ah, xe, y, paint(hexcolor, a, stroke=stroke))
        c.drawLine(xe - 12 * ah, y + 9 * ah, xe, y, paint(hexcolor, a, stroke=stroke))


# ---------------------------------------------------------------- logo
MARK = [[(133, 0), (0, 133), (0, 306), (133, 306)],
        [(0, 341), (137, 478), (527, 478), (527, 341)],
        [(167, 0), (527, 0), (527, 132), (167, 132)],
        [(527, 169), (406, 169), (268, 307), (527, 307)]]
_MARK_OFFSETS = [(-90, 0), (0, 90), (90, 0), (110, 40)]
_WORD = None


def _word_path():
    global _WORD
    if _WORD is None:
        svg = (BRAND / "guard-logo-white.svg").read_text()
        d = re.findall(r' d="([^"]+)"', svg)[-1]
        tokens = re.findall(r"[MmLlCczZ]|-?\d+(?:\.\d+)?", d)
        path, i, cmd, cx, cy = skia.Path(), 0, None, 0.0, 0.0
        while i < len(tokens):
            if tokens[i] in "MmLlCczZ":
                cmd = tokens[i]
                i += 1
                if cmd in "zZ":
                    path.close()
                    continue
            if cmd in "Mm":
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                cx, cy = (cx + x, cy + y) if cmd == "m" else (x, y)
                path.moveTo(cx, cy)
                cmd = "l" if cmd == "m" else "L"
            elif cmd in "Ll":
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                cx, cy = (cx + x, cy + y) if cmd == "l" else (x, y)
                path.lineTo(cx, cy)
            elif cmd in "Cc":
                v = [float(t) for t in tokens[i:i + 6]]
                i += 6
                if cmd == "c":
                    v = [v[0] + cx, v[1] + cy, v[2] + cx, v[3] + cy, v[4] + cx, v[5] + cy]
                path.cubicTo(*v)
                cx, cy = v[4], v[5]
        _WORD = path
    return _WORD


def lockup(c, x, y, scale, hexcolor, a=1.0, build=1.0, word=1.0):
    """GUARD mark + wordmark. (x, y) = top-left of the 500x120 lock-up box. build: mark assembly 0..1, word: reveal 0..1."""
    c.save()
    c.translate(x, y)
    c.scale(scale, scale)
    c.translate(-253, -325)
    c.save()
    c.translate(253, 325)
    c.scale(0.25, 0.25)
    for i, pts in enumerate(MARK):
        b = out_expo(seg(build, i * 0.12, i * 0.12 + 0.62))
        ox, oy = _MARK_OFFSETS[i]
        p = skia.Path()
        p.moveTo(pts[0][0] + ox * (1 - b), pts[0][1] + oy * (1 - b))
        for px, py in pts[1:]:
            p.lineTo(px + ox * (1 - b), py + oy * (1 - b))
        p.close()
        c.drawPath(p, paint(hexcolor, a * clamp(b * 1.6)))
    c.restore()
    if word > 0:
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(405, 320, 360 * out_expo(word) + 8, 130))
        c.translate(416 + 22 * (1 - out_expo(word)), 338)
        c.scale(1 / 12, 1 / 12)
        c.translate(0, 1080)
        c.scale(0.1, -0.1)
        c.drawPath(_word_path(), paint(hexcolor, a * clamp(word * 3)))
        c.restore()
    c.restore()


def mark_only(c, x, y, scale, hexcolor, a=1.0):
    c.save()
    c.translate(x, y)
    c.scale(scale, scale)
    for pts in MARK:
        p = skia.Path()
        p.moveTo(*pts[0])
        for q in pts[1:]:
            p.lineTo(*q)
        p.close()
        c.drawPath(p, paint(hexcolor, a))
    c.restore()


# ---------------------------------------------------------------- output
def new_surface():
    s = skia.Surface(W, H)
    return s, s.getCanvas()


def frame_bytes(surface):
    return np.array(surface.makeImageSnapshot().toarray(), dtype=np.uint8).tobytes()


def save_png(surface, path, size=None):
    img = surface.makeImageSnapshot()
    if size:
        img = img.resize(*size)
    img.save(str(path), skia.kPNG)
