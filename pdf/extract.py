#!/usr/bin/env python3
"""pdf/extract.py — pip不要・標準ライブラリのみの軽量 PDF テキスト抽出。

ACM DL の論文 PDF を `pdf/` に置いて実行すると、隣に `<name>.txt` を書き出す。
用途は「論文本文を grep して本書の記述と照合する」こと（清書ではない）。

  python3 pdf/extract.py                # pdf/ 内の全 .pdf を変換
  python3 pdf/extract.py foo.pdf bar.pdf  # 指定ファイルだけ
  python3 pdf/extract.py --meta foo.pdf   # タイトル/著者/DOI だけ表示（論文の同定用）

抽出方式：各 stream を zlib 展開し、コンテンツストリーム中の Tj/TJ の
`(...)`・`<hex>` を拾って latin-1 で復元する。多くの ACM PDF（標準/Type1
フォント）はこれで十分読める。CID サブセットフォントでグリフ番号になり
文字化けする PDF は ASCII 比率の警告を出す（捏造を避けるため、無理な推測
変換はしない。その場合は論文ごとに個別対応する）。

注意：PDF のカーニング（TJ 配列）のため、出力では語中に空白が入ることが
ある（例 "or ders of magnitude"）。grep するときは語境界を仮定せず、
`grep -aoiE "or.{0,4}ers of magnitude"` のようにゆるいパターンで当てること。
本文照合（grep）用であり、清書テキストではない。
"""
import re, sys, zlib, glob, os

OCTAL = re.compile(rb"\\([0-7]{1,3})")
ESCAPES = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b",
           b"f": b"\f", b"(": b"(", b")": b")", b"\\": b"\\"}


