/* eslint-disable no-console */
// Attribute the Google Maps TOON overhead: indentation/newlines vs quoting vs key repetition.
import fs from 'node:fs';
import { encode as tokenize } from 'gpt-tokenizer/model/gpt-4o';
const d = JSON.parse(fs.readFileSync('repro/out/raw_texts.json', 'utf8'));
const toon: string = d.toon['maps n=100'].data;
const json: string = d.json['maps n=100'].data;
const t = (s: string) => tokenize(s).length;
const T = t(toon), J = t(json);
const lines = toon.split('\n');
const noIndent = lines.map((l) => l.replace(/^ +/, '')).join('\n');
const quoted = (toon.match(/: "/g) ?? []).length;
const fieldLines = lines.filter((l) => /^\s+(- )?[^\s:][^:]*: /.test(l)).length;
console.log({ jsonTok: J, toonTok: T, deltaTok: T - J, deltaPct: (((T - J) / J) * 100).toFixed(1) });
console.log({ lines: lines.length, fieldLines, quotedValues: quoted });
console.log({ tokWithoutIndentation: t(noIndent), indentationTokens: T - t(noIndent) });
