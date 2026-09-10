#!/usr/bin/env python3
"""検査に使う抽出コマンドの例（pypdf）。

    ../check.py --cmd "python3 examples/pypdf_extract.py {file}"

**読めないときは空文字を出さず、終了コード1で終える。** これが要点。
"""
import sys, warnings
warnings.filterwarnings('ignore')

path = sys.argv[1]
try:
    import pypdf
    text = ''.join(p.extract_text() or '' for p in pypdf.PdfReader(path).pages)
except Exception:
    sys.exit(1)          # 開けなかった
if not text.strip():
    sys.exit(1)          # テキスト層が無い。空文字を成功にしない
print(text)
