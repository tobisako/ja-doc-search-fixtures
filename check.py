#!/usr/bin/env python3
"""
自分の抽出処理を fixtures に通して、日本語の取りこぼしを検査する。

**言語を問いません。** 「ファイルパスを受け取り、抽出したテキストを標準出力に出す」
コマンドさえあれば、Python でも Node でも Go でも検査できます。

    ./check.py --cmd "python3 my_extract.py {file}"
    ./check.py --cmd "node my_extract.mjs {file}"

抽出できなかったときは、**空文字を出さずに終了コード1で終えてください。**
それが「読めないと言えている」ことの合図になります。

依存はありません（標準ライブラリのみ）。このファイルごと自分のCIにコピーして構いません。
"""
import argparse, json, subprocess, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def cps(s):
    return ' '.join(f'U+{ord(c):04X}' for c in s)

def run_one(cmd_tmpl, path):
    """(text, failed) を返す。failed=True は「抽出できないと言えた」"""
    cmd = cmd_tmpl.replace('{file}', str(path))
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        return '', True
    if p.returncode != 0:
        return '', True
    return p.stdout.decode('utf-8', errors='replace'), False

def check(fx, text, failed):
    """期待どおりかを見る。問題のリストを返す（空なら合格）"""
    e, bad = fx['expect'], []

    if e.get('must_fail'):
        if not failed:
            bad.append(f"抽出できないはずが、成功して {len(text.strip())}文字返った"
                       + ("（空文字を成功として返している）" if not text.strip() else ""))
        return bad

    if failed:
        bad.append('抽出できるはずが、失敗した')
        return bad

    for w in e.get('must_find', []):
        if w not in text:
            # なぜ見つからないのかを言う。ここが一番効く
            nf = unicodedata.normalize('NFKC', text)
            hint = '（NFKC を掛ければ見つかる＝正規化されていない）' if w in nf else ''
            bad.append(f'「{w}」が見つからない{hint}')

    for w in e.get('must_keep', []):
        if w not in text:
            bad.append(f'「{w}」が保たれていない（NFKC で潰していないか）  {cps(w)}')

    for hexcp in e.get('must_not_contain_cp', []):
        ch = chr(int(hexcp, 16))
        if ch in text:
            bad.append(f'U+{hexcp} 「{ch}」がそのまま残っている（正規化されていない）')
    return bad

def main():
    ap = argparse.ArgumentParser(description='日本語ドキュメントの取りこぼしを検査する')
    ap.add_argument('--cmd', required=True,
                    help='抽出コマンド。{file} がファイルパスに置き換わる')
    ap.add_argument('--group', help='この分類だけ検査する（kangxi / zenkaku / dakuten / no-text / broken / encoding）')
    ap.add_argument('-q', '--quiet', action='store_true', help='合格したものを表示しない')
    args = ap.parse_args()

    spec = json.loads((ROOT / 'expected.json').read_text(encoding='utf-8'))
    fixtures = [f for f in spec['fixtures'] if not args.group or f['group'] == args.group]

    ok = 0
    ng = []
    for fx in fixtures:
        path = ROOT / 'fixtures' / fx['file']
        if not path.exists():
            print(f'  ! 見つからない: {fx["file"]}'); continue
        text, failed = run_one(args.cmd, path)
        bad = check(fx, text, failed)
        if bad:
            ng.append((fx, bad))
            print(f'✗ [{fx["group"]}] {fx["file"]}')
            for b in bad: print(f'      {b}')
            print(f'      → {fx["why"]}')
        else:
            ok += 1
            if not args.quiet: print(f'✓ [{fx["group"]}] {fx["file"]}')

    print(f'\n合格 {ok} / 不合格 {len(ng)}（全 {len(fixtures)}本）')
    if ng:
        print('\n落ちた分類:')
        by = {}
        for fx, _ in ng: by[fx['group']] = by.get(fx['group'], 0) + 1
        for g, n in sorted(by.items(), key=lambda x: -x[1]):
            print(f'  {g:<10} {n}本')
    return 1 if ng else 0

sys.exit(main())
