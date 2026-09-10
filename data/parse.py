#!/usr/bin/env python3
"""Parse the raw TOON evaluation artifacts from apify/apify-mcp-server
(branch feat/evaluate-toon-format @ 9417a220) into flat CSVs.

Usage: python3 data/parse.py   (run from the repo root)
Outputs: data/execution-a.csv, data/execution-a-runs.csv, data/execution-b.csv,
         data/execution-b-runs.csv, data/encoder-rows.csv, data/encoder-sweeps.csv,
         data/spec-fixtures.csv
"""
import csv, json, re, statistics as st
from pathlib import Path

RAW = Path(__file__).parent / "raw"
OUT = Path(__file__).parent

def w(name, rows, header):
    with open(OUT / name, "w", newline="") as f:
        cw = csv.writer(f); cw.writerow(header); cw.writerows(rows)
    print(f"{name}: {len(rows)} rows")

# --- Execution A: toon_ab_run.log (5 runs x 2 formats x 20 tests) ---
line_re = re.compile(r"\[run (\d+) · (TOON|JSON)\] (✅|❌|🔥) \d+/20 (\S+) \((\d+) B, (\d+) tok\)")
total_re = re.compile(r"run (\d+) · (TOON|JSON) done: (\d+)/20 pass · (\d+) B · (\d+) tok · (\d+)s")
rows_a, runs_a = [], []
verdict_map = {"✅": "PASS", "❌": "FAIL", "🔥": "ERROR"}
for line in open(RAW / "toon_ab_run.log", encoding="utf-8"):
    m = line_re.search(line)
    if m:
        run, fmt, v, test, b, t = m.groups()
        rows_a.append([int(run), fmt.lower(), test, verdict_map[v], int(b), int(t)])
        continue
    m = total_re.search(line)
    if m:
        run, fmt, p, b, t, s = m.groups()
        runs_a.append([int(run), fmt.lower(), int(p), 20, int(b), int(t), int(s)])
w("execution-a.csv", rows_a, ["run", "format", "test_id", "verdict", "result_bytes", "total_tokens"])
if not runs_a:  # derive per-run totals if the log has no summary lines
    agg = {}
    for run, fmt, test, v, b, t in rows_a:
        a = agg.setdefault((run, fmt), [0, 0, 0, 0])
        a[0] += v == "PASS"; a[1] += 1; a[2] += b; a[3] += t
    runs_a = [[r, f, *v, ""] for (r, f), v in sorted(agg.items())]
w("execution-a-runs.csv", runs_a, ["run", "format", "pass_count", "test_count", "total_bytes", "total_tokens", "duration_s"])

# --- Execution B: toon_ab_results.json rawRuns (3 runs x 2 formats x 16 tests) ---
d = json.load(open(RAW / "toon_ab_results.json"))
rows_b, runs_b = [], []
for r in d["rawRuns"]:
    runs_b.append([r["run"], r["format"], r["passCount"], r["failCount"], r["errorCount"], r["totalBytes"],
                   r["totalTokens"], r["totalPromptTokens"], r["totalCompletionTokens"], r["durationMs"]])
    for o in r["outcomes"]:
        rows_b.append([r["run"], r["format"], o["testId"], o["category"], o["verdict"], o["resultBytes"],
                       o["promptTokens"], o["completionTokens"], o["totalTokens"], o["turns"], o["durationMs"]])
w("execution-b.csv", rows_b, ["run", "format", "test_id", "category", "verdict", "result_bytes", "prompt_tokens",
                             "completion_tokens", "total_tokens", "turns", "duration_ms"])
w("execution-b-runs.csv", runs_b, ["run", "format", "pass_count", "fail_count", "error_count", "total_bytes",
                                  "total_tokens", "prompt_tokens", "completion_tokens", "duration_ms"])

# --- Encoder-only measurement ---
e = json.load(open(RAW / "toon_encoding_results.json"))
rows_e = [[r["label"], r["rows"], r["bytesT"], r["bytesJ"], r["tokT"], r["tokJ"],
           round(100 * (r["bytesT"] / r["bytesJ"] - 1), 2), round(100 * (r["tokT"] / r["tokJ"] - 1), 2)] for r in e["rows"]]
w("encoder-rows.csv", rows_e, ["payload", "rows", "toon_bytes", "json_bytes", "toon_tokens", "json_tokens",
                              "bytes_delta_pct", "tokens_delta_pct"])
rows_s = [[label, s["n"], s["toonTok"], s["jsonTok"], round(s["bytesDeltaPct"], 3), round(s["tokDeltaPct"], 3)]
          for label, sw in e["sweeps"].items() for s in sw]
w("encoder-sweeps.csv", rows_s, ["payload", "n_rows", "toon_tokens", "json_tokens", "bytes_delta_pct", "tokens_delta_pct"])
print("tokenizer:", e["tokenizer"])

# --- Spec fixture table (hand-transcribed from toon_format_adoption.md headline table) ---
spec = [["get-actor-run-list", -44.0, "toon-flatten"], ["get-dataset-list", -31.6, "toon-flatten (mixed-schema: json)"],
        ["get-key-value-store-list", -31.3, "toon-flatten (mixed-schema: json)"], ["get-key-value-store-keys", -19.0, "toon-flatten"],
        ["dataset-items", -1.2, "depends on the Actor"], ["combined (18 fixtures)", -6.2, "toon-flatten 10/18, json 8/18"]]
w("spec-fixtures.csv", spec, ["tool", "bytes_delta_pct_vs_json", "winning_strategy"])

# --- Sanity aggregates (printed, compared against the committed summary blocks) ---
def agg(rows, fmt, bi, ti, vi):
    sel = [r for r in rows if r[1] == fmt]
    return sum(r[bi] for r in sel), sum(r[ti] for r in sel), sum(r[vi] == "PASS" for r in sel), len(sel)
for name, rows, bi, ti, vi, nruns in [("A", rows_a, 4, 5, 3, 5), ("B", rows_b, 5, 8, 4, 3)]:
    tb, tt, tp, n = agg(rows, "toon", bi, ti, vi); jb, jt, jp, _ = agg(rows, "json", bi, ti, vi)
    print(f"Exec {name}: bytes/run TOON {tb/nruns:.0f} JSON {jb/nruns:.0f} Δ {100*(tb/jb-1):+.2f}% | "
          f"tokens/run TOON {tt/nruns:.0f} JSON {jt/nruns:.0f} Δ {100*(tt/jt-1):+.2f}% | "
          f"pass TOON {100*tp/n:.1f}% JSON {100*jp/n:.1f}%")
pa = {f: [r[2] for r in runs_a if r[1] == f] for f in ("toon", "json")}
print("Exec A per-run passes:", pa, "sd:", {f: round(st.stdev(v), 2) for f, v in pa.items()})
print("committed A summary:", json.load(open(RAW / "toon_ab_analysis.json")).get("accuracy"))
print("committed B comparison:", d["comparison"])
