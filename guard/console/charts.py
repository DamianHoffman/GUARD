"""Dependency-free inline SVG charts in the GUARD style: a grid of small squares (server-side rendered, no JavaScript)."""
from html import escape

EMPTY, FILL, HOT, TEXT, MUTED, GRID = "#17181C", "#5A5B61", "#FFFFFF", "#E8E8EA", "#8B8C92", "#23252A"
TEAL, NAVY, AMBER = FILL, TEXT, MUTED          # names kept for backwards compatibility with app.py


def _fmt(v: float) -> str:
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.0f}k"
    return f"{v:.0f}"


def bar_chart(labels, values, width=640, height=210, color=None, rows=10) -> str:
    """Columns built from small squares. The tallest column is highlighted in white."""
    values = [float(v or 0) for v in values]
    if not values:
        return '<p class="muted">No data yet.</p>'
    left, top, bottom = 44, 8, 26
    vmax = max(values) or 1
    cols = len(values)
    cell = min((width - left - 6) / cols, (height - top - bottom) / rows)
    size, gap = cell * 0.78, cell * 0.22
    hot = values.index(max(values))
    out = [f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="Daily spend, last {cols} report days">']
    base_y = top + rows * cell
    for frac in (0, 0.5, 1):
        y = base_y - frac * rows * cell + (-size / 2 if frac else -size / 2 + cell * 0.1)
        out.append(f'<text x="{left-8}" y="{y+size/2+4:.1f}" text-anchor="end" font-size="11" fill="{MUTED}" font-family="JetBrains Mono, DejaVu Sans Mono, monospace">{_fmt(vmax*frac)}</text>')
    x_off = left + ((width - left - 6) - cols * cell) / 2
    for i, v in enumerate(values):
        filled = round(rows * v / vmax)
        for r in range(rows):
            x = x_off + i * cell
            y = base_y - (r + 1) * cell + gap / 2
            fill = (HOT if i == hot else FILL) if r < filled else EMPTY
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{size:.1f}" height="{size:.1f}" rx="1.5" fill="{fill}"/>')
    for i in sorted({0, cols // 2, cols - 1}):
        x = x_off + i * cell + size / 2
        out.append(f'<text x="{x:.1f}" y="{height-6}" text-anchor="middle" font-size="11" fill="{MUTED}" font-family="JetBrains Mono, DejaVu Sans Mono, monospace">{escape(str(labels[i]))}</text>')
    out.append("</svg>")
    return "".join(out)


def hbar(items, width=520, color=None, label_w=150) -> str:
    """Horizontal bars as rows of squares: items = [(label, value), ...]."""
    items = [(str(l), float(v or 0)) for l, v in items]
    if not items:
        return '<p class="muted">No data yet.</p>'
    vmax = max(v for _, v in items) or 1
    row_h, n_cells = 26, 24
    cell = (width - label_w - 60) / n_cells
    size = cell * 0.76
    height = row_h * len(items) + 4
    out = [f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="bar chart">']
    for i, (label, v) in enumerate(items):
        y = 2 + i * row_h
        filled = max(1, round(n_cells * v / vmax)) if v else 0
        out.append(f'<text x="0" y="{y+16}" font-size="12" fill="{TEXT}">{escape(label)}</text>')
        for c in range(n_cells):
            fill = (HOT if i == 0 else FILL) if c < filled else EMPTY
            out.append(f'<rect x="{label_w + c*cell:.1f}" y="{y+5}" width="{size:.1f}" height="14" rx="1.5" fill="{fill}"/>')
        out.append(f'<text x="{label_w + n_cells*cell + 8:.1f}" y="{y+16}" font-size="12" fill="{MUTED}">{_fmt(v)}</text>')
    out.append("</svg>")
    return "".join(out)
