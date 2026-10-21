#!/usr/bin/env python3
"""Generate the three figures for the TOON post as standalone SVGs.
Stdlib only. Usage: python3 charts/make_charts.py  (from repo root). Outputs charts/fig*.svg.

Inputs: data/spec-fixtures.csv (fig 1), rerun/results/encoder-2.3.0.json (fig 2, the September 2026
re-run the post cites), data/execution-{a,b}-runs.csv (fig 3).

Design: dark Apify surface, chart-only figures. Titles, explanations and sources live in the post's
captions and body, so the images carry axes, labels and values and nothing else.
Thin marks, 4px rounded data-ends, 2px lines, >=8px markers with 2px surface ring,
hairline gridlines, text in ink tokens (never series colors), legend for >=2 series.
Palette validated (dataviz validate_palette.js, --mode dark, surface #1F2123):
TOON #DC5C05 (apify-orange-600), JSON #1672EB (primary-500).
"""
import csv, json, math, statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"; OUT = ROOT / "charts"
FONT = "Inter, 'SF Pro Text', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
SURF, GRID, AXIS = "#1F2123", "#34373B", "#6D7178"
INK, INK2, MUTED = "#F4F4F5", "#D2D3D6", "#9398A0"
TOON, JSONC, DIM = "#DC5C05", "#1672EB", "#6D7178"
W = 960

def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;")
def text(x, y, s, size=13, fill=INK2, anchor="start", weight=400):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{esc(s)}</text>'
def svg(h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="{FONT}">'
            f'<rect width="{W}" height="{h}" fill="{SURF}"/>{body}</svg>')
def rbar_h(x0, x1, y, t, fill):
    """Horizontal bar from baseline x0 to x1 (either direction), rounded at the data end only."""
    r = min(4, t / 2, abs(x1 - x0))
    if x1 >= x0:
        return (f'<path d="M{x0:.1f},{y:.1f} H{x1 - r:.1f} a{r},{r} 0 0 1 {r},{r} V{y + t - r:.1f} '
                f'a{r},{r} 0 0 1 -{r},{r} H{x0:.1f} Z" fill="{fill}"/>')
    return (f'<path d="M{x0:.1f},{y:.1f} H{x1 + r:.1f} a{r},{r} 0 0 0 -{r},{r} V{y + t - r:.1f} '
            f'a{r},{r} 0 0 0 {r},{r} H{x0:.1f} Z" fill="{fill}"/>')
def dot(x, y, fill, r=5):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 2}" fill="{SURF}"/><circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>'
def jitter(values, step=13):
    """Vertical offsets so identical x-values do not stack into one dot."""
    from collections import Counter, defaultdict
    cnt, seen, out = Counter(values), defaultdict(int), []
    for v in values:
        k, i = cnt[v], seen[v]; seen[v] += 1
        out.append((i - (k - 1) / 2) * step)
    return out
def legend(x, y, items):
    out, cx = "", x
    for label, color in items:
        out += f'<rect x="{cx}" y="{y - 10}" width="12" height="12" rx="2" fill="{color}"/>' + text(cx + 20, y + 1, label, 13, INK2)
        cx += 20 + 7.5 * len(label) + 28
    return out

# ---------------- Fig 1: the proposal (spec fixture bytes, adaptive picker) ----------------
def fig1():
    rows = [r for r in csv.DictReader(open(D / "spec-fixtures.csv")) if not r["tool"].startswith("combined")]
    rowh, barh, top, left, right = 56, 26, 28, 230, 60
    h = top + rowh * len(rows) + 52
    plot_w = W - left - right
    xmin, xmax = -50, 0
    def X(v): return left + (v - xmin) / (xmax - xmin) * plot_w
    b = ""
    for tick in (-50, -40, -30, -20, -10, 0):
        b += f'<line x1="{X(tick):.1f}" y1="{top - 8}" x2="{X(tick):.1f}" y2="{top + rowh * len(rows)}" stroke="{AXIS if tick == 0 else GRID}" stroke-width="1"/>'
        b += text(X(tick), top + rowh * len(rows) + 22, f"{tick}%".replace("-", "\u2212") if tick else "0", 12, MUTED, "middle")
    b += text(left + plot_w / 2, top + rowh * len(rows) + 44, "byte change versus JSON", 12, MUTED, "middle")
    for i, r in enumerate(rows):
        v = float(r["bytes_delta_pct_vs_json"]); y = top + i * rowh + (rowh - barh) / 2
        hot = r["tool"] == "dataset-items"
        name = "get-dataset-items" if hot else r["tool"]
        b += rbar_h(X(0), X(v), y, barh, TOON if hot else JSONC)
        b += text(left - 16, y + barh / 2 + 5, name, 14, INK, "end", 600 if hot else 400)
        b += text(X(v) - 10, y + barh / 2 + 5, f"{v:.1f}%".replace("-", "\u2212"), 13, INK, "end", 600)
    (OUT / "fig1-spec-promise.svg").write_text(svg(h, b))

