#!/usr/bin/env python3
"""Static GUARD images for the README (same visual language as the film). Output: docs/images/*.png

  python tools/video/stills.py            # all infographics
"""
import json
import math
import sys
from pathlib import Path

import skia

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import (BG, CARD, DOTS, F, HERE, INK, MUTED, TEXT, WHITE, arrow, cell, check, clamp, color,  # noqa: E402
                    file_icon, lock, lockup, mark_only, mix, num, paint, rrect, text)

ROOT = HERE.parent.parent
OUT = ROOT / "docs" / "images"
N = json.loads((HERE / "numbers.json").read_text())
GREY2, LINE = "#8B8C92", "#26272C"


# ------------------------------------------------------------------ canvas helpers
def canvas(w, h, dark=False):
    s = skia.Surface(w, h)
    c = s.getCanvas()
    if dark:
        c.clear(color("#0B0B0C"))
        base, dotc, k = "#0B0B0C", "#1A1B1F", 0.75
    else:
        c.clear(color(BG))
        base, dotc, k = BG, DOTS, 1.0
    step = 15
    for gy in range(0, h // step + 2):
        for gx in range(0, w // step + 2):
            x, y = gx * step + (step / 2 if gy % 2 else 0), gy * step
            d = math.hypot((x - w / 2) / (w * 0.6), (y - h / 2) / (h * 0.6))
            c.drawCircle(x, y, (0.5 + 1.3 * clamp(1 - d) ** 1.4) * k, paint(dotc, 0.9))
    return s, c


def panel(c, x, y, w, h, r=36, fill=CARD, line="#FFFFFF", shadow=True):
    if shadow:
        sh = paint("#000000", 0.38)
        sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 34))
        c.drawRoundRect(skia.Rect.MakeXYWH(x, y + 30, w, h), r, r, sh)
        sh2 = paint("#000000", 0.16)
        sh2.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 9))
        c.drawRoundRect(skia.Rect.MakeXYWH(x, y + 10, w, h), r, r, sh2)
    rrect(c, x, y, w, h, r, fill=fill)
    rrect(c, x + 0.5, y + 0.5, w - 1, h - 1, r, stroke=1, line=line, a=0.06)


def save(s, name):
    OUT.mkdir(parents=True, exist_ok=True)
    s.makeImageSnapshot().save(str(OUT / name), skia.kPNG)
    print("wrote", name)


