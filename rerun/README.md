# Encoder re-run on fresh data (September 24, 2026)

The June encoder-only measurement (`data/raw/toon_encoding_results.json`) could not be re-run because its fixture files were never committed. This folder re-runs it on fresh Apify data, end to end through the real server.

## What was run

- **Server:** `apify/apify-mcp-server` at `9417a220` (branch `feat/evaluate-toon-format`). It has the shipped encoder (`@toon-format/toon@2.3.0`, dot-flatten, markdown fence) plus the `APIFY_MCP_DISABLE_TOON` switch used by the A/B harness.
- **Arms:** the stdio server is spawned twice, once with TOON on and once with `APIFY_MCP_DISABLE_TOON=1`. Both arms get identical tool calls. The JSON arm is `JSON.stringify` in a ```` ```json ```` fence, as in June.
- **Metric:** UTF-8 bytes and `o200k_base` tokens (`gpt-tokenizer@3.4.0`, as in June) of `content[0].text`, the block the encoder produces.
- **Data:**
  - Google Maps: `compass/crawler-google-places` with `{"searchStringsArray":["restaurant"],"locationQuery":"Prague, Czechia","maxCrawledPlacesPerSearch":100,"language":"en"}`. 100 places, 59 to 62 top-level fields each.
  - Web pages: `apify/rag-web-browser` with `{"query":"best open source web scraping libraries","maxResults":15}`. 15 items.
  - Also the account's 10 latest Actor runs, datasets and key-value stores, and one run's key-value store keys (3 keys).
- **Not committed:** the raw payloads. They are third-party web content and account data.

## Results

TOON versus JSON (positive means TOON is larger):

| Payload | Bytes | Tokens | June tokens |
|---|---:|---:|---:|
| Google Maps, 1 place | +17.9% | +21.5% | +18.9% |
| Google Maps, 5 places | +14.3% | +15.0% | +9.5% |
| Google Maps, 10 places | +12.5% | +12.7% | +9.8% |
| Google Maps, 25 places | +12.2% | +11.1% | +12.2% |
| Google Maps, 50 places | +12.7% | +12.6% | +12.1% |
| Google Maps, 100 places | +11.9% | +11.7% | +11.1% |
| Web pages, 15 items | +1.9% | +1.4% | +0.6% (15 real pages) |
| Actor run list, 10 runs | −44.0% | −23.0% | +9.5% |
| Dataset list, 10 | −46.2% | −29.0% | not measured |
| Key-value store list, 10 | +12.7% | +15.9% | not measured |
| Key-value store keys | −15.4% | −7.6% | −5.9% (4 keys) |

Full numbers: `results/encoder-2.3.0.json`.

What it shows:

1. **Google Maps places cost about 11 to 12% more tokens as TOON at every row count.** This confirms the June result.
2. **TOON never produced a table for Google Maps places.** Each place has array fields (`categories`, `openingHours`, …) and a varying key set, so TOON writes all 100 places in indented list form, one `key: value` line per field.
   - Of the 18,796 extra tokens on the 100-place payload, 11,369 (60%) are indentation (`results/maps-overhead.txt`).
   - Only 921 values needed quoting.
   - Plain TOON without dot-flattening costs +9.7% tokens. Dot-flattening adds about 2 points by making repeated keys longer (`reviewsDistribution.oneStar`).
3. **List tools shrink, but tokens shrink about half as much as bytes.** The run list is −44% bytes but only −23% tokens.
4. **The run-list result depends on row uniformity.** In June the 10-run fixture came out +9.5% tokens. Here, with uniform rows, it is −23%.
5. **The current TOON release gives the same numbers.** Re-encoding with `@toon-format/toon@4.1.1` changes no dot-flattened result by more than 0.1 point (`results/encoder-4.1.1.json`).

## Reproduce

```bash
git -C apify-mcp-server worktree add ../toon-repro 9417a220 && cd ../toon-repro
pnpm install --frozen-lockfile
mkdir repro && cp <this folder>/measure_e2e.ts <this folder>/why_maps.ts repro/
# run the two Actors above, then:
APIFY_TOKEN=... MAPS=<maps datasetId> RAG=<rag datasetId> KVS=<keyValueStoreId> pnpm exec tsx repro/measure_e2e.ts
pnpm exec tsx repro/why_maps.ts
# TOON 4.1.1 check, in a directory with @toon-format/toon@4.1.1 and gpt-tokenizer@3.4.0:
node toon_v4_check.mjs ../toon-repro/repro/out/raw_texts.json
```

Live Actor output changes over time, so exact numbers will differ. The Google Maps runs cost $0.40 and the web-page run $0.01 on the free tier.
