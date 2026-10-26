"""The GUARD demo film: intro, six scenes, outro. All numbers come from numbers.json (a real demo run)."""
import json
import random
from datetime import date, timedelta

import skia

from engine import *  # noqa: F401,F403
from engine import _word_path  # noqa: F401

N = json.loads((HERE / "numbers.json").read_text())
LAST = date.fromisoformat(N["days"][-1][0])
PL_MON = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"]
PL_DAY = ["pn", "wt", "śr", "cz", "pt", "sb", "nd"]

SCENES = [("files", 3.8, 9.4), ("grid", 9.4, 18.2), ("roles", 18.2, 24.4),
          ("backup", 24.4, 30.2), ("status", 30.2, 35.8), ("console", 35.8, 41.2)]
DURATION = 46.0


numr = lambda v: num(round(v))


def env(T, s, e, fin=0.5, fout=0.4):
    return out_cubic(seg(T, s, s + fin)) * (1 - in_out(seg(T, e - fout, e)))


# ------------------------------------------------------------------ tooltip with auto width
def tip(c, x, y, l1, l2, l3, a):
    w = max(330, F("semi", 31).measureText(l2) + 56, F("reg", 19).measureText(l3) + 76)
    tooltip(c, x, y, l1, l2, l3, a, w)
    return w


# ------------------------------------------------------------------ scene 1: files arrive
def scene_files(c, t, a, dy):
    header(c, "Każdego ranka przychodzą pliki", "CSV z sieci reklamowych", a, dy)
    d = LAST
    cards = [("AdServe PL", f"adserve_{d}.csv", d.strftime("%Y-%m-%d"), "148.20 PLN", "UTF-8  ·  przecinek"),
             ("MediaBuy Polska", f"mediabuy_{d}.csv", d.strftime("%d.%m.%Y"), "148,20 zł", "Windows-1250  ·  średnik"),
             ("EuroAds Network", f"euroads_{d}.csv", d.strftime("%m/%d/%Y"), "34.63 EUR", "UTF-8  ·  daty USA")]
    cw, gap, y0 = 360, 44, CY + 132
    for i, (name, fname, dt, amount, enc) in enumerate(cards):
        ai = a * out_cubic(seg(t, 0.25 + i * 0.28, 0.95 + i * 0.28))
        x, y = L + i * (cw + gap), y0 + (1 - out_cubic(seg(t, 0.25 + i * 0.28, 1.0 + i * 0.28))) * 34 + dy
        rrect(c, x, y, cw, 318, 20, fill="#131418", a=ai)
        rrect(c, x + 0.5, y + 0.5, cw - 1, 317, 20, stroke=1, line="#2A2B30", a=ai)
        file_icon(c, x + 30, y + 30, 24, "#9A9BA1", ai)
        text(c, name, x + 72, y + 54, F("semi", 26), WHITE, ai)
        text(c, fname, x + 30, y + 100, F("mono", 15), MUTED, ai)
        c.drawRect(skia.Rect.MakeXYWH(x + 30, y + 124, cw - 60, 1.2), paint("#26272C", ai))
        for j, (lab, val) in enumerate([("Data", dt), ("Kwota", amount), ("Plik", enc)]):
            ry = y + 168 + j * 48
            aj = ai * out_cubic(seg(t, 0.9 + i * 0.28 + j * 0.12, 1.4 + i * 0.28 + j * 0.12))
            text(c, lab, x + 30, ry, F("reg", 20), "#76777D", aj)
            text(c, val, x + cw - 30, ry, F("mono", 19 if j < 2 else 15), WHITE if j < 2 else "#B4B5BA", aj, "r")
    kpis(c, [("3", None, "sieci reklamowe", "codziennie, o świcie", "ok"),
             ("3", None, "formaty plików", "przecinek, średnik, USA", "dim"),
             ("2", None, "waluty", "złoty i euro", "dim"),
             ("0", None, "wspólnych zasad", "każdy pisze po swojemu", "bad")], t, 1.9, a)


