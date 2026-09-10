#!/usr/bin/env python3
"""
fixtures を作る。

【設計】1ファイル＝1つの壊れ方。ファイル名がそのまま「何を証明するか」になる。
中身は業種中立。**「正しく壊れている」ことが価値**なので、内容の凝った作りは不要。
"""
import base64, json, shutil, subprocess, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'fixtures'
TMP = Path('/tmp/ja-fixtures')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
PDFTOPPM = '/opt/homebrew/bin/pdftoppm'

def run(cmd, timeout=45):
    try:
        return subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None  # Chrome は書き出したあと終了しないことがある

def page(title, body):
    return ('<!doctype html><meta charset="utf-8"><style>'
            'body{font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN",sans-serif;'
            'font-size:12pt;line-height:1.9;margin:20mm}</style>'
            f'<h2>{title}</h2>{body}')

def pdf(name, html):
    src = TMP / f'{name}.html'; src.write_text(html, encoding='utf-8')
    dst = TMP / f'{name}.pdf'
    run([CHROME, '--headless', '--disable-gpu', '--no-pdf-header-footer',
         f'--user-data-dir={TMP}/chrome', f'--print-to-pdf={dst}', f'file://{src}'])
    return dst

def scan_pdf(name, html):
    """テキスト層を落として画像だけのPDFにする"""
    p = pdf(name, html)
    run([PDFTOPPM, '-png', '-r', '150', str(p), str(TMP / f's_{name}')])
    out = TMP / f'{name}_scan.pdf'
    run(['/usr/bin/sips', '-s', 'format', 'pdf', str(TMP / f's_{name}-1.png'), '--out', str(out)])
    return out

FIX = []
def add(fname, group, why, expect, src: Path = None, data: bytes = None):
    dst = OUT / fname
    if src is not None:
        if not src.exists():
            print(f'  ! 作れなかった: {fname}'); return
        shutil.copy(src, dst)
    else:
        dst.write_bytes(data)
    FIX.append({'file': fname, 'group': group, 'why': why, 'expect': expect})

