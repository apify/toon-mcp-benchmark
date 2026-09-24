/* eslint-disable no-console */
/**
 * Re-run of the encoder-only TOON vs JSON measurement on fresh Apify data, end to end.
 *
 * Spawns the real stdio server at this commit twice (TOON on, then APIFY_MCP_DISABLE_TOON=1),
 * calls the five TOON-encoded tools with identical arguments, and counts UTF-8 bytes and
 * o200k_base tokens (gpt-tokenizer, same as toon_encoding_measure.ts) of content[0].text,
 * the block encodeToon produces. Also reports the full text the model receives (all text blocks).
 *
 * From the TOON run's structuredContent it additionally computes the proposal's metric
 * (adaptive picker: min bytes of JSON.stringify vs encode(dotFlatten(x)), no fence) and
 * a no-flatten TOON variant, to separate the effect of dot-flattening.
 *
 * Usage: MAPS=<datasetId> RAG=<datasetId> KVS=<storeId> pnpm exec tsx repro/measure_e2e.ts
 */
import fs from 'node:fs';

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { encode as toonEncode } from '@toon-format/toon';
import { encode as tokenize } from 'gpt-tokenizer/model/gpt-4o';

import { dotFlatten } from '../src/utils/encode_text.js';

const { MAPS, RAG, KVS } = process.env;
if (!MAPS || !RAG || !KVS) throw new Error('Set MAPS, RAG, KVS');

const TOOLS = [
    'get-dataset-items',
    'get-actor-run-list',
    'get-key-value-store-keys',
    'get-dataset-list',
    'get-key-value-store-list',
];

type Call = { label: string; tool: string; args: Record<string, unknown> };
const calls: Call[] = [
    ...[1, 5, 10, 25, 50, 100].map((n) => ({
        label: `maps n=${n}`,
        tool: 'get-dataset-items',
        args: { datasetId: MAPS, limit: n },
    })),
    ...[1, 5, 10, 15].map((n) => ({
        label: `rag n=${n}`,
        tool: 'get-dataset-items',
        args: { datasetId: RAG, limit: n },
    })),
    { label: 'run-list n=10', tool: 'get-actor-run-list', args: { limit: 10, desc: true } },
    { label: 'kv-keys', tool: 'get-key-value-store-keys', args: { keyValueStoreId: KVS } },
    { label: 'dataset-list n=10', tool: 'get-dataset-list', args: { limit: 10, desc: true } },
    { label: 'kvs-list n=10', tool: 'get-key-value-store-list', args: { limit: 10, desc: true } },
];

type Out = { data: string; all: string; sc: unknown };

async function runArm(format: 'toon' | 'json'): Promise<Record<string, Out>> {
    const env: Record<string, string> = { ...(process.env as Record<string, string>) };
    if (format === 'json') env.APIFY_MCP_DISABLE_TOON = '1';
    else delete env.APIFY_MCP_DISABLE_TOON;
    const transport = new StdioClientTransport({
        command: 'pnpm',
        args: ['exec', 'tsx', 'src/stdio.ts', `--tools=${TOOLS.join(',')}`, '--telemetry-enabled=false'],
        env,
    });
    const client = new Client({ name: 'toon-repro', version: '1.0.0' }, { capabilities: {} });
    await client.connect(transport);
    const out: Record<string, Out> = {};
    for (const c of calls) {
        const res = (await client.callTool({ name: c.tool, arguments: c.args })) as {
            content: { type: string; text?: string }[];
            structuredContent?: unknown;
            isError?: boolean;
        };
        if (res.isError) throw new Error(`${c.label}: ${JSON.stringify(res.content)}`);
        const texts = res.content.filter((b) => b.type === 'text').map((b) => b.text ?? '');
        out[c.label] = { data: texts[0], all: texts.join('\n'), sc: res.structuredContent };
    }
    await client.close();
    return out;
}