# ------------------------------------------------------------------ scene 2: every row is checked
_rng = random.Random(7)
COLS, ROWS = 30, 9
HEIGHTS = [_rng.randint(5, 9) for _ in range(COLS)]
REJ = {}
_cells = [(i, r) for i in range(COLS) for r in range(HEIGHTS[i])]
while len(REJ) < 13:
    i, r = _rng.choice(_cells)
    if i >= 3 and i not in {k[0] for k in REJ}:
        REJ[(i, r)] = len(REJ)
REASONS = [("mediabuy  ·  wiersz 32", "Błędna data", "31-31-2026"),
           ("adserve  ·  wiersz 14", "Kliknięć > wyświetleń", "47 512 kliknięć, 47 012 wyśw."),
           ("euroads  ·  wiersz 9", "Nieznana kampania", "CMP-99999"),
           ("adserve  ·  wiersz 51", "Duplikat wiersza", "ten sam klucz dwa razy"),
           ("mediabuy  ·  wiersz 7", "Brak wyświetleń", "puste pole"),
           ("euroads  ·  wiersz 23", "Ujemny koszt", "-114,79")]
GX0 = L
GP = (R - L) / COLS
GS = GP * 0.74
GY1 = CY + 118
GRP = 33.5


def gx(i):
    return GX0 + i * GP


def gy(r):
    return GY1 + (ROWS - 1 - r) * GRP


def scene_grid(c, t, a, dy):
    header(c, "Strażnik sprawdza każdy wiersz", "każdy kwadrat to wiersz z pliku", a, dy)
    t_s, step = 1.5, 0.085
    for i in range(COLS):
        ci = a * out_cubic(seg(t, 0.2 + i * 0.02, 0.7 + i * 0.02))
        res = seg(t, t_s + i * step, t_s + i * step + 0.45)
        for r in range(ROWS):
            x, y = gx(i), gy(r) + dy
            if r >= HEIGHTS[i]:
                cell(c, x, y, GS, "empty", ci)
                continue
            if res <= 0:
                cell(c, x, y, GS, "dim", ci, grow=0.55 + 0.45 * out_cubic(seg(t, 0.3 + i * 0.02 + r * 0.01, 0.8 + i * 0.02 + r * 0.01)))
            elif (i, r) in REJ:
                cell(c, x, y, GS, "bad", ci, flash=1 - 0.55 * res)
            else:
                cell(c, x, y, GS, "ok", ci, flash=1 - res)
    sweep = seg(t, t_s, t_s + COLS * step + 0.2)
    if 0 < sweep < 1:
        xs = GX0 + sweep * (R - L)
        for k in range(8):
            c.drawRect(skia.Rect.MakeXYWH(xs - 8 - k * 9, GY1 - 10 + dy, 9, ROWS * GRP + 8), paint(WHITE, a * 0.035 * (8 - k)))
        c.drawRect(skia.Rect.MakeXYWH(xs - 1, GY1 - 10 + dy, 2, ROWS * GRP + 8), paint(WHITE, a * 0.7))
    ya = GY1 + ROWS * GRP + 26 + dy
    text(c, (LAST - timedelta(days=29)).strftime("%-d ") + PL_MON[(LAST - timedelta(days=29)).month - 1], L, ya, F("mono", 19), MUTED, a * seg(t, 0.5, 1.2))
    text(c, "wczoraj", R, ya, F("mono", 19), MUTED, a * seg(t, 0.5, 1.2), "r")
    # legend
    ly = CY + CH - 228 + dy
    la = a * out_cubic(seg(t, 3.9, 4.5))
    x = L
    x += dot_label(c, x, ly, "Przyjęte do bazy", None, "ok", la)
    dot_label(c, x, ly, "Odrzucone, z powodem", None, "bad", la)
    # tooltip tour
    order = sorted(REJ, key=lambda k: k[0])[2::3][:4]
    for k, (i, r) in enumerate(order):
        t0 = 4.7 + k * 1.15
        ta = seg(t, t0, t0 + 0.25) * (1 - seg(t, t0 + 0.9, t0 + 1.12))
        if ta > 0:
            x0 = gx(i) + GS / 2
            c.drawRoundRect(skia.Rect.MakeXYWH(gx(i) - 6, GY1 - 8 + dy, GS + 12, ROWS * GRP + 4), 6, 6,
                            paint("#6A6B71", a * ta, stroke=1.6, dash=(5, 5)))
            l1, l2, l3 = REASONS[k % len(REASONS)]
            w = max(330, F("semi", 31).measureText(l2) + 56)
            tx = min(x0 - 30, R - w)
            tip(c, tx, gy(r) - 160 + dy + (1 - out_cubic(ta)) * 10, l1, l2, l3, a * ta)
    kpis(c, [(N["read"], numr, "wierszy sprawdzono", f"{N['files']} plików", "dim"),
             (N["loaded"], numr, "przyjęto do bazy", f"{100 - N['reject_pct']:.1f}% wierszy".replace('.', ','), "ok"),
             (N["rejected"], numr, "odrzucono z powodem", f"{N['reject_pct']}% wierszy".replace('.', ','), "bad"),
             ("0", None, "zgubionych po cichu", "każdy wiersz ma kartkę", "ok")], t, 1.5, a)


