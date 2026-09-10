#!/usr/bin/env python3
"""
`expected.json` の `must_not_contain_cp` を、**実ファイルの中身から導く。**

【なぜ要るか】期待値を手で書くと、実ファイルと食い違う。
実際に踏んだ: K02 は U+2F2F と書いたが中身は U+2FA6 だった（＝素通りしていた）。
K04 は U+FA19 のつもりが Chrome が生成時に正規化して消していた。

**Chrome は日本語PDFを作るだけで、勝手に康熙部首を混ぜてくる。**
だから「何が入っているか」は、作った本人にも事前には分からない。実物から読む。

NFKC で直せないもの（U+2E8C など）は期待値に入れない。誰にも直せないため。
"""
import json, unicodedata as u, warnings
from pathlib import Path
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent

RANGES = [(0x2e80, 0x2eff), (0x2f00, 0x2fdf), (0xf900, 0xfaff), (0xfe30, 0xfe4f), (0xff61, 0xff9f)]

def read(path: Path) -> str:
    if path.suffix.lower() == '.pdf':
        try:
            import pypdf
            return ''.join(p.extract_text() or '' for p in pypdf.PdfReader(str(path)).pages)
        except Exception:
            return ''
    for enc in ('utf-8', 'cp932', 'euc_jp'):
        try:
            return path.read_bytes().decode(enc)
        except Exception:
            continue
    return ''

def scan(text):
    fixable, stuck = [], []
    for ch in text:
        c = ord(ch)
        if any(lo <= c <= hi for lo, hi in RANGES):
            key = f'{c:04X}'
            (fixable if u.normalize('NFKC', ch) != ch else stuck)
            if u.normalize('NFKC', ch) != ch:
                if key not in fixable: fixable.append(key)
            else:
                if key not in stuck: stuck.append(key)
    return sorted(fixable), sorted(stuck)

def main():
    p = ROOT / 'expected.json'
    d = json.loads(p.read_text(encoding='utf-8'))
    notes = []
    for fx in d['fixtures']:
        path = ROOT / 'fixtures' / fx['file']
        if not path.exists() or fx['expect'].get('must_fail'):
            continue
        text = read(path)
        if not text.strip():
            continue
        fixable, stuck = scan(text)
        if fixable:
            fx['expect']['must_not_contain_cp'] = fixable
        else:
            fx['expect'].pop('must_not_contain_cp', None)
        if stuck:
            notes.append((fx['file'], stuck))
            fx['expect']['known_unfixable_cp'] = stuck
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print('実ファイルから期待値を導きました')
    for fx in d['fixtures']:
        cps = fx['expect'].get('must_not_contain_cp')
        if cps: print(f'  {fx["file"]:<38} 直すべき: {" ".join("U+"+c for c in cps)}')
    if notes:
        print('\nNFKC でも直らないため期待値から外したもの（誰にも直せない）:')
        for f, s in notes:
            print(f'  {f:<38} {" ".join("U+"+c+"("+chr(int(c,16))+")" for c in s)}')

main()