def _unescape_pdf_string(s: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(s):
        c = s[i:i+1]
        if c == b"\\" and i + 1 < len(s):
            nxt = s[i+1:i+2]
            m = OCTAL.match(s, i)
            if m:
                out.append(int(m.group(1), 8) & 0xFF)
                i = m.end()
                continue
            out += ESCAPES.get(nxt, nxt)
            i += 2
            continue
        out += c
        i += 1
    return bytes(out)


def _iter_streams(data: bytes):
    # `stream` の後の改行は \r\n / \n のどちらもあり、末尾も改行有無の両方がある。
    # 取りこぼしを避けるため末尾の改行は要求しない。
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        raw = m.group(1)
        if raw[-2:] == b"\r\n":
            raw = raw[:-2]
        elif raw[-1:] in (b"\n", b"\r"):
            raw = raw[:-1]
        try:
            yield zlib.decompress(raw)
        except Exception:
            yield raw  # 非圧縮ストリームもそのまま見る


def _text_from_content(stream: bytes) -> str:
    parts = []
    # (...) 文字列（Tj / TJ 配列内）
    for m in re.finditer(rb"\((?:[^()\\]|\\.)*\)", stream):
        parts.append(_unescape_pdf_string(m.group(0)[1:-1]).decode("latin-1"))
    # <hex> 文字列（1バイト符号と仮定して復元。CID の場合は後段で警告）
    for m in re.finditer(rb"<([0-9A-Fa-f]+)>", stream):
        h = m.group(1)
        if len(h) % 2:
            h += b"0"
        try:
            parts.append(bytes.fromhex(h.decode()).decode("latin-1"))
        except Exception:
            pass
    return " ".join(parts)


def _build_tounicode_map(data: bytes):
    """全ストリームから ToUnicode CMap(bfchar/bfrange) を集めて
    code(int) -> Unicode文字列 の対応表を作る（CIDフォント PDF 用）。
    コードは CMap 中の <hex> をそのままビット列として扱う（多くは2バイト）。"""
    cmap = {}
    def utf16be(h: bytes) -> str:
        b = bytes.fromhex(h.decode())
        try:
            return b.decode("utf-16-be")
        except Exception:
            return ""
    for s in _iter_streams(data):
        if b"beginbfchar" not in s and b"beginbfrange" not in s:
            continue
        for blk in re.findall(rb"beginbfchar(.*?)endbfchar", s, re.S):
            for src, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
                cmap[int(src, 16)] = utf16be(dst)
        for blk in re.findall(rb"beginbfrange(.*?)endbfrange", s, re.S):
            for lo, hi, dst in re.findall(
                    rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
                a, b = int(lo, 16), int(hi, 16)
                base = int(dst, 16)
                for i in range(b - a + 1):
                    cmap[a + i] = chr(base + i) if base + i < 0x110000 else ""
    return cmap


def _text_with_cmap(data: bytes, cmap: dict, width: int = 2) -> str:
    out = []
    for s in _iter_streams(data):
        if not _is_content_stream(s):
            continue
        # content stream 中の表示文字列：<hex> と (...) を width バイト単位で復号
        for tok in re.finditer(rb"<([0-9A-Fa-f]+)>|\(((?:[^()\\]|\\.)*)\)", s):
            if tok.group(1) is not None:
                raw = bytes.fromhex(tok.group(1).decode() + ("0" if len(tok.group(1)) % 2 else ""))
            else:
                raw = _unescape_pdf_string(tok.group(2))
            for i in range(0, len(raw) - width + 1, width):
                code = int.from_bytes(raw[i:i+width], "big")
                out.append(cmap.get(code, ""))
        out.append("\n")
    return "".join(out)


def _ascii_ratio(s: str) -> float:
    if not s:
        return 1.0
    printable = sum(1 for ch in s if ch == "\n" or 32 <= ord(ch) < 127)
    return printable / len(s)


def _is_content_stream(s: bytes) -> bool:
    # 画像・フォントプログラム等のバイナリ stream を除き、テキスト描画
    # オペレータを含むコンテンツ stream だけを対象にする（ノイズ低減）。
    return (b"Tj" in s or b"TJ" in s) and b"BT" in s


def extract_text(path: str) -> str:
    data = open(path, "rb").read()
    chunks = [_text_from_content(s) for s in _iter_streams(data)
              if _is_content_stream(s)]
    text = "\n".join(c for c in chunks if c.strip())
    # 体裁を少し整える（リガチャ・余分な空白）
    text = (text.replace("\x02", "fi").replace("\x03", "fl")
                .replace("\x01", "ff").replace("\xad", "-"))
    text = re.sub(r"[ \t]{2,}", " ", text)
    # 文字化け（CIDフォント）なら ToUnicode CMap で復号を試みる
    if _ascii_ratio(text) < 0.55:
        cmap = _build_tounicode_map(data)
        if cmap:
            for w in (2, 1):
                alt = re.sub(r"[ \t]{2,}", " ", _text_with_cmap(data, cmap, w))
                if _ascii_ratio(alt) > _ascii_ratio(text) and len(alt) > 200:
                    text = alt
                    break
    return text


def show_meta(path: str):
    data = open(path, "rb").read()
    def grab(key: bytes):
        m = re.search(re.escape(key) + rb"\s*\(((?:[^()\\]|\\.)*)\)", data)
        return _unescape_pdf_string(m.group(1)).decode("latin-1") if m else None
    titles = [t for t in re.findall(r"/Title\s*\(((?:[^()\\]|\\.)*)\)",
                                    data.decode("latin-1"))
              if len(t) > 25 and " " in t]
    doi = re.search(rb"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", data)
    print(f"== {path}")
    print("  TITLE :", titles[0] if titles else "(compressed/objstm)")
    print("  AUTHOR:", grab(b"/Author") or "(n/a)")
    print("  DOI   :", doi.group(0).decode() if doi else "(n/a)")


def main(argv):
    meta = "--meta" in argv
    argv = [a for a in argv if not a.startswith("--")]
    here = os.path.dirname(os.path.abspath(__file__))
    paths = argv or sorted(glob.glob(os.path.join(here, "*.pdf")))
    for p in paths:
        if meta:
            show_meta(p)
            continue
        text = extract_text(p)
        ratio = _ascii_ratio(text)
        out = os.path.splitext(p)[0] + ".txt"
        open(out, "w", encoding="utf-8").write(text)
        warn = "" if ratio > 0.85 else (
            f"  [!] ASCII率 {ratio:.0%} — CIDフォントの可能性。"
            "本文照合には注意（無理な推測変換はしていません）。")
        print(f"wrote {out}  ({len(text)} chars, ascii {ratio:.0%}){warn}")


if __name__ == "__main__":
    main(sys.argv[1:])