# ------------------------------------------------------------------ scene 3: permissions and privacy
ROLES = [("guard_etl", "ładuje dane", ["write", "none", "none", "none"]),
         ("guard_analyst", "czyta raporty", ["none", "none", "read", "none"]),
         ("guard_backup", "robi kopie", ["read", "read", "read", "none"]),
         ("guard_monitor", "pilnuje stanu", ["none", "none", "none", "read"])]
COLS_R = ["Fakty i kampanie", "Dane osobowe", "Raporty", "Stan systemu"]


def mask_mix(clear, masked, p):
    k = int(len(clear) * clamp(p))
    return masked[:k] + clear[k:]


def scene_roles(c, t, a, dy):
    header(c, "Każdy widzi tylko to, co musi", "uprawnienia i RODO", a, dy)
    am = a * (1 - in_out(seg(t, 3.2, 3.7)))
    ap = a * out_cubic(seg(t, 3.5, 4.1))
    if am > 0:
        cx0 = L + 400
        cwid = (R - cx0) / 4
        text(c, "Rola", L + 24, CY + 148 + dy, F("reg", 19), "#76777D", am)
        for j, name in enumerate(COLS_R):
            text(c, name, cx0 + cwid * (j + 0.5), CY + 148 + dy, F("reg", 19), "#76777D", am * seg(t, 0.2, 0.7), "c")
        for i, (role, desc, marks) in enumerate(ROLES):
            ai = am * out_cubic(seg(t, 0.35 + i * 0.25, 0.9 + i * 0.25))
            y = CY + 172 + i * 74 + (1 - out_cubic(seg(t, 0.35 + i * 0.25, 1.0 + i * 0.25))) * 16 + dy
            rrect(c, L, y, R - L, 62, 14, fill="#121317", a=ai)
            if role == "guard_analyst" and seg(t, 2.3, 2.7) > 0:
                rrect(c, L + 0.5, y + 0.5, R - L - 1, 61, 14, stroke=1.4, line=WHITE, a=ai * seg(t, 2.3, 2.7))
            text(c, role, L + 24, y + 28, F("monomed", 20), WHITE, ai)
            text(c, desc, L + 24, y + 51, F("reg", 16), "#76777D", ai)
            for j, m in enumerate(marks):
                mx, my = cx0 + cwid * (j + 0.5), y + 31
                pa = ai * out_cubic(seg(t, 0.8 + i * 0.25 + j * 0.07, 1.2 + i * 0.25 + j * 0.07))
                if m == "write":
                    rrect(c, mx - 13, my - 13, 26, 26, 5, fill=WHITE, a=pa)
                elif m == "read":
                    rrect(c, mx - 13, my - 13, 26, 26, 5, fill="#8E8F95", a=pa)
                elif j == 1:
                    cl = 1.0 if role != "guard_analyst" else seg(t, 2.4, 2.9)
                    lock(c, mx, my - 2, 26, "#8B8C92", pa, closed=cl)
                else:
                    rrect(c, mx - 12, my - 12, 24, 24, 5, stroke=1.6, line="#4A4B50", a=pa, dash=(4, 4))
        ly = CY + CH - 228 + dy
        la = am * out_cubic(seg(t, 1.9, 2.4))
        x = L
        for lab, st in [("zapis", "hot"), ("odczyt", "ok"), ("brak dostępu", "bad")]:
            if st == "ok":
                rrect(c, x, ly - 15, 15, 15, 4, fill="#8E8F95", a=la)
                text(c, lab, x + 27, ly, F("reg", 21), "#B4B5BA", la)
                x += 27 + F("reg", 21).measureText(lab) + 34
            elif st == "bad":
                rrect(c, x, ly - 15, 15, 15, 4, stroke=1.6, line="#6A6B71", a=la, dash=(3, 3))
                text(c, lab, x + 27, ly, F("reg", 21), "#B4B5BA", la)
            else:
                x += dot_label(c, x, ly, lab, None, "hot", la)
    if ap > 0:
        pw = 520
        for k, (title, lines) in enumerate([
                ("W bazie: pełne dane", ["Jan Kowalski", "jan.kowalski@mail.pl", "+48 600 100 200"]),
                ("Widok analityka: zamaskowane", ["J*** K*******", "ja**********@mail.pl", "+48 *** *** 200"])]):
            x = L if k == 0 else R - pw
            y = CY + 124 + dy
            rrect(c, x, y, pw, 308, 20, fill="#131418", a=ap)
            rrect(c, x + 0.5, y + 0.5, pw - 1, 307, 20, stroke=1, line="#2A2B30", a=ap)
            text(c, title, x + 32, y + 52, F("reg", 20), "#76777D", ap)
            clear = ["Jan Kowalski", "jan.kowalski@mail.pl", "+48 600 100 200"]
            for j, ln in enumerate(lines):
                s = ln if k == 0 else mask_mix(clear[j], ln, seg(t, 4.3 + j * 0.25, 5.0 + j * 0.25))
                text(c, s, x + 32, y + 120 + j * 62, F("semi", 34) if j == 0 else F("mono", 23), WHITE if j == 0 else "#C9CACD", ap)
        mx = (L + pw + R - pw) / 2
        lock(c, mx, CY + 236 + dy, 40, WHITE, ap, closed=seg(t, 4.3, 4.8))
        arrow(c, mx - 44, CY + 310 + dy, mx + 44, "#8B8C92", ap, seg(t, 4.0, 4.7))
        x = L
        for k, lab in enumerate(["widoki bez danych osobowych", "maskowane kopie testowe", "szyfrowane kopie zapasowe"]):
            pa = ap * out_cubic(seg(t, 4.9 + k * 0.2, 5.4 + k * 0.2))
            w = F("reg", 19).measureText(lab) + 52
            rrect(c, x, CY + 470 + dy, w, 46, 23, stroke=1.4, line="#3A3B41", a=pa)
            check(c, x + 24, CY + 493 + dy, 14, WHITE, pa, 1.0, 2.6)
            text(c, lab, x + 40, CY + 500 + dy, F("reg", 19), "#C9CACD", pa)
            x += w + 16
    kpis(c, [("4", None, "role", "minimalne uprawnienia", "ok"),
             ("12", None, "testów uprawnień", "wszystkie przechodzą", "ok"),
             ("AES-256", None, "szyfrowanie kopii", "GPG + suma kontrolna", "dim"),
             ("audyt", None, "zmiany w bazie", "kto, co i kiedy", "dim")], t, 1.2, a)


