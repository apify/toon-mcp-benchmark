#!/usr/bin/env python3
"""Generate the three figures for the TOON post as standalone SVGs from data/*.csv.
Stdlib only. Usage: python3 charts/make_charts.py  (from repo root). Outputs charts/fig*.svg.

Design: thin marks, 4px rounded data-ends, 2px lines, >=8px markers with 2px surface ring,
hairline solid gridlines, text in ink tokens (never series colors), legend for >=2 series.
Palette validated for CVD/contrast: TOON #DC5C05, JSON #1672EB on white.
"""
import csv, statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"; OUT = ROOT / "charts"
FONT = "Inter, 'SF Pro Text', -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
INK, INK2, MUTED, GRID, SURF = "#1F2123", "#4F5257", "#6D7178", "#E4E5E6", "#FFFFFF"
TOON, JSONC, DIM = "#DC5C05", "#1672EB", "#B4B6BC"
MAPS, TEXTP = "#8A38F5", "#20A34E"  # payload-type hues for fig 2 (not the TOON/JSON pair)
W = 960

def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;")
def text(x, y, s, size=13, fill=INK2, anchor="start", weight=400, extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" {extra}>{esc(s)}</text>'
def header(title, sub, y=34):
    return text(40, y, title, 20, INK, weight=600) + text(40, y + 24, sub, 13, MUTED)
def footer(h, note):
    return text(40, h - 16, note, 11, MUTED)
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
        out += f'<rect x="{cx}" y="{y - 9}" width="12" height="12" rx="2" fill="{color}"/>' + text(cx + 18, y + 1, label, 12, INK2)
        cx += 18 + 7 * len(label) + 24
    return out

# ---------------- Fig 1: the promise (spec fixture bytes) ----------------
def fig1():
    rows = [r for r in csv.DictReader(open(D / "spec-fixtures.csv")) if not r["tool"].startswith("combined")]
    combined = next(r for r in csv.DictReader(open(D / "spec-fixtures.csv")) if r["tool"].startswith("combined"))
    h = 420; top, left, right = 96, 250, 260
    plot_w = W - left - right; rowh = 48; barh = 22
    xmin, xmax = -50, 5
    def X(v): return left + (v - xmin) / (xmax - xmin) * plot_w
    b = header("What the proposal measured: TOON versus JSON, bytes, 18 fixtures",
               "Payload size change per MCP tool, negative means TOON is smaller. Spec of 2026-05-13; adaptive picker on captured API payloads.")
    for tick in (-50, -40, -30, -20, -10, 0):
        b += f'<line x1="{X(tick):.1f}" y1="{top - 8}" x2="{X(tick):.1f}" y2="{top + rowh * len(rows)}" stroke="{GRID if tick else INK2}" stroke-width="1"/>'
        b += text(X(tick), top + rowh * len(rows) + 18, f"{tick:+d}%" if tick else "0", 11, MUTED, "middle")
    for i, r in enumerate(rows):
        v = float(r["bytes_delta_pct_vs_json"]); y = top + i * rowh + (rowh - barh) / 2
        hot = r["tool"] == "dataset-items"
        b += rbar_h(X(0), X(v), y, barh, TOON if hot else JSONC)
        b += text(left - 14, y + barh / 2 + 4, r["tool"], 13, INK, "end", 600 if hot else 400)
        b += text(X(v) - 8, y + barh / 2 + 4, f"{v:+.1f}%", 12, INK, "end", 600)
    # callout on dataset-items
    yi = top + 4 * rowh + rowh / 2
    b += text(X(0) + 12, yi - 4, "carries most production traffic", 12, INK2, weight=600)
    b += text(X(0) + 12, yi + 12, "and saved about one percent", 12, INK2)
    b += text(40, top + rowh * len(rows) + 48,
              f"Combined across all 18 fixtures: {float(combined['bytes_delta_pct_vs_json']):+.1f}%. The picker chose TOON for 10 fixtures and JSON for 8.", 12, INK2)
    b += footer(h, "Source: res/toon_format_adoption.md in apify/apify-mcp-server (PR #836). Data and code: github.com/apify/toon-mcp-benchmark")
    (OUT / "fig1-spec-promise.svg").write_text(svg(h, b))

# ---------------- Fig 2: production reality (encoder-only token delta by rows) ----------------
def fig2():
    rows = list(csv.DictReader(open(D / "encoder-sweeps.csv")))
    series = {}
    for r in rows: series.setdefault(r["payload"], []).append((int(r["n_rows"]), float(r["tokens_delta_pct"]), int(r["toon_tokens"]), int(r["json_tokens"])))
    names = {"get-dataset-items · compact tabular (Google Maps)": "Google Maps places",
             "get-dataset-items · text-heavy (rag-web-browser)": "Web pages as text"}
    colors = {"get-dataset-items · compact tabular (Google Maps)": MAPS, "get-dataset-items · text-heavy (rag-web-browser)": TEXTP}
    ns = [1, 5, 10, 25, 50, 100]
    h = 470; top, left, right, bottom = 126, 70, 300, 70
    plot_w, plot_h = W - left - right, h - top - bottom
    ymin, ymax = -5, 20
    def X(n): return left + ns.index(n) / (len(ns) - 1) * plot_w
    def Y(v): return top + (ymax - v) / (ymax - ymin) * plot_h
    b = header("What the shipped encoder did: tokens, TOON versus JSON, by rows returned",
               "Token count change when the same dataset items are encoded as TOON instead of JSON. Positive means TOON costs more.")
    b += text(40, 80, "Google Maps places are nested objects with about 60 fields each; web pages are long text from rag-web-browser. Tokenizer: gpt-tokenizer, o200k_base.", 12, MUTED)
    for tick in (-5, 0, 5, 10, 15, 20):
        b += f'<line x1="{left}" y1="{Y(tick):.1f}" x2="{left + plot_w}" y2="{Y(tick):.1f}" stroke="{GRID if tick else INK2}" stroke-width="1"/>'
        b += text(left - 10, Y(tick) + 4, f"{tick:+d}%" if tick else "0", 11, MUTED, "end")
    for n in ns:
        b += text(X(n), top + plot_h + 20, str(n), 11, MUTED, "middle")
    b += text(left + plot_w / 2, top + plot_h + 40, "dataset items returned by one tool call", 12, MUTED, "middle")
    for key, pts in series.items():
        pts.sort(); c = colors[key]
        d = " ".join(f"{'M' if i == 0 else 'L'}{X(n):.1f},{Y(v):.1f}" for i, (n, v, _, _) in enumerate(pts))
        b += f'<path d="{d}" fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
        for n, v, _, _ in pts: b += dot(X(n), Y(v), c, 4)
        n, v, tt, tj = pts[-1]
        b += text(X(n) + 14, Y(v) + 4, f"{v:+.1f}%  {names[key]}", 12, INK, weight=600)
        b += text(X(n) + 14, Y(v) + 20, f"{tt:,} vs {tj:,} tokens at {n} rows", 11, MUTED)
    b += legend(left, top - 14, [("Google Maps places", MAPS), ("Web pages as text", TEXTP)])
    b += footer(h, "Source: toon_encoding_results.json, branch feat/evaluate-toon-format of apify/apify-mcp-server. Data: github.com/apify/toon-mcp-benchmark")
    (OUT / "fig2-encoder-tokens.svg").write_text(svg(h, b))

# ---------------- Fig 3: the A/B noise ----------------
def fig3():
    a = list(csv.DictReader(open(D / "execution-a-runs.csv"))); bb = list(csv.DictReader(open(D / "execution-b-runs.csv")))
    def runs(rows, fmt, total_key=None, total=None):
        sel = [r for r in rows if r["format"] == fmt]
        return [(int(r["pass_count"]), int(r[total_key]) if total_key else total) for r in sel], sel
    exec_a = {"toon": runs(a, "toon", "test_count")[0], "json": runs(a, "json", "test_count")[0]}
    exec_b = {"toon": [(int(r["pass_count"]), int(r["pass_count"]) + int(r["fail_count"]) + int(r["error_count"])) for r in bb if r["format"] == "toon"],
              "json": [(int(r["pass_count"]), int(r["pass_count"]) + int(r["fail_count"]) + int(r["error_count"])) for r in bb if r["format"] == "json"]}
    def totals(rows, fmt, key): return sum(int(r[key]) for r in rows if r["format"] == fmt)
    da_b = totals(a, "toon", "total_bytes") / totals(a, "json", "total_bytes") - 1
    da_t = totals(a, "toon", "total_tokens") / totals(a, "json", "total_tokens") - 1
    db_b = totals(bb, "toon", "total_bytes") / totals(bb, "json", "total_bytes") - 1
    db_t = totals(bb, "toon", "total_tokens") / totals(bb, "json", "total_tokens") - 1
    h = 560; left, right = 250, 330; plot_w = W - left - right
    def X(p): return left + p * plot_w
    b = header("Two A/B rounds, two signs: per-run pass rate of the same agent on TOON and JSON",
               "Each dot is one full run of the test suite. Agent: Claude Haiku 4.5. Judge: DeepSeek V4 Flash. Live Actor output varies between runs.")
    def panel(y0, title, sub, ex, dbytes, dtok):
        out = text(40, y0, title, 14, INK, weight=600) + text(40, y0 + 18, sub, 12, MUTED)
        base = y0 + 44
        for tick in (0, 0.25, 0.5, 0.75, 1.0):
            out += f'<line x1="{X(tick):.1f}" y1="{base - 6}" x2="{X(tick):.1f}" y2="{base + 2 * 44}" stroke="{GRID}" stroke-width="1"/>'
            out += text(X(tick), base + 2 * 44 + 16, f"{int(tick * 100)}%", 11, MUTED, "middle")
        for j, (fmt, color, label) in enumerate((("toon", TOON, "TOON"), ("json", JSONC, "JSON"))):
            y = base + j * 44 + 16
            pts = ex[fmt]; rates = [p / t for p, t in pts]; mean = st.mean(rates)
            out += text(left - 14, y + 4, label, 13, INK, "end", 600)
            out += f'<line x1="{X(mean):.1f}" y1="{y - 12}" x2="{X(mean):.1f}" y2="{y + 12}" stroke="{color}" stroke-width="2"/>'
            for (p, t), dy in zip(pts, jitter([p / t for p, t in pts])): out += dot(X(p / t), y + dy, color, 5)
            out += text(X(1.0) + 14, y + 4, f"mean {mean * 100:.0f}%   runs: {', '.join(str(p) for p, _ in pts)} of {pts[0][1]}", 11, INK2)
        out += text(40, base + 2 * 44 + 42,
                    f"Suite totals, TOON versus JSON: bytes {dbytes * 100:+.1f}%, agent tokens {dtok * 100:+.1f}%, pass rate {(st.mean([p / t for p, t in ex['toon']]) - st.mean([p / t for p, t in ex['json']])) * 100:+.1f} points.", 12, INK2, weight=600)
        return out
    b += panel(96, "Round 1 · 5 runs × 20 tasks across search, call, MCP, fetch and storage tools · June 2026",
               "Six of the 20 tasks never touch a TOON-encoded tool.", exec_a, da_b, da_t)
    b += panel(330, "Round 2 · 3 runs × 16 storage tasks, after tool descriptions told agents to request only the fields they need",
               "Seven of the 16 tasks pull real scraped data: Google Maps, hotels, Google Search, Instagram, TikTok, YouTube, Reddit.", exec_b, db_b, db_t)
    b += footer(h, "Source: toon_ab_run.log and toon_ab_results.json, branch feat/evaluate-toon-format of apify/apify-mcp-server. Data: github.com/apify/toon-mcp-benchmark")
    (OUT / "fig3-ab-noise.svg").write_text(svg(h, b))

if __name__ == "__main__":
    fig1(); fig2(); fig3()
    for f in sorted(OUT.glob("fig*.svg")): print(f.name, f.stat().st_size, "bytes")
