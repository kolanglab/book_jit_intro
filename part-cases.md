# 第 III 部 ケーススタディ

最後に、実在する処理系の JIT を見ていきます。第 I 部・第 II 部で学んだ
技法が、現実の制約（互換性、開発リソース、対象言語の性質）のなかで
どう組み合わされ、どう取捨選択されているかを観察します。

- **JVM（HotSpot / GraalVM）** —— JIT 研究の本流。C1・C2 の二段構成と
  Sea of Nodes、そして Graal による刷新。
- **V8** —— JavaScript を四段（Ignition / Sparkplug / Maglev / TurboFan）で
  速くする、ヒドゥンクラスとインラインキャッシュの王国。
- **Ruby** —— YJIT（基本ブロックバージョニング）と、その先の ZJIT。
  Ruby 固有のオブジェクトモデルにどう寄り添うか。
- **Python（PyPy / CPython）** —— メタトレーシングの PyPy と、
  公式に JIT を載せた CPython 3.13 の Copy-and-Patch。
- **LuaJIT** —— 一人の天才が作り上げた、トレーシング JIT の到達点。
- **その他の処理系** —— JavaScriptCore・.NET・Julia・Dart・Android ART・
  Self まで、地図の余白を埋めます。

各章では、その処理系**ならでは**の技術を、できるだけコードとともに
紹介します。同じ「JIT」という言葉の下に、これだけ多様な設計があることが
見えてくるはずです。