# ---------------- Fig 2: encoder tokens by rows (September 2026 re-run) ----------------
def fig2():
    rows = json.load(open(ROOT / "rerun" / "results" / "encoder-2.3.0.json"))["rows"]
    series = [("maps", "Google Maps places", TOON), ("rag", "Web pages as text", JSONC)]
    pts = {k: sorted((int(r["label"].split("n=")[1]), r["toonFlatTokPct"]) for r in rows if r["label"].startswith(k + " n="))
           for k, _, _ in series}
    ns = [1, 5, 10, 15, 25, 50, 100]
    h = 430; top, left, right, bottom = 60, 64, 210, 64
    plot_w, plot_h = W - left - right, h - top - bottom
    ymin, ymax = -5, 25
    def X(n): return left + math.log10(n) / 2 * plot_w  # log scale, 1 to 100
    def Y(v): return top + (ymax - v) / (ymax - ymin) * plot_h
    b = legend(left + plot_w - 360, 28, [(name, c) for _, name, c in series])
    for tick in (-5, 0, 5, 10, 15, 20, 25):
        b += f'<line x1="{left}" y1="{Y(tick):.1f}" x2="{left + plot_w}" y2="{Y(tick):.1f}" stroke="{AXIS if tick == 0 else GRID}" stroke-width="1"/>'
        b += text(left - 12, Y(tick) + 4, f"{tick:+d}%".replace("-", "\u2212") if tick else "0", 12, MUTED, "end")
    for n in ns:
        b += text(X(n), top + plot_h + 22, str(n), 12, MUTED, "middle")
    b += text(left + plot_w / 2, top + plot_h + 46, "dataset items per tool call", 12, MUTED, "middle")
    b += text(left - 12, 29, "token change, TOON vs JSON", 12, MUTED, "start")
    for k, name, c in series:
        p = pts[k]
        d = " ".join(f"{'M' if i == 0 else 'L'}{X(n):.1f},{Y(v):.1f}" for i, (n, v) in enumerate(p))
        b += f'<path d="{d}" fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
        for n, v in p: b += dot(X(n), Y(v), c, 4)
        n, v = p[-1]
        b += text(X(n) + 14, Y(v) + 5, f"{v:+.1f}%", 14, INK, weight=600)
        b += text(X(n) + 14 + 10.5 * len(f"{v:+.1f}%"), Y(v) + 5, f"at {n} items", 12, MUTED)
    (OUT / "fig2-encoder-tokens.svg").write_text(svg(h, b))

# ---------------- Fig 3: the A/B noise ----------------
def fig3():
    a = list(csv.DictReader(open(D / "execution-a-runs.csv"))); bb = list(csv.DictReader(open(D / "execution-b-runs.csv")))
    exec_a = {f: [(int(r["pass_count"]), int(r["test_count"])) for r in a if r["format"] == f] for f in ("toon", "json")}
    exec_b = {f: [(int(r["pass_count"]), int(r["pass_count"]) + int(r["fail_count"]) + int(r["error_count"])) for r in bb if r["format"] == f]
              for f in ("toon", "json")}
    left, right = 170, 150; plot_w = W - left - right
    rowh = 46
    def X(p): return left + p * plot_w
    def panel(y0, title, ex):
        out = text(40, y0, title, 15, INK, weight=600)
        base = y0 + 22
        for tick in (0, 0.25, 0.5, 0.75, 1.0):
            out += f'<line x1="{X(tick):.1f}" y1="{base}" x2="{X(tick):.1f}" y2="{base + 2 * rowh}" stroke="{GRID}" stroke-width="1"/>'
            out += text(X(tick), base + 2 * rowh + 18, f"{int(tick * 100)}%", 12, MUTED, "middle")
        for j, (fmt, color, label) in enumerate((("toon", TOON, "TOON"), ("json", JSONC, "JSON"))):
            y = base + j * rowh + rowh / 2
            p = ex[fmt]; rates = [x / t for x, t in p]; mean = st.mean(rates)
            out += text(left - 18, y + 5, label, 14, INK, "end", 600)
            out += f'<line x1="{X(mean):.1f}" y1="{y - 14}" x2="{X(mean):.1f}" y2="{y + 14}" stroke="{INK2}" stroke-width="2"/>'
            for r_, dy in zip(rates, jitter(rates)): out += dot(X(r_), y + dy, color, 5)
            out += text(X(1.0) + 18, y + 5, f"mean {mean * 100:.0f}%", 13, INK2)
        return out
    h = 2 * (22 + 2 * rowh + 30) + 70
    b = panel(34, "Round 1 · 5 runs per format", exec_a)
    b += panel(34 + 22 + 2 * rowh + 30 + 40, "Round 2 · 3 runs per format", exec_b)
    (OUT / "fig3-ab-noise.svg").write_text(svg(h, b))

if __name__ == "__main__":
    fig1(); fig2(); fig3()
    for f in sorted(OUT.glob("fig*.svg")): print(f.name, f.stat().st_size, "bytes")