# ------------------------------------------------------------------ scene 4: backups
def scene_backup(c, t, a, dy):
    header(c, "Kopie zapasowe, które naprawdę działają", "co noc o 02:00", a, dy)
    n = 14
    pitch = (R - L) / n
    s = 58
    days = [LAST - timedelta(days=n - 1 - i) for i in range(n)]
    for i, d in enumerate(days):
        t0 = 0.45 + i * 0.13
        ai = a * out_cubic(seg(t, 0.2 + i * 0.04, 0.7 + i * 0.04))
        x, y = L + i * pitch + (pitch - s) / 2, CY + 132 + dy
        done = seg(t, t0, t0 + 0.45)
        rrect(c, x, y, s, s, 10, fill=mix(CELL_DIM, CELL_OK, done), a=ai)
        if done > 0:
            lock(c, x + s / 2, y + s / 2 - 1, 24, "#0E0F12", ai * done, closed=out_cubic(seg(t, t0 + 0.15, t0 + 0.5)))
        sun = d.weekday() == 6
        if sun and done >= 1:
            rr = out_cubic(seg(t, t0 + 0.4, t0 + 1.0))
            rrect(c, x - 6 * rr, y - 6 * rr, s + 12 * rr, s + 12 * rr, 14, stroke=2.0, line=WHITE, a=ai * rr)
        text(c, d.strftime("%d.%m"), x + s / 2, y + s + 34, F("mono", 16), WHITE if sun else MUTED, ai, "c")
        text(c, PL_DAY[d.weekday()], x + s / 2, y + s + 58, F("reg", 16), WHITE if sun else FAINT, ai, "c")
    # restore test
    py = CY + 290 + dy
    pa = a * out_cubic(seg(t, 2.7, 3.3))
    rrect(c, L, py, R - L, 214, 20, fill="#131418", a=pa)
    rrect(c, L + 0.5, py + 0.5, R - L - 1, 213, 20, stroke=1, line="#2A2B30", a=pa)
    text(c, "Test odtwarzania", L + 32, py + 52, F("semi", 26), WHITE, pa)
    text(c, "co niedzielę o 03:00", R - 32, py + 52, F("reg", 20), "#76777D", pa, "r")
    steps = ["odszyfruj kopię", "odtwórz do tymczasowej bazy", "porównaj liczby wierszy"]
    sw = (R - L - 64) / 3
    for k, lab in enumerate(steps):
        t0 = 3.6 + k * 0.85
        sa = pa * out_cubic(seg(t, t0 - 0.2, t0 + 0.2))
        x = L + 32 + k * sw
        rrect(c, x, py + 82, 30, 30, 15, stroke=1.8, line="#5A5B61", a=sa)
        check(c, x + 15, py + 97, 15, WHITE, sa, seg(t, t0 + 0.45, t0 + 0.8), 3.0)
        text(c, lab, x + 46, py + 104, F("reg", 21), "#D2D3D6", sa)
    prog = seg(t, 3.6, 5.9)
    rrect(c, L + 32, py + 138, R - L - 64, 10, 5, fill="#1F2025", a=pa)
    rrect(c, L + 32, py + 138, (R - L - 64) * in_out(prog), 10, 5, fill=WHITE, a=pa)
    done = seg(t, 5.9, 6.4)
    text(c, "Odtworzono w 1 s  ·  liczby wierszy zgodne", L + 32, py + 188, F("med", 24), WHITE, pa * done)
    kpis(c, [("02:00", None, "codzienna kopia", "pg_dump + GPG", "ok"),
             ("14", None, "kopii w retencji", "starsze usuwane", "dim"),
             ("co tydzień", None, "test odtwarzania", "kopia → baza testowa", "ok"),
             ("1 s", None, "czas odtworzenia", "na danych demonstracyjnych", "dim")], t, 1.0, a)