def wrap(s, font, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.measureText(t) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def paragraph(c, s, x, y, font, col, maxw, lh, a=1.0):
    for i, ln in enumerate(wrap(s, font, maxw)):
        text(c, ln, x, y + i * lh, font, col, a)
    return y + len(wrap(s, font, maxw)) * lh


# ------------------------------------------------------------------ icons
def cross(c, cx, cy, s, col, a=1.0, sw=3.0):
    c.drawLine(cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2, paint(col, a, stroke=sw))
    c.drawLine(cx - s / 2, cy + s / 2, cx + s / 2, cy - s / 2, paint(col, a, stroke=sw))


def mini_grid(c, x, y, cols, rows, s, gap, bad=(), hidden=(), seed=3, a=1.0):
    import random
    rnd = random.Random(seed)
    for i in range(cols):
        h = rnd.randint(max(2, rows - 4), rows)
        for r in range(rows):
            xx, yy = x + i * (s + gap), y + (rows - 1 - r) * (s + gap)
            if (i, r) in bad:
                cell(c, xx, yy, s, "bad", a, flash=1)
            elif r >= h and (i, r) not in hidden:
                cell(c, xx, yy, s, "empty", a)
            elif (i, r) in hidden:
                cell(c, xx, yy, s, "ok", a)
                text(c, "?", xx + s / 2, yy + s * 0.78, F("semi", s * 0.8), "#0E0F12", a, "c")
            else:
                cell(c, xx, yy, s, "ok", a)


def db_icon(c, x, y, w, col, a=1.0):
    for k in range(3):
        rrect(c, x, y + k * (w * 0.34), w, w * 0.26, w * 0.09, stroke=2.6, line=col, a=a)
        cell(c, x + w * 0.12, y + k * (w * 0.34) + w * 0.07, w * 0.12, "hot", a)


def person(c, cx, cy, s, col, a=1.0):
    c.drawCircle(cx, cy - s * 0.22, s * 0.2, paint(col, a, stroke=3))
    p = skia.Path()
    p.moveTo(cx - s * 0.38, cy + s * 0.5)
    p.cubicTo(cx - s * 0.38, cy + s * 0.05, cx + s * 0.38, cy + s * 0.05, cx + s * 0.38, cy + s * 0.5)
    c.drawPath(p, paint(col, a, stroke=3))


def clock(c, cx, cy, s, col, a=1.0):
    c.drawCircle(cx, cy, s / 2, paint(col, a, stroke=3))
    c.drawLine(cx, cy, cx, cy - s * 0.3, paint(col, a, stroke=3))
    c.drawLine(cx, cy, cx + s * 0.22, cy + s * 0.1, paint(col, a, stroke=3))


def bars_icon(c, x, y, s, col, a=1.0):
    for i, hgt in enumerate([0.45, 0.8, 0.6, 1.0, 0.7]):
        rrect(c, x + i * s * 0.22, y + s * (1 - hgt), s * 0.15, s * hgt, 3, fill=col, a=a)


def badge(c, x, y, label, filled=False, size=20):
    w = F("semi", size).measureText(label) + 38
    if filled:
        rrect(c, x, y, w, size + 20, (size + 20) / 2, fill=WHITE)
        text(c, label, x + 19, y + size + 4, F("semi", size), INK)
    else:
        rrect(c, x, y, w, size + 20, (size + 20) / 2, stroke=1.4, line="#4A4B50")
        text(c, label, x + 19, y + size + 4, F("semi", size), "#C9CACD")
    return w


# ------------------------------------------------------------------ 1. problem / solution
def problem_solution():
    s, c = canvas(1600, 900)
    for k, (x, ok) in enumerate([(70, False), (830, True)]):
        panel(c, x, 80, 700, 740)
        badge(c, x + 40, 118, "Z GUARD" if ok else "Bez GUARD", filled=ok)
        text(c, "Automat pilnuje danych" if ok else "Ręczna robota w Excelu", x + 40, 232, F("semi", 38), WHITE)
        text(c, "pliki → sprawdzenie → baza → raport" if ok else "pliki → kopiuj, wklej → raport", x + 40, 272, F("reg", 22), GREY2)
        # illustration
        for i in range(3):
            file_icon(c, x + 52 + i * 62, 318, 30, "#9A9BA1", 1)
        arrow(c, x + 262, 345, x + 332, "#6A6B71", 1)
        if ok:
            mark_only(c, x + 350, 320, 0.10, WHITE)
            arrow(c, x + 418, 345, x + 470, "#6A6B71", 1)
            mini_grid(c, x + 488, 305, 6, 5, 22, 6, bad={(1, 2), (4, 3)}, seed=5)
        else:
            person(c, x + 372, 342, 52, "#B4B5BA")
            arrow(c, x + 412, 345, x + 462, "#6A6B71", 1)
            mini_grid(c, x + 488, 305, 6, 5, 22, 6, hidden={(1, 2), (4, 3), (3, 1)}, seed=5)
        c.drawRect(skia.Rect.MakeXYWH(x + 40, 440, 620, 1.2), paint(LINE))
        rows = ([("0 godzin ręcznej pracy", "pliki ładują się same, o świcie"),
                 ("każdy błąd ma powód", "odrzucone wiersze trafiają na listę"),
                 ("kopie, które da się odtworzyć", "test odtwarzania co tydzień")] if ok else
                [("kilka godzin co tydzień", "kopiowanie i poprawianie w Excelu"),
                 ("wie o tym jedna osoba", "po jej odejściu nikt nie rozumie procesu"),
                 ("błędy widać dopiero u klienta", "nikt nie liczy, co poszło nie tak")])
        for i, (h1, h2) in enumerate(rows):
            y = 492 + i * 108
            if ok:
                rrect(c, x + 40, y - 8, 46, 46, 23, fill=WHITE)
                check(c, x + 63, y + 15, 20, INK, 1, 1, 4.2)
            else:
                rrect(c, x + 40, y - 8, 46, 46, 23, stroke=2, line="#4A4B50")
                cross(c, x + 63, y + 15, 16, "#8B8C92", 1, 3.4)
            text(c, h1, x + 108, y + 16, F("med", 27), WHITE if ok else "#C9CACD")
            text(c, h2, x + 108, y + 50, F("reg", 21), GREY2)
    save(s, "problem-solution.png")


# ------------------------------------------------------------------ 2. how it works
def how_it_works():
    s, c = canvas(1600, 810)
    panel(c, 50, 50, 1500, 700)
    text(c, "Jak to działa", 110, 134, F("semi", 36), WHITE)
    text(c, "cztery kroki, bez ręcznej pracy", 1490, 134, F("reg", 24), "#6F7076", 1, "r")
    steps = [("1", "Pliki", "Sieci reklamowe wysyłają raporty w różnych formatach."),
             ("2", "Kontrola", "GUARD sprawdza każdy wiersz. Błędne trafiają na listę z powodem."),
             ("3", "Baza", "Dobre dane lądują w bazie, gdzie każdy widzi tylko swoją część."),
             ("4", "Raporty", "Konsola i raporty pokazują wyniki. Bez Excela.")]
    cw = 320
    for i, (n, title, desc) in enumerate(steps):
        x = 110 + i * (cw + 30)
        rrect(c, x, 190, cw, 356, 24, fill="#131418")
        rrect(c, x + 0.5, 190.5, cw - 1, 355, 24, stroke=1, line="#2A2B30")
        rrect(c, x + 28, 218, 44, 44, 22, stroke=2, line=WHITE)
        text(c, n, x + 50, 249, F("semi", 24), WHITE, 1, "c")
        ix, iy = x + 28, 292
        if i == 0:
            for k in range(3):
                file_icon(c, ix + k * 56, iy, 30, "#B4B5BA", 1)
        elif i == 1:
            mark_only(c, ix, iy - 2, 0.12, WHITE)
            mini_grid(c, ix + 92, iy - 4, 5, 3, 16, 5, bad={(2, 1)}, seed=9)
        elif i == 2:
            db_icon(c, ix, iy - 2, 70, "#B4B5BA")
            lock(c, ix + 120, iy + 28, 34, "#8B8C92", 1)
        else:
            bars_icon(c, ix, iy - 4, 70, "#B4B5BA")
            cell(c, ix + 100, iy + 6, 18, "hot")
            cell(c, ix + 126, iy + 6, 18, "ok")
        text(c, title, x + 28, 408, F("semi", 31), WHITE)
        paragraph(c, desc, x + 28, 446, F("reg", 21), "#9C9DA3", cw - 56, 29)
        if i < 3:
            arrow(c, x + cw + 4, 368, x + cw + 26, "#6A6B71", 1, 1, 2.6)
    # supporting row
    text(c, "przez cały czas", 110, 610, F("reg", 21), "#6F7076")
    x = 110
    for lab, kind in [("kopie zapasowe z testem odtwarzania", "lock"), ("uprawnienia i RODO", "person"), ("alarmy i instrukcje awaryjne", "clock")]:
        w = F("med", 22).measureText(lab) + 78
        rrect(c, x, 632, w, 62, 31, stroke=1.4, line="#3A3B41")
        {"lock": lambda: lock(c, x + 34, 662, 24, "#C9CACD", 1),
         "person": lambda: person(c, x + 34, 662, 30, "#C9CACD"),
         "clock": lambda: clock(c, x + 34, 663, 26, "#C9CACD")}[kind]()
        text(c, lab, x + 58, 671, F("med", 22), "#E4E4E6")
        x += w + 20
    save(s, "how-it-works.png")


# ------------------------------------------------------------------ 3. a day with GUARD
def day_timeline():
    s, c = canvas(1600, 740)
    panel(c, 50, 50, 1500, 640)
    text(c, "Jeden dzień z GUARD", 110, 134, F("semi", 36), WHITE)
    text(c, "wszystko dzieje się samo", 1490, 134, F("reg", 24), "#6F7076", 1, "r")
    ax0, ax1, top = 640, 1470, 196

    def X(h):
        return ax0 + (ax1 - ax0) * h / 24

    for h in range(0, 25, 3):
        x = X(h)
        text(c, f"{h:02d}:00", x, top, F("mono", 18), "#76777D", 1, "c")
        c.drawLine(x, top + 16, x, top + 16 + 5 * 82 + 6, paint("#25262B", 1, stroke=1.4, dash=(3, 6)))
    lanes = [("Kopia zapasowa", "zaszyfrowana, z sumą kontrolną", [(2.0, "02:00", "hot")]),
             ("Ładowanie plików", "z 3 sieci reklamowych", [(5.5, "05:30", "hot")]),
             ("Kontrola dostaw", "czy każdy plik dotarł?", [(6.25, "06:15", "ok")]),
             ("Kontrola stanu", "baza, dysk, kopie, alarmy", None),
             ("Test odtwarzania", "tylko w niedziele", [(3.0, "nd 03:00", "bad")])]
    for i, (title, sub, marks) in enumerate(lanes):
        y = top + 36 + i * 82
        rrect(c, 110, y, 1380, 66, 16, fill="#121317")
        text(c, title, 140, y + 29, F("semi", 25), WHITE)
        text(c, sub, 140, y + 54, F("reg", 18), GREY2)
        if marks is None:
            for k in range(144):
                cell(c, X(k / 6) + 1, y + 29, 7, "ok" if k % 6 else "hot")
            text(c, "co 10 minut", ax1 - 8, y + 24, F("mono", 17), "#B4B5BA", 1, "r")
            continue
        for h, label, st in marks:
            x = X(h)
            cell(c, x - 15, y + 18, 30, st, 1, flash=1)
            text(c, label, x + 28, y + 40, F("monomed", 20), WHITE)
    save(s, "day-timeline.png")


# ------------------------------------------------------------------ 4. architecture
def box(c, x, y, w, h, title, sub=None, hot=False, r=18):
    rrect(c, x, y, w, h, r, fill=WHITE if hot else "#131418")
    if not hot:
        rrect(c, x + 0.5, y + 0.5, w - 1, h - 1, r, stroke=1, line="#2E2F35")
    text(c, title, x + w / 2, y + h / 2 + (-2 if sub else 8), F("semi", 24), INK if hot else WHITE, 1, "c")
    if sub:
        text(c, sub, x + w / 2, y + h / 2 + 26, F("reg", 18), "#4A4B50" if hot else GREY2, 1, "c")


def architecture():
    s, c = canvas(1600, 960)
    panel(c, 50, 50, 1500, 860)
    text(c, "Architektura", 110, 134, F("semi", 36), WHITE)
    text(c, "co z czym rozmawia", 1490, 134, F("reg", 24), "#6F7076", 1, "r")
    for i, (n, sub) in enumerate([("AdServe", "CSV, UTF-8, PLN"), ("MediaBuy", "CSV, cp1250, ;"), ("EuroAds", "CSV, EUR")]):
        box(c, 110, 190 + i * 100, 210, 80, n, sub)
        c.drawLine(320, 230 + i * 100, 370, 330, paint("#5A5B61", 1, stroke=2.4))
    arrow(c, 370, 330, 410, "#8B8C92", 1, 1, 2.6)
    box(c, 410, 270, 240, 120, "GUARD", "sprawdza i ładuje", hot=True)
    arrow(c, 650, 330, 710, "#8B8C92", 1, 1, 2.6)
    rrect(c, 710, 190, 400, 300, 22, fill="#131418")
    rrect(c, 710.5, 190.5, 399, 299, 22, stroke=1, line="#2E2F35")
    text(c, "PostgreSQL", 740, 234, F("semi", 26), WHITE)
    for i, (n, sub) in enumerate([("core", "kampanie, wyniki dzienne"), ("ops", "log ładowań, odrzucone, audyt"), ("reporting", "widoki bez danych osobowych")]):
        rrect(c, 740, 256 + i * 74, 340, 62, 12, fill="#1A1B20")
        text(c, n, 760, 286 + i * 74, F("monomed", 21), WHITE)
        text(c, sub, 760, 308 + i * 74, F("reg", 17), GREY2)
    for i, (n, sub) in enumerate([("Konsola", "tylko do odczytu"), ("Raport PowerShell", "rola analityka"), ("Grafana", "wykresy i alarmy")]):
        box(c, 1240, 190 + i * 100, 250, 80, n, sub)
        c.drawLine(1110, 340, 1240, 230 + i * 100, paint("#5A5B61", 1, stroke=2.4))
    c.drawLine(1110, 340, 1160, 340, paint("#5A5B61", 1, stroke=2.4))
    # bottom row
    c.drawLine(910, 490, 910, 560, paint("#5A5B61", 1, stroke=2.4, dash=(6, 6)))
    text(c, "co noc", 924, 534, F("mono", 17), GREY2)
    box(c, 710, 560, 400, 96, "Kopia zapasowa", "pg_dump + GPG AES-256")
    arrow(c, 710, 608, 650, "#8B8C92", 1, 1, 2.6) if False else None
    c.drawLine(710, 608, 640, 608, paint("#8B8C92", 1, stroke=2.6))
    box(c, 410, 560, 230, 96, "Azure Blob", "kopia poza serwerem")
    c.drawLine(910, 656, 910, 720, paint("#5A5B61", 1, stroke=2.4, dash=(6, 6)))
    box(c, 710, 720, 400, 96, "Test odtwarzania", "co tydzień, z pomiarem czasu", hot=True)
    box(c, 1240, 560, 250, 96, "Monitoring", "kontrola co 10 min")
    c.drawLine(1110, 340, 1175, 340, paint("#5A5B61", 1, stroke=2.4))
    c.drawLine(1365, 470, 1365, 560, paint("#5A5B61", 1, stroke=2.4, dash=(6, 6)))
    box(c, 1240, 720, 250, 96, "Alarm + runbook", "co zrobić, krok po kroku")
    c.drawLine(1365, 656, 1365, 720, paint("#5A5B61", 1, stroke=2.4))
    save(s, "architecture.png")


# ------------------------------------------------------------------ 5. who benefits
def for_whom():
    s, c = canvas(1600, 640)
    cards = [("Dla rekrutera", ["Realistyczny projekt, nie tutorial", "Testy, CI i dokumentacja", "Widać sposób myślenia: runbooki, ADR"]),
             ("Dla działu biznesowego", ["Wyniki bez Excela", "Wiadomo, dlaczego liczby się różnią", "Brak dostępu do danych osobowych"]),
             ("Dla administratora", ["Alarmy i instrukcje awaryjne", "Kopie z testem odtwarzania", "Jedno polecenie: guard health"])]
    cw = 470
    for i, (title, items) in enumerate(cards):
        x = 60 + i * (cw + 35)
        panel(c, x, 70, cw, 500)
        text(c, title, x + 40, 150, F("semi", 33), WHITE)
        c.drawRect(skia.Rect.MakeXYWH(x + 40, 182, cw - 80, 1.2), paint(LINE))
        for j, it in enumerate(items):
            y = 244 + j * 118
            rrect(c, x + 40, y - 6, 44, 44, 22, fill=WHITE)
            check(c, x + 62, y + 16, 19, INK, 1, 1, 4)
            paragraph(c, it, x + 106, y + 14, F("med", 25), "#E4E4E6", cw - 150, 32)
    save(s, "for-whom.png")


# ------------------------------------------------------------------ 6. tech stack strip
def stack():
    s, c = canvas(1600, 340)
    panel(c, 50, 50, 1500, 240)
    text(c, "Technologie", 100, 120, F("semi", 28), WHITE)
    chips = ["PostgreSQL 16", "Python", "Flask", "Bash", "PowerShell", "Linux", "cron", "Docker Compose", "Prometheus", "Grafana", "GPG", "Azure Blob", "Git + GitHub Actions", "MkDocs"]
    x, y = 100, 150
    for ch in chips:
        w = F("med", 21).measureText(ch) + 40
        if x + w > 1500:
            x, y = 100, y + 56
        rrect(c, x, y, w, 44, 22, stroke=1.4, line="#4A4B50")
        text(c, ch, x + 20, y + 29, F("med", 21), "#E4E4E6")
        x += w + 12
    save(s, "stack.png")


# ------------------------------------------------------------------ 7. social preview (dark)
def social():
    s, c = canvas(1280, 640, dark=True)
    lockup(c, 215, 210, 1.7, WHITE)
    text(c, "Czyste dane reklamowe. Zaufane raporty.", 640, 470, F("med", 30), WHITE, 0.6, "c")
    text(c, "kontrola danych  ·  kopie zapasowe  ·  uprawnienia  ·  monitoring", 640, 540, F("reg", 22), "#6F7076", 1, "c")
    save(s, "social-preview.png")


# ------------------------------------------------------------------ 8. screenshots in a card
def framed(src, out, width=1600, pad=80):
    img = skia.Image.open(str(src))
    iw, ih = img.width(), img.height()
    cw = width - 2 * pad
    ch = round(cw * ih / iw)
    s, c = canvas(width, ch + 2 * pad)
    panel(c, pad, pad, cw, ch, r=34, fill="#101114")
    c.save()
    c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(pad, pad, cw, ch), 34, 34), True)
    c.drawImageRect(img, skia.Rect.MakeXYWH(pad, pad, cw, ch), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    c.restore()
    save(s, out)


if __name__ == "__main__":
    for fn in (problem_solution, how_it_works, day_timeline, architecture, for_whom, stack, social):
        fn()
    shots = ROOT / "docs" / "screenshots"
    for name in ("overview", "rejects", "status", "campaigns", "runs"):
        if (shots / f"console-{name}.png").exists():
            framed(shots / f"console-{name}.png", f"console-{name}-card.png")