const bytes = (s: string) => Buffer.byteLength(s, 'utf8');
const toks = (s: string) => tokenize(s).length;
const pct = (t: number, j: number) => ((t - j) / j) * 100;

const toon = await runArm('toon');
const json = await runArm('json');

const rows = calls.map(({ label }) => {
    const t = toon[label];
    const j = json[label];
    // Sanity: the TOON arm must actually be TOON and the JSON arm JSON.
    if (!t.data.startsWith('```toon\n')) throw new Error(`${label}: TOON arm is not TOON: ${t.data.slice(0, 20)}`);
    if (!j.data.startsWith('```json\n')) throw new Error(`${label}: JSON arm is not JSON: ${j.data.slice(0, 20)}`);
    // Proposal metric on the payload encodeToon received (structuredContent minus summary/nextStep).
    const { summary: _s, nextStep: _n, ...payload } = (t.sc ?? {}) as Record<string, unknown>;
    const jsonBare = JSON.stringify(payload);
    const toonFlatBare = toonEncode(dotFlatten(payload) as never);
    const toonPlainBare = toonEncode(payload as never);
    const picker = bytes(toonFlatBare) < bytes(jsonBare) ? toonFlatBare : jsonBare;
    return {
        label,
        dataBytesT: bytes(t.data),
        dataBytesJ: bytes(j.data),
        dataTokT: toks(t.data),
        dataTokJ: toks(j.data),
        allTokT: toks(t.all),
        allTokJ: toks(j.all),
        pickerBytesPct: pct(bytes(picker), bytes(jsonBare)),
        pickerChoice: picker === jsonBare ? 'json' : 'toon-flatten',
        toonFlatBytesPct: pct(bytes(toonFlatBare), bytes(jsonBare)),
        toonFlatTokPct: pct(toks(toonFlatBare), toks(jsonBare)),
        toonPlainBytesPct: pct(bytes(toonPlainBare), bytes(jsonBare)),
        toonPlainTokPct: pct(toks(toonPlainBare), toks(jsonBare)),
        prettyJsonTokPct: pct(toks(JSON.stringify(payload, null, 2)), toks(jsonBare)),
    };
});

const f = (n: number) => `${n >= 0 ? '+' : ''}${n.toFixed(1)}%`;
console.log(
    'payload'.padEnd(20) +
        'JSON B'.padStart(9) +
        'TOON B'.padStart(9) +
        'ΔB'.padStart(8) +
        'JSON tok'.padStart(10) +
        'TOON tok'.padStart(10) +
        'Δtok'.padStart(8) +
        'Δtok all'.padStart(9) +
        '  | picker ΔB  flatTOON ΔB/Δtok  plainTOON ΔB/Δtok',
);
for (const r of rows) {
    console.log(
        r.label.padEnd(20) +
            String(r.dataBytesJ).padStart(9) +
            String(r.dataBytesT).padStart(9) +
            f(pct(r.dataBytesT, r.dataBytesJ)).padStart(8) +
            String(r.dataTokJ).padStart(10) +
            String(r.dataTokT).padStart(10) +
            f(pct(r.dataTokT, r.dataTokJ)).padStart(8) +
            f(pct(r.allTokT, r.allTokJ)).padStart(9) +
            `  | ${f(r.pickerBytesPct).padStart(7)} (${r.pickerChoice})  ${f(r.toonFlatBytesPct)}/${f(r.toonFlatTokPct)}  ${f(r.toonPlainBytesPct)}/${f(r.toonPlainTokPct)}`,
    );
}

fs.mkdirSync('repro/out', { recursive: true });
fs.writeFileSync('repro/out/results.json', JSON.stringify({ tokenizer: 'o200k_base (gpt-4o)', rows }, null, 2));
fs.writeFileSync('repro/out/raw_texts.json', JSON.stringify({ toon, json }, null, 2));
console.log('\nwrote repro/out/results.json, repro/out/raw_texts.json');
