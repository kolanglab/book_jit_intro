# 第 III 部 ケーススタディ

最後に、実在する処理系の JIT を見ていきます。第 I 部・第 II 部で学んだ
技法が、現実の制約（互換性、開発リソース、対象言語の性質）のなかで
どう組み合わされ、どう取捨選択されているかを観察します。

- **JVM（HotSpot / GraalVM）** —— JIT 研究の本流。C1・C2 の二段構成と
  Sea of Nodes、そして Graal による刷新。
- **V8** —— JavaScript を四段（Ignition / Sparkplug / Maglev / TurboFan）で
  速くする、ヒドゥンクラスとインラインキャッシュの王国。
- **Ruby** —— YJIT（基本ブロックバージョニング）と、Ruby 4.0 の実験的な ZJIT。
  Ruby 固有のオブジェクトモデルにどう寄り添うか。
- **Python（PyPy / CPython）** —— メタトレーシングの PyPy と、
  CPython 3.13 以降の実験的 Copy-and-Patch JIT。
- **LuaJIT** —— 一人の天才が作り上げた、トレーシング JIT の到達点。
- **その他の処理系** —— JavaScriptCore・.NET・Julia・Dart・Android ART・
  Self まで、地図の余白を埋めます。
- **言語処理系の外の JIT** —— 正規表現・データベース・eBPF・GPU・動的
  バイナリ変換まで。「実行時情報による特化」という発想の広がりを俯瞰します。

各章では、その処理系**ならでは**の技術を、できるだけコードとともに
紹介します。同じ「JIT」という言葉の下に、これだけ多様な設計があることが
見えてくるはずです。
