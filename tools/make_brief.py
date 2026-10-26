#!/usr/bin/env python3
"""One-page project brief (PDF + PNG) in the GUARD style. Needs: pip install weasyprint ; apt install poppler-utils.
   python tools/make_brief.py   ->  docs/guard-project-brief.pdf, docs/images/project-brief.png
"""
import base64
import json
import re
import subprocess
from pathlib import Path

import weasyprint

ROOT = Path(__file__).resolve().parent.parent
N = json.loads((ROOT / "tools" / "video" / "numbers.json").read_text())


def b64(path):
    return base64.b64encode((ROOT / path).read_bytes()).decode()


def crop_b64(path, box):
    from PIL import Image
    import io
    im = Image.open(ROOT / path).convert("RGB").crop(box)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


logo = re.sub(r'<svg[^>]*>', '<svg viewBox="253 325 500 120" width="190" xmlns="http://www.w3.org/2000/svg">',
              (ROOT / "docs/assets/brand/guard-logo-white.svg").read_text(), count=1)
chips = ["PostgreSQL 16", "Python", "Flask", "Bash", "PowerShell", "Linux", "cron", "Docker Compose", "Prometheus", "Grafana",
         "GPG", "Azure Blob", "Git + GitHub Actions", "MkDocs"]
chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
fmt = lambda n: f"{n:,}".replace(",", "\u00a0")
html = f"""<!doctype html><html lang="pl"><head><meta charset="utf-8"><style>
@page{{size:A4;margin:0}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:Inter,Arial,sans-serif;color:#0B0B0C;font-size:9.4pt;line-height:1.4;background:#fff}}
.top{{background:#0B0B0C;color:#fff;padding:8mm 12mm 7mm;display:flex;justify-content:space-between;align-items:center}}
.tr{{text-align:right;font-size:8.3pt;color:#A5A6AB;line-height:1.6}} .tr b{{color:#fff;font-weight:600}}
.wrap{{padding:5.5mm 12mm 0}}
h2{{font-size:8.6pt;letter-spacing:.9px;text-transform:uppercase;color:#6B6C72;margin:0 0 2mm;font-weight:600}}
p{{margin:0 0 3.2mm}}
.kpis{{display:flex;gap:3mm;margin:1mm 0 4mm}}
.k{{flex:1;background:#0E0F12;color:#fff;border-radius:3mm;padding:3mm 3.4mm}}
.k b{{display:block;font-size:16pt;font-weight:600;letter-spacing:-.3px;line-height:1.15}} .k span{{font-size:7.8pt;color:#8B8C92}}
.note{{font-size:7.4pt;color:#8B8C92;margin:-2.6mm 0 4mm}}
img.flow{{width:100%;margin:0 0 4mm;border-radius:3mm;display:block}}
.cols{{display:flex;gap:7mm;margin-bottom:3mm}} .cols>div{{flex:1}}
ul{{margin:0;padding-left:4.4mm}} li{{margin-bottom:1.6mm}}
.shot{{height:30mm;overflow:hidden;border-radius:3mm;margin-bottom:1.4mm;background:#0E0F12}} .shot img{{width:100%;display:block}}
.cap{{font-size:7.4pt;color:#8B8C92;margin-bottom:3.6mm}}
.chip{{display:inline-block;border:1px solid #C9CACD;border-radius:99px;padding:.5mm 2.8mm;margin:0 1.2mm 1.5mm 0;font-size:8pt;font-weight:600}}
.foot{{position:absolute;bottom:0;left:0;right:0;padding:3.2mm 12mm;background:#F1F1EF;font-size:7.8pt;color:#6B6C72;display:flex;justify-content:space-between;gap:10mm}}
</style></head><body>
<div class="top">{logo}<div class="tr"><b>Czyste dane reklamowe. Zaufane raporty.</b><br>Projekt portfolio · Junior DevOps<br>Dane syntetyczne · licencja MIT</div></div>
<div class="wrap">
<h2>Do czego służy</h2>
<p>Sieci reklamowe codziennie przysyłają pliki z wynikami reklam, każda w innym formacie i z błędami. <b>GUARD automatycznie ładuje je do bazy PostgreSQL</b>,
odrzuca błędne wiersze i tłumaczy dlaczego, chroni dane osobowe, robi kopie zapasowe i <b>dowodzi, że da się je odtworzyć</b>, a działom biznesowym daje konsolę tylko do odczytu.
Projekt odwzorowuje pracę operacyjną wokół systemów raportowych kluczowych dla firmy medialnej.</p>
<div class="kpis">
<div class="k"><b>{N['files']} plików</b><span>{fmt(N['read'])} wierszy sprawdzonych w ok. 0,7 s</span></div>
<div class="k"><b>{N['rejected']}</b><span>wierszy odrzuconych ({str(N['reject_pct']).replace('.', ',')}%), każdy z powodem</span></div>
<div class="k"><b>43 testy</b><span>31 automatycznych + 12 uprawnień</span></div>
<div class="k"><b>≈ 1 s</b><span>odtworzenie zaszyfrowanej kopii (demo)</span></div>
</div>
<div class="note">Zmierzone na syntetycznym zestawie demo. Czas odtwarzania przy realnej wielkości danych to cel opisany w dokumentacji, nie pomiar.</div>
<h2>Jak to działa</h2>
<img class="flow" src="data:image/png;base64,{crop_b64('docs/images/how-it-works.png', (40, 40, 1560, 764))}">
<div class="cols"><div>
<h2>Co robi</h2><ul>
<li><b>Idempotentny ETL</b> dla trzech formatów plików (UTF-8 i Windows-1250, PLN i EUR, trzy style dat). Bezpieczne ponowne uruchomienie.</li>
<li><b>Kontrola jakości:</b> lista odrzuconych wierszy, kwarantanna uszkodzonych plików, alarm o braku pliku.</li>
<li><b>Najmniejsze uprawnienia</b>, maskowane widoki i rejestr zmian (RODO).</li></ul></div><div>
<h2>&nbsp;</h2><ul>
<li><b>Szyfrowane kopie</b> (GPG AES-256), cotygodniowy test odtwarzania, kopia w Azure Blob.</li>
<li><b>Monitoring:</b> kontrola stanu, reguły alertów Prometheus, Grafana, strona statusu.</li>
<li><b>Dokumentacja operacyjna:</b> runbook, ćwiczenia awaryjne, 6 decyzji architektonicznych, cele usługi, audyt „odziedziczonego” systemu.</li></ul></div></div>
<h2>Technologie</h2><div>{chip_html}</div>
</div>
<div class="foot"><span>GUARD v1.0.0 · projekt portfolio, dane syntetyczne</span><span>Kod, runbook i decyzje architektoniczne: repozytorium GitHub</span></div>
</body></html>"""
out = ROOT / "docs" / "guard-project-brief.pdf"
weasyprint.HTML(string=html).write_pdf(str(out))
pages = subprocess.check_output(["pdfinfo", str(out)]).decode().split("Pages:")[1].split("\n")[0].strip()
subprocess.check_call(["pdftoppm", "-png", "-r", "110", "-singlefile", str(out), str(ROOT / "docs/images/project-brief")])
print("pages:", pages)
