# Provenance

All raw files in `data/raw/` are byte-identical copies of blobs in the public repository
[apify/apify-mcp-server](https://github.com/apify/apify-mcp-server), extracted with `git show <ref>:<path>`
on 2026-09-10. None of them ever reached the `master` branch.

| File | Source ref | Path in source repo | Commit that added it |
|---|---|---|---|
| `toon_format_adoption.md` | `feat/toon-format-benchmark` @ `78e5bb5f` | `res/toon_format_adoption.md` | `78e5bb5f` (2026-05-13, PR #836, closed unmerged; refiled as issue #913) |
| `toon_ab_eval.ts` | `feat/evaluate-toon-format` @ `9417a220` | `evals/workflows/toon_ab_eval.ts` | `e3c28bec` (2026-06-25) |
| `toon_encoding_measure.ts` | same | `evals/workflows/toon_encoding_measure.ts` | `e3c28bec` (2026-06-25) |
| `toon_ab_run.log` | same | `evals/workflows/toon_ab_run.log` | `9417a220` (2026-06-26) |
| `toon_ab_analysis.json` | same | `evals/workflows/toon_ab_analysis.json` | `9417a220` (2026-06-26) |
| `toon_ab_results.json` | same | `evals/workflows/toon_ab_results.json` | `9417a220` (2026-06-26) |
| `toon_encoding_results.json` | same | `evals/workflows/toon_encoding_results.json` | `9417a220` (2026-06-26) |
| `test_cases.json` | same | `evals/workflows/test_cases.json` | cumulative; storage cases from `6b55e2bc`, `ae9b6404` |
| `evals_README.md` | same | `evals/workflows/README.md` | documents the `APIFY_MCP_DISABLE_TOON` A/B recipe |

## Timeline of the TOON episode in apify-mcp-server

| Date | Event |
|---|---|
| 2026-05-13 | Spec proposes an adaptive JSON-or-TOON picker based on 18 fixtures (PR #836) |
| 2026-06-09 | PRs #950 + #952 ship always-TOON encoding for five list tools (`@toon-format/toon@2.3.0`) |
| 2026-06-16 to 06-26 | Evaluation work on `feat/evaluate-toon-format`: byte and token metrics, A/B switch, two A/B executions, encoder-only measurement |
| 2026-06-25 | Gate issue #943 ("does TOON degrade MCP task performance?") closed |
| 2026-06-29 | PR #1031 lands byte/token cost metrics on master; TOON scaffolding and these result files excluded |
| 2026-07-09 | PR #1060 removes TOON (16 files, +23 / −308) |

## What each measurement is

### Spec fixtures (`toon_format_adoption.md`)
18 payloads: 15 captured from the live Apify API, 3 synthetic (the test account had no storages with a user-declared schema).
Metric: UTF-8 bytes. Compared `json` (`JSON.stringify`) against `toon-flatten` (dot-flatten nested keys, then TOON-encode).
The fixture files themselves were never committed.

### Encoder-only measurement (`toon_encoding_results.json`)
Deterministic: no agent, no live calls. Encodes fixture payloads with the *shipped* `encodeToon` (always TOON, dot-flatten,
markdown fence) and with `JSON.stringify`, then counts bytes and tokens.
Tokenizer: `gpt-tokenizer` 3.4.x, encoding `o200k_base` (GPT-4o). This is a proxy; the agent model in the A/B runs was Claude Haiku 4.5, whose tokenizer differs.
**Not reproducible:** `toon_encoding_measure.ts` reads its fixtures from an absolute scratchpad path on the author's machine
(`maps_items.json`, `rag_items.json`, `kvs_keys.json`, `run_list.json`), and those files were never committed. The results JSON is the only record.

### Execution A (`toon_ab_run.log`, `toon_ab_analysis.json`)
End-to-end A/B with a live agent: 5 runs per format × 20 test cases across categories search/call/mcp/fetch/storage, concurrency 8.
Agent `anthropic/claude-haiku-4.5`, LLM judge `deepseek/deepseek-v4-flash`, via OpenRouter.
Bytes = UTF-8 bytes of tool results fed to the agent. Tokens = agent prompt + completion tokens as billed (judge excluded).
Six of the 20 tests never call a TOON-encoded tool, so their bytes are identical between arms and dilute the suite-wide average.
`toon_ab_analysis.json` has no generating script in the repo; it was produced ad hoc from the same run. Its `toonSd`/`jsonSd`
are population standard deviations (4.12 / 3.2); `parse.py` prints sample standard deviations (4.6 / 3.58).

### Execution B (`toon_ab_results.json`)
Same harness, 3 runs per format × 16 storage-category tests, concurrency 2, after the tool descriptions were changed to push
agents to request only the fields they need (`2e639fba`). Ran after Execution A (it includes test cases added on 2026-06-26).
`rawRuns` carries per-test prompt/completion token splits, turns and duration.

## Caveats that travel with the data
- Live Actor output varies between calls, so unseeded tests are not strictly paired between arms.
- Pass/fail comes from an LLM judge; per-run pass counts in Execution A swing between 8 and 18 out of 20.
- The two A/B executions differ in sign on every headline metric. Quote them separately.
- Encoder-only tokens are GPT-4o tokenizer counts; A/B tokens are Claude Haiku 4.5 billing counts. Do not mix them.
- Identifiers in the data are public Actor names and public social handles used as scrape targets. No credentials, no personal data.

## License
Code in this repository: MIT (`LICENSE`). Data files under `data/`: CC BY 4.0 (`LICENSE-DATA`). Attribution: Apify, apify/apify-mcp-server contributors.
