// Re-encodes the payloads captured by measure_e2e.ts with the current TOON release (4.1.1),
// using the same dot-flatten transform and markdown fence as the shipped encoder.
// Usage (in a directory with @toon-format/toon@4.1.1 and gpt-tokenizer@3.4.0 installed):
//   node toon_v4_check.mjs <path to raw_texts.json from measure_e2e.ts>
import fs from 'node:fs';

import { encode } from '@toon-format/toon';
import { encode as tokenize } from 'gpt-tokenizer/model/gpt-4o';

// Port of dotFlatten from apify-mcp-server@9417a220 src/utils/encode_text.ts.
const MAX_DEPTH = 20;

function flattenValue(value, depth) {
    if (depth > MAX_DEPTH) throw new RangeError('dotFlatten: max depth exceeded');
    if (Array.isArray(value)) return value.map((item) => flattenValue(item, depth + 1));
    if (value !== null && typeof value === 'object') {
        const out = Object.create(null);
        flattenInto(value, '', depth, out);
        return out;
    }
    return value;
}

function flattenInto(obj, prefix, depth, out) {
    if (depth > MAX_DEPTH) throw new RangeError('dotFlatten: max depth exceeded');
    for (const [rawKey, v] of Object.entries(obj)) {
        const key = prefix ? `${prefix}.${rawKey.replaceAll('.', '_')}` : rawKey.replaceAll('.', '_');
        if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
            flattenInto(v, key, depth + 1, out);
        } else {
            if (key in out) throw new RangeError(`dotFlatten: key collision on "${key}"`);
            out[key] = flattenValue(v, depth + 1);
        }
    }
}

const bytes = (s) => Buffer.byteLength(s, 'utf8');
const toks = (s) => tokenize(s).length;
const pct = (t, j) => +(((t - j) / j) * 100).toFixed(2);

const raw = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const rows = Object.entries(raw.toon).map(([label, arm]) => {
    const { summary: _summary, nextStep: _nextStep, ...payload } = arm.sc;
    const jsonText = `\`\`\`json\n${JSON.stringify(payload)}\n\`\`\``;
    const flatText = `\`\`\`toon\n${encode(flattenValue(JSON.parse(JSON.stringify(payload)), 0))}\n\`\`\``;
    const plainText = `\`\`\`toon\n${encode(payload)}\n\`\`\``;
    return {
        label,
        flatFenceBytesPct: pct(bytes(flatText), bytes(jsonText)),
        flatFenceTokPct: pct(toks(flatText), toks(jsonText)),
        plainFenceBytesPct: pct(bytes(plainText), bytes(jsonText)),
        plainFenceTokPct: pct(toks(plainText), toks(jsonText)),
        // The live JSON arm (APIFY_MCP_DISABLE_TOON=1) must equal this reconstruction.
        jsonArmMatchesReconstruction: raw.json[label].data === jsonText,
    };
});

console.log(JSON.stringify({ toonVersion: '4.1.1', tokenizer: 'o200k_base (gpt-4o)', rows }, null, 2));