# ------------------------------------------------------------------ scene 5: alarm
CHECKS = [("Baza danych", "przyjmuje połączenia"), ("Świeżość danych", "najnowsze dane: wczoraj"),
          ("Pipeline", "brak nieudanych plików (24 h)"), ("Jakość danych", f"{N['reject_pct']}% wierszy odrzuconych".replace('.', ',')),
          ("Kopia zapasowa", "ostatnia: dziś w nocy"), ("Dysk", "4% zajęte")]


def pill(c, x, y, label, a, inverted=False):
    w = 92 if len(label) < 5 else 112
    if inverted:
        rrect(c, x - w, y, w, 34, 17, fill=WHITE, a=a)
        text(c, label, x - w / 2, y + 23, F("semi", 17), INK, a, "c")
    else:
        rrect(c, x - w, y, w, 34, 17, fill="#1E2025", a=a)
        rrect(c, x - w + 0.5, y + 0.5, w - 1, 33, 17, stroke=1, line="#33343A", a=a)
        text(c, label, x - w / 2, y + 23, F("semi", 17), WHITE, a, "c")


def scene_status(c, t, a, dy):
    header(c, "Alarm, zanim zauważy to biznes", "kontrola co 10 minut", a, dy)
    t_al = 3.2
    al = seg(t, t_al, t_al + 0.4)
    ba = a * out_cubic(seg(t, 0.2, 0.7))
    by = CY + 112 + dy
    fill = mix("#1E2025", WHITE, al)
    rrect(c, L, by, R - L, 62, 16, fill=fill, a=ba)
    msg_ok, msg_bad = "Wszystko działa", "Wymagana reakcja: brakuje pliku mediabuy"
    text(c, msg_ok, L + 28, by + 40, F("semi", 24), WHITE, ba * (1 - al))
    text(c, msg_bad, L + 28, by + 40, F("semi", 24), INK, ba * al)
    for i, (name, detail) in enumerate(CHECKS):
        ai = a * out_cubic(seg(t, 0.5 + i * 0.16, 1.0 + i * 0.16))
        y = CY + 196 + i * 53 + dy
        c.drawRect(skia.Rect.MakeXYWH(L, y + 52, R - L, 1), paint("#1B1C21", ai))
        bad = i == 1
        text(c, name, L + 8, y + 33, F("med", 22), WHITE, ai)
        text(c, detail if not bad or al < 0.5 else "brak pliku mediabuy_" + str(LAST + timedelta(days=1)) + ".csv", L + 330, y + 33, F("reg", 20),
             "#A5A6AB" if not (bad and al > 0.5) else WHITE, ai)
        if bad and al > 0:
            pill(c, R - 8, y + 8, "ALARM", ai * al, True)
            pill(c, R - 8, y + 8, "OK", ai * (1 - al))
        else:
            pill(c, R - 8, y + 8, "OK", ai)
    ra = a * out_cubic(seg(t, 4.2, 4.8))
    if ra > 0:
        text(c, "instrukcja: docs/runbook.md  →", R - 28, by + 39, F("mono", 19), INK, ra, "r")
    kpis(c, [("10 min", None, "interwał kontroli", "zadanie w cron", "ok"),
             ("6", None, "kontroli stanu", "baza, dane, dysk, kopie…", "dim"),
             ("2", None, "poziomy alarmu", "ostrzeżenie i krytyczny", "dim"),
             ("1", None, "instrukcja na każdy alarm", "runbook krok po kroku", "ok")], t, 1.2, a)


