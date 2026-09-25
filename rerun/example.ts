/* eslint-disable no-console */
import fs from 'node:fs';
import { encode } from '@toon-format/toon';
import { encode as tokenize } from 'gpt-tokenizer/model/gpt-4o';
const d = JSON.parse(fs.readFileSync('repro/out/raw_texts.json', 'utf8'));
const runs = d.json['run-list n=10'].sc.items.slice(0, 3).map((r: any) => ({ id: r.id, status: r.status, startedAt: r.startedAt, usageTotalUsd: +r.usageTotalUsd.toFixed(4) }));
const pretty = JSON.stringify(runs, null, 2), compact = JSON.stringify(runs), toon = encode(runs);
for (const [n, s] of [['pretty', pretty], ['compact', compact], ['toon', toon]] as const) console.log(`--- ${n}: ${Buffer.byteLength(s)} bytes, ${tokenize(s).length} tokens\n${s}`);
