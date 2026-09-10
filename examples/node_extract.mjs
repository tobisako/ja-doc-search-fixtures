#!/usr/bin/env node
// 検査に使う抽出コマンドの例（Node）。
//     ../check.py --cmd "node examples/node_extract.mjs {file}"
// 読めないときは空文字を出さず、終了コード1で終えること。
import { readFileSync } from 'node:fs';
try {
  const { extractText, getDocumentProxy } = await import('unpdf');
  const pdf = await getDocumentProxy(new Uint8Array(readFileSync(process.argv[2])));
  const { text } = await extractText(pdf, { mergePages: true });
  const merged = Array.isArray(text) ? text.join('\n') : text;
  if (!merged.trim()) process.exit(1);
  console.log(merged);
} catch {
  process.exit(1);
}