# ------------------------------------------------------------------ scene 6: console
def scene_console(c, t, a, dy):
    header(c, "Konsola dla biznesu", "tylko do odczytu", a, dy)
    vals = [v for _, v in N["days"]]
    vmax, hot = max(vals), vals.index(max(vals))
    gx0 = L + 70
    gp = (R - gx0) / COLS
    gs = gp * 0.74
    for lab, f in (("100k", 1.0), ("50k", 0.5), ("0", 0.0)):
        yy = GY1 + (ROWS - 0.5) * GRP - f * (ROWS - 1) * GRP
        text(c, lab, L + 50, yy + 6 + dy, F("mono", 19), "#6F7076", a * seg(t, 0.3, 0.9), "r")
    for i, v in enumerate(vals):
        ci = a * out_cubic(seg(t, 0.2 + i * 0.025, 0.8 + i * 0.025))
        n_f = round(ROWS * v / vmax)
        for r in range(ROWS):
            filled = r < n_f
            st = ("hot" if i == hot else "ok") if filled else "empty"
            grow = out_cubic(seg(t, 0.4 + i * 0.03 + r * 0.025, 0.9 + i * 0.03 + r * 0.025)) if filled else 1
            cell(c, gx0 + i * gp, gy(r) + dy, gs, st, ci, grow=0.3 + 0.7 * grow)
    ya = GY1 + ROWS * GRP + 26 + dy
    d0 = LAST - timedelta(days=29)
    text(c, f"{d0.day} {PL_MON[d0.month - 1]}", gx0, ya, F("mono", 19), MUTED, a * seg(t, 0.5, 1.2))
    text(c, "wczoraj", R, ya, F("mono", 19), MUTED, a * seg(t, 0.5, 1.2), "r")
    ly = CY + CH - 228 + dy
    la = a * out_cubic(seg(t, 1.3, 1.9))
    x = L
    x += dot_label(c, x, ly, "Dzienny koszt (PLN)", None, "ok", la)
    dot_label(c, x, ly, "Najdroższy dzień", None, "hot", la)
    lw = F("reg", 20).measureText("bez danych osobowych") + 64
    rrect(c, R - lw, ly - 28, lw, 42, 21, stroke=1.4, line="#3A3B41", a=la)
    lock(c, R - lw + 26, ly - 8, 18, "#B4B5BA", la)
    text(c, "bez danych osobowych", R - lw + 46, ly, F("reg", 20), "#C9CACD", la)
    for k, i in enumerate([5, 12, hot, 21, 29]):
        t0 = 2.1 + k * 0.62
        ta = seg(t, t0, t0 + 0.2) * (1 - seg(t, t0 + 0.5, t0 + 0.68))
        if ta > 0:
            x0 = gx0 + i * gp
            c.drawRoundRect(skia.Rect.MakeXYWH(x0 - 6, GY1 - 8 + dy, gs + 12, ROWS * GRP + 4), 6, 6,
                            paint("#6A6B71", a * ta, stroke=1.6, dash=(5, 5)))
            d = date.fromisoformat(N["days"][i][0])
            top = gy(max(0, round(ROWS * vals[i] / vmax) - 1))
            w = max(330, F("semi", 31).measureText(num(vals[i]) + " PLN") + 56)
            tip(c, min(x0 - 30, R - w), max(CY + 96, top - 168) + dy, f"{PL_DAY[d.weekday()]} {d.day} {PL_MON[d.month - 1]}",
                f"{num(vals[i])} PLN", "3 sieci reklamowe", a * ta)
    tot = N["total_spend"]
    nets = N["networks"]
    kpis(c, [(tot / 1e6, lambda v: f"{v:.1f}M".replace(".", ","), "koszt reklam, 30 dni (PLN)", "3 sieci razem", "dim"),
             (nets[0][1] / 1e6, lambda v: f"{v:.1f}M".replace(".", ","), nets[0][0], f"{100 * nets[0][1] / tot:.0f}% całości", "hot"),
             (nets[1][1] / 1e3, lambda v: f"{v:.0f}k", nets[1][0], f"{100 * nets[1][1] / tot:.0f}% całości", "ok"),
             (nets[2][1] / 1e3, lambda v: f"{v:.0f}k", nets[2][0], f"{100 * nets[2][1] / tot:.0f}% całości", "ok")], t, 1.0, a)


