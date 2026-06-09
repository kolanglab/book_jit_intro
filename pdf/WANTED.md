# 論文の入手・照合ステータス（最終）

凡例：✅入手＆本文照合済み ／ 🟡入手したが抽出が文字化け・暗号化で本文照合は不可（記述は標準的で低リスク）
／ 🌐Webで照合済み（PDF不要） ／ ❌入手不可 ／ ⬜任意（未取得・なくてよい）

運用：PDF をブラウザ（ACM会員）で `pdf/` に保存 → `python3 pdf/extract.py` で `*.txt` 化 →
grep で本文照合。ファイル名は DOI 等のままでOK（中身のメタデータで判定）。

> **結論：追加で必要な PDF はありません。** 第II部「最新研究」は全て一次情報で裏取り済み。
> 第I部・第III部の中核論文も主要なものは本文照合済み。残る 🟡 は抽出不可だが記述は教科書的で、
> メタデータは dblp/ACM で検証済み。

## 第II部「最新研究」—— すべて一次情報で裏取り済み
| cite key | 論文 | 状態 |
|----------|------|------|
| barrett2017 | Virtual Machine Warmup Blows Hot and Cold | 🌐 公式HTML/arXivで照合済み |
| haas2017 | Bringing the Web up to Speed with WebAssembly | 🌐 著者PDFで照合済み |
| fluckiger2018 | Correctness of Speculative Optimizations … | 🌐 arXivで照合済み |
| xu2021 | Copy-and-Patch Compilation | ✅ `3485513`（本文照合・性能数値を実数へ修正） |
| cpython313jit | PEP 744 — JIT Compilation | 🌐 PEPで照合済み |
| wurthinger2017 | Practical Partial Evaluation … | ✅ `3062341.3062381`（本文照合・第一Futamura射影/性能比を確認） |
| wurthinger2013 | One VM to Rule Them All | ✅ `2509578.2509581`（本文照合） |
| prokopec2017 | Making Collection Operations Optimal … | ✅ `3136000.3136002`（本文照合・case-jvm へ引用追加） |

## 第I部・第III部の中核/古典研究
| 章 | cite key | 論文 | 状態 |
|----|----------|------|------|
| ir | click1995 | A Simple Graph-Based IR (Sea of Nodes) | ✅ `202529.202534`（本文照合・5箇所精密化） |
| ir | poletto1999 | Linear Scan Register Allocation | ✅ `330249.330250`（彩色比 約10%以内/数倍速を確認） |
| ir/jvm | duboscq2013 | An IR for Speculative Optimizations (Graal) | ✅ `2542142.2542143`（guard=浮動ノード/GVN coalesce 確認） |
| tracing | gal2006 | HotpathVM | ✅ `1134760.1134780`（primary/secondary trace・7〜11倍を確認、"trace tree"は後年の語と補注） |
| meta-tracing | bolz2015 | The Impact of Meta-Tracing on VM Design | ✅ `1-s2.0-S0167642313000269`（本文照合） |
| meta-tracing | bolz2009 | Tracing the Meta-Level (PyPy) | 🌐 照合済み |
| tracing | gal2009 | Trace-based JIT Type Specialization (TraceMonkey) | 🌐 照合済み |
| compilation-units/ruby | chevalier2015 | Lazy Basic Block Versioning | 🌐 照合済み（型テスト71%除去/最大50%高速を確認） |
| ir | cytron1991 | Efficiently Computing SSA Form | 🟡 `115372.115320`（抽出文字化け＝カスタムType1。SSAの記述は教科書的、メタデータ検証済み） |
| deopt-osr | holzle1992 | Debugging Optimized Code with Dynamic Deoptimization | 🟡 `143095.143114`（抽出文字化け。脱最適化の起源＝デバッグは確立した事実） |
| profiling/tiered | arnold2000 | Adaptive Optimization in the Jalapeño JVM | 🟡 `353171.353175`（抽出文字化け。サンプリング適応の記述は標準的） |
| case-jvm | paleczny2001 | The Java HotSpot Server Compiler | 🟡 `paleczny.pdf`（**RC4暗号化で本文抽出不可**。C2＝サーバコンパイラの記述は標準的で click1995 も引用済み、訂正不要） |
| compilation-units | suganuma2000 | Overview of the IBM Java JIT Compiler | ❌ 入手不可（IBM Systems Journal、ペイウォール）。本文の言及は「領域ベース JIT の一例」という一般的記述で問題なし |

## ASTro 設計メモ用（本とは独立、`tmp/` に成果物）
| 用途 | 論文 | 状態 |
|------|------|------|
| ASTro OSR/脱最適化 設計メモ | essertel2021「On-Stack Replacement for Program Generators…」(GPCE 2021) | ✅ `essertel-gpce21.pdf`（本文精読 → `tmp/astro-osr-design-memo.md`）。本書 deopt-osr へも引用追加 |
| 関連 | delia2018「On-Stack Replacement, Distilled」(PLDI 2018) | 🌐 概要確認（deopt-osr へ引用追加） |

## これ以上の取得は不要
- SELF/Smalltalk 系（ungar1987 / chambers1989 / deutsch1984 / holzle1994 / holzle1991）：本書の主張は確立した史実。dblp でメタデータ検証済み（holzle1991・detlefs1999 は DOI 補完）。
- 後から追加した文献（georges2007 / kotzmann2008 / wimmer2010 / stadler2014 / detlefs1999 / ishizaki2000 / rigo2006 / wimmer2019）：DOI 等を dblp/ACM で検証済み。
- 教科書・公式ドキュメント（aho2006 / lattner2004 / cranelift / dynasm / luajit / makarov_mir / v8maglev / v8sparkplug / pep659）：一次情報は公開済み。

> 🟡 の4本（cytron1991 / holzle1992 / arnold2000 / paleczny2001）は古いカスタムエンコード／RC4暗号化のため、
> 標準ライブラリ（`pdf/extract.py`）では本文抽出できません。記述はいずれも教科書的で訂正の必要は見込んでいません。
> どうしても逐語照合したい場合のみ、「選択可能テキスト版（非暗号化）」PDF があれば差し替えられます。