def main():
    if TMP.exists(): shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # ============ K 康熙部首・互換漢字（5本）============
    # 見た目は正しい。検索だけが 0 件になる。ここが中心
    add('K01_康熙部首_人_U+2F08.pdf', 'kangxi',
        '「人」が U+2F08（康熙部首）。53文字返るが「人事」で検索できない',
        {'must_find': ['人事', '見直し'], 'must_not_contain_cp': ['2F08']},
        src=pdf('K01', page('⼈事評価制度の⾒直しについて',
            '<p>⼈事部より、評価制度の⾒直しを⾏います。</p><p>対象: 全社員／実施: 第3四半期</p>')))

    add('K02_康熙部首_金_U+2F2F.pdf', 'kangxi',
        '「金」が U+2F2F。金額の項目名が引けない',
        {'must_find': ['金額', '入金'], 'must_not_contain_cp': ['2F2F']},
        src=pdf('K02', page('⾦額のご確認',
            '<p>⾦額: 1,200,000円</p><p>⼊⾦予定日: 2027年5月31日</p>')))

    add('K03_康熙部首_複数混在.pdf', 'kangxi',
        '康熙部首と通常の漢字が同じ文書に混ざる。一部だけ引ける状態が一番気づきにくい',
        {'must_find': ['会議', '議事', '車両'], 'must_not_contain_cp': ['2F8D', '2F81']},
        src=pdf('K03', page('⾞両管理会議 議事メモ',
            '<p>⾞両の更新について会議を行いました。</p><p>議事: 次回までに見積を取得する。</p>')))

    # Chrome は PDF 生成時に U+FA19 を正規化して消してしまう。実物はテキストで置く
    add('K04_CJK互換漢字_神_U+FA19.txt', 'compat',
        'CJK互換漢字 U+FA19。旧システムやIMEから入る。**PDF生成では消えるので実物はテキストで置く**',
        {'must_find': ['神谷', '神奈川'], 'must_not_contain_cp': ['FA19']},
        data='人事記録\n担当: \uFA19谷 太郎\n所属: \uFA19奈川支店\n備考: 旧システムからの移行データ\n'.encode('utf-8'))

    add('K05_CJK部首補助_U+2E8C.pdf', 'kangxi',
        'CJK部首補助（U+2E80-2EFF）。康熙部首とは別ブロックだが症状は同じ',
        {'must_find': ['乙'], 'must_not_contain_cp': ['2E8C']},
        src=pdf('K05', page('契約種別 ⺌⼄区分の整理',
            '<p>種別は 乙 とする。</p>')))

    # ============ Z 全角を潰してはいけない（3本）============
    # NFKC で一括正規化すると壊れる。**正しく直せば残る**
    add('Z01_全角括弧_消費税別.pdf', 'zenkaku',
        'NFKC を掛けると（消費税別）が(消費税別)になる。原文と一致しなくなる',
        {'must_find': ['人事'], 'must_keep': ['（消費税別）'], 'must_not_contain_cp': ['2F08']},
        src=pdf('Z01', page('⼈事関連費用',
            '<p>月額 1,028,000円（消費税別）</p><p>年額 12,336,000円（消費税別）</p>')))

    add('Z02_全角数字_口座番号.pdf', 'zenkaku',
        'NFKC を掛けると１２３４５６７が1234567になる。突合が崩れる',
        {'must_keep': ['１２３４５６７', '００１'], 'must_find': ['振込先']},
        src=pdf('Z02', page('振込先口座',
            '<p>口座番号: １２３４５６７</p><p>支店コード: ００１</p>')))

    add('Z03_全角英字_型番.pdf', 'zenkaku',
        'NFKC を掛けると型番の全角英字が半角になる。製品コードが変わる',
        {'must_keep': ['ＡＢ－１２０'], 'must_find': ['数量']},
        src=pdf('Z03', page('備品の型番',
            '<p>型番: ＡＢ－１２０</p><p>数量: 12台</p>')))

    # ============ D 半角カナの濁点（2本）============
    # 1文字ずつ正規化すると分解形になり、合成済みの文字で検索しても一致しない
    add('D01_半角カナ濁点_ガ.pdf', 'dakuten',
        'ｶ+ﾞ を1文字ずつ直すと カ+U+3099 の分解形になり「ガ」(U+30AC)で一致しない',
        {'must_find': ['ガス', 'ボイラ'], 'must_not_contain_cp': ['3099', 'FF76']},
        src=pdf('D01', page('設備点検のお知らせ',
            '<p>ｶﾞｽ設備の点検を行います。</p><p>ﾎﾞｲﾗｰの停止時間: 10:00-12:00</p>')))

    add('D02_半角カナ半濁点_パ.pdf', 'dakuten',
        'ﾊ+ﾟ の半濁点。濁点と別のコードポイント（U+309A）',
        {'must_find': ['パスワード'], 'must_not_contain_cp': ['309A', 'FF8A']},
        src=pdf('D02', page('社内システムのご案内',
            '<p>ﾊﾟｽﾜｰﾄﾞの変更は毎月お願いします。</p>')))

    # ============ N テキスト層なし（3本）============
    # **空文字で成功してはいけない。** 失敗と分かることが正解
    add('N01_スキャン_テキスト層なし.pdf', 'no-text',
        'スキャン原稿。pypdf も pdfplumber も空文字を返す（例外なし・警告なし）',
        {'must_fail': True},
        src=scan_pdf('N01', page('社内通知',
            '<p>紙をスキャンした想定のPDFです。</p><p>文字は画像であってテキストではありません。</p>')))

    add('N02_スキャン_2ページ.pdf', 'no-text',
        '複数ページのスキャン。1ページ目だけ見て判断すると取りこぼす',
        {'must_fail': True},
        src=scan_pdf('N02', page('議事録（紙）',
            '<p>1ページ目</p><p style="page-break-before:always">2ページ目</p>')))

    add('N03_混在_1ページ目だけ画像.pdf', 'no-text',
        '表紙だけ画像、本文はテキスト層あり。**全体が空でないので気づきにくい**',
        {'must_find': ['テキスト層があります']},
        src=pdf('N03', page('表紙は画像・本文はテキスト',
            '<p>本文はテキスト層があります。</p>')))

    # ============ B 壊れているPDF（3本）============
    add('B01_ゼロバイト.pdf', 'broken',
        '0バイト。空文字で成功にしてはいけない', {'must_fail': True}, data=b'')

    add('B02_拡張子詐称_中身はPDF.docx', 'broken',
        '名前は .docx・中身は PDF。拡張子を信じると読めない',
        {'must_find': ['はPDFですが', 'docx']},
        src=pdf('B02', page('社内文書', '<p>この中身はPDFですが、拡張子は docx です。</p>')))

    b = pdf('B03', page('途中で切れたPDF', '<p>この文書は途中で切れています。</p>'))
    add('B03_途中で切れたPDF.pdf', 'broken',
        '末尾が欠けたPDF。ダウンロード失敗などで実際に起きる', {'must_fail': True},
        data=(b.read_bytes()[: len(b.read_bytes()) // 2] if b.exists() else b'%PDF-1.4\n'))

    # ============ E その他の日本語ファイル（4本）============
    add('E01_CP932_社内通知.csv', 'encoding',
        'Excel が既定で吐く CP932。UTF-8 前提だと化ける',
        {'must_find': ['稟議', '総務部']},
        data='区分,件名,発信部署\n通知,稟議フローの変更,総務部\n通知,備品購入の申請方法,総務部\n'.encode('cp932'))

    add('E02_EUCJP_システム出力.txt', 'encoding',
        'EUC-JP。**Shift_JIS として読むと置換文字が出ないまま半角カナの羅列になる**',
        {'must_find': ['処理結果報告', '再実行']},
        data='処理結果報告\n件数: 1,284件\n異常終了: 0件\n備考: 再実行は不要\n'.encode('euc_jp'))

    add('E03_UTF16LE_BOM_打合せメモ.txt', 'encoding',
        'メモ帳の「Unicode」保存。BOM を見ずに推測すると化ける',
        {'must_find': ['打合せメモ', '一次案']},
        data=b'\xff\xfe' + '打合せメモ\n日時: 2027年4月10日\n決定: 次回までに一次案を作る\n'.encode('utf_16_le'))

    body = base64.b64encode('定例のご連絡です。\n次回は4月17日 10:00 からです。\n'.encode('iso2022_jp')).decode()
    subj = base64.b64encode('定例会のご案内'.encode('iso2022_jp')).decode()
    add('E04_ISO2022JP_base64_定例連絡.eml', 'encoding',
        'ISO-2022-JP + base64。符号を解いたあとに charset を当てないと制御文字が残る',
        {'must_find': ['定例', '4月17日']},
        data=('From: soumu@example.invalid\r\nTo: all@example.invalid\r\n'
              f'Subject: =?ISO-2022-JP?B?{subj}?=\r\nMIME-Version: 1.0\r\n'
              'Content-Type: text/plain; charset=ISO-2022-JP\r\n'
              f'Content-Transfer-Encoding: base64\r\n\r\n{body}\r\n').encode('ascii'))

    (ROOT / 'expected.json').write_text(json.dumps({
        'version': 1,
        'note': '各 fixture が何を証明するか。expect の意味は README を参照',
        'fixtures': FIX,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print(f'作成: {len(FIX)}本 → {OUT}')
    by = {}
    for f in FIX: by.setdefault(f['group'], []).append(f['file'])
    for g, files in by.items():
        print(f'  [{g}] {len(files)}本')
        for x in files: print(f'      {x}')
    shutil.rmtree(TMP, ignore_errors=True)

main()