SCENE_FN = {"files": scene_files, "grid": scene_grid, "roles": scene_roles,
            "backup": scene_backup, "status": scene_status, "console": scene_console}


# ------------------------------------------------------------------ intro / outro / timeline
def big_lockup(c, T0, T, a=1.0):
    tt = T - T0
    lockup(c, 300, 418, 2.0, INK, a, build=seg(tt, 0.2, 1.3), word=seg(tt, 1.0, 1.9))
    text(c, "Czyste dane reklamowe. Zaufane raporty.", W / 2, 722, F("med", 34), INK, a * 0.62 * out_cubic(seg(tt, 1.8, 2.5)), "c")


def render(c, T):
    background(c)
    if T < 3.6:
        big_lockup(c, 0.0, T, 1 - in_out(seg(T, 2.95, 3.5)))
    card_in = seg(T, 3.0, 3.9)
    card_a = out_cubic(seg(T, 3.0, 3.5)) * (1 - in_out(seg(T, 41.0, 41.6)))
    if card_a > 0:
        card(c, appear=card_in, a=card_a)
    for name, s, e in SCENES:
        if s <= T < e:
            a = env(T, s, e)
            SCENE_FN[name](c, T - s, a, (1 - out_cubic(seg(T, s, s + 0.55))) * 18)
    if T >= 41.4:
        big_lockup(c, 41.4, T, 1 - in_out(seg(T, 45.2, 45.9)))
        text(c, "Projekt portfolio  ·  dane syntetyczne", W / 2, 790, F("reg", 24), INK, 0.45 * out_cubic(seg(T, 43.2, 44.0)) * (1 - in_out(seg(T, 45.2, 45.9))), "c")
