# ケーススタディ：JVM（HotSpot と GraalVM）

ケーススタディの最初は、JIT 研究の本流 —— **Java 仮想マシン**（JVM）です。
とりわけ標準実装の **HotSpot** は、20 年以上にわたって磨かれ、本書で
見てきた技法のほとんどを実戦投入してきた、いわば JIT の博物館です。
ここを丁寧に見ておくと、他の処理系が「HotSpot のどの部分を真似て、
どこを変えたか」として理解できるようになります。

## 出自：SELF から HotSpot へ

HotSpot のルーツは、本書で何度も登場した **SELF** の処理系にあります。
[デオプティマイズ](deopt-osr.md)（1992 年、SELF のデバッグのために発明）も、
[型フィードバック](profiling.md)による[インラインキャッシュ](profiling.md)
[](#cite:holzle1994)も、SELF で生まれました。その研究者たちが Sun に移り、
Java VM として結実させたのが HotSpot です。だから HotSpot は、最初から
「観測して投機する」JIT の思想を血肉としています。

名前の "HotSpot" 自体が、[なぜ JIT か](why-jit.md)で見た**ホットスポット**
（熱い場所だけを最適化する）に由来します。

## 二つのコンパイラ：C1 と C2

HotSpot の JIT は、伝統的に二つのコンパイラを持ちます
[](#cite:paleczny2001)。これは[階層的 JIT](tiered.md)の典型例です。

- **C1（クライアントコンパイラ）**：素早くコンパイルする[ベースライン](tiered.md)
  寄りのコンパイラ。最適化は控えめだが、起動が速い。
- **C2（サーバコンパイラ）**：時間をかけて徹底的に最適化する。[中間表現](ir.md)で
  見た **Sea of Nodes**[](#cite:click1995)を使い、高品質な機械語を出す。

現代の HotSpot は、この二つとインタプリタを組み合わせた**階層的コンパイル**
（tiered compilation）を標準とします。実行レベルは 0〜4 まであり、

```
レベル0: インタプリタ
レベル1: C1（最適化なし）
レベル2: C1（軽い最適化）
レベル3: C1（プロファイル収集つき）
レベル4: C2（全力最適化）
```

と段を上がっていきます。ふつうの流れは「0 → 3（C1 でプロファイルを
集めながら動かす）→ 4（集めたプロファイルで C2 が最適化）」です。
[プロファイリング](profiling.md)で見たカウンタとフィードバックが、この
段の昇格を駆動します。

## 投機の主役：仮想呼び出しの脱仮想化

Java で JIT がもっとも効くのは、**仮想呼び出し**（virtual call、実行時に
相手のメソッドが決まる呼び出し）の最適化です。Java では、ほとんどの
メソッド呼び出しが原理的には仮想呼び出しで、[なぜ JIT か](why-jit.md)で
見た「探して飛ぶ」間接呼び出しのコストを伴います。

HotSpot はこれを**クラス階層解析**（Class Hierarchy Analysis、CHA）と
[型フィードバック](profiling.md)で攻めます。たとえば次のコードを考えます。

```java
abstract class Shape { abstract double area(); }
class Circle extends Shape {
    double r;
    Circle(double r) { this.r = r; }
    double area() { return 3.14159 * r * r; }
}

double totalArea(Shape[] shapes) {
    double sum = 0;
    for (Shape s : shapes) {
        sum += s.area();   // 仮想呼び出し：s の実際の型しだい
    }
    return sum;
}
```

`s.area()` は、`s` が `Circle` なのか他の `Shape` なのか、原理的には
実行時まで分かりません。ところが、もしプログラム全体で `Shape` の具体
クラスが `Circle` しかロードされていなければ、CHA は「`area()` の実装は
`Circle#area` 一つしかない」と判断できます。すると HotSpot は、`s.area()` を
**`Circle#area` への直接呼び出しに脱仮想化**し、さらに本体が小さいので
[インライン化](why-jit.md)します。

```java
// HotSpot が最適化したあとのイメージ（概念）
for (Shape s : shapes) {
    // ガード：s は本当に Circle か？（後で別クラスがロードされたら破れる）
    sum += 3.14159 * ((Circle) s).r * ((Circle) s).r;  // インライン展開
}
```

ここがまさに投機です。「`Circle` しかない」という前提は、将来別の
`Shape` サブクラスがロードされると崩れます。そのとき HotSpot は
[デオプティマイズ](deopt-osr.md)（HotSpot の用語では **uncommon trap**、
めったに起きない罠）して、仮想呼び出しのある安全なコードへ戻ります。
**クラスのロードという、Java 特有の動的なイベントが、デオプトの引き金**に
なるのが面白いところです。

> [!NOTE]
> 呼び出し先が 1 種類なら単態、2 種類なら**二態**（bimorphic）として
> インライン化し、それ以上に散らばると[多態インラインキャッシュ](profiling.md)
> [](#cite:holzle1994)や、あきらめて仮想呼び出しのまま、と段階的に対応
> します。「いくつまでなら投機的にインライン化するか」は HotSpot の
> 重要なチューニングどころです。

## Java 特有の最適化：エスケープ解析

もう一つ、Java の JIT で効果が大きいのが**エスケープ解析**（escape
analysis）です。Java はあらゆるオブジェクトをヒープに確保し、[ガベージ
コレクション](glossary.md)で回収します。短命なオブジェクトを大量に作ると、
確保と回収のコストがかさみます。

エスケープ解析は、「あるオブジェクトが、それを作ったメソッドの外へ
**漏れ出す（エスケープする）か**」を調べます。漏れ出さない —— そのメソッドの
中でしか使われず、外に渡らない —— と分かれば、ヒープに確保する必要が
ありません。

```java
double distance(double x1, double y1, double x2, double y2) {
    Point p1 = new Point(x1, y1);   // この Point は…
    Point p2 = new Point(x2, y2);   // …メソッドの外へ出ない
    return p1.distanceTo(p2);
}
```

`p1` と `p2` は `distance` の中で作られ、中で使われ、外へ返りも渡りも
しません。C2 はこれを見抜き、**オブジェクトを作らずに、そのフィールド
（`x`, `y`）を直接ローカル変数（できれば CPU レジスタ）に置きます**。
これを**スカラ置換**（scalar replacement）と呼びます。[トレーシング](tracing.md)で
ふれた「ループ内アロケーションの除去」と同じ発想を、メソッド JIT で
実現したものです。`new` が消え、GC の負担も消えます。

## Graal：Java で書かれた JIT

HotSpot の物語は C2 で終わりません。**Graal** は、C2 を置き換えるべく
開発された新しい最適化コンパイラです。最大の特徴は、**Graal 自身が
Java で書かれている**ことです（C2 は C++ で書かれています）。「JIT
コンパイラを、その VM が動かす言語自身で書く」という、自己言及的な
設計です。

Graal は[中間表現](ir.md)に Sea of Nodes 系の表現を使い、[投機の前提と
デオプト点を第一級のノード](deopt-osr.md)として扱う洗練された設計を
持ちます[](#cite:duboscq2013)。そしてこの Graal が、[部分評価と Futamura
射影](research-partial-eval.md)で見た **Truffle** の土台でもあります。
Truffle 言語（TruffleRuby・GraalPy など）は、Graal の部分評価機構の上に
載っているのです。

さらに **GraalVM** は、[ウォームアップ問題](research-warmup.md)で
ふれた **Native Image** —— Java アプリを AOT コンパイルして瞬時に起動
できるようにする機能 —— も提供します。「JIT（実行時最適化）と AOT
（瞬時起動）を一つの基盤で両立する」という、ウォームアップ問題への
JVM 世界の回答が、GraalVM に集約されています。

> [!TIP]
> 手元の JDK で JIT の挙動を覗くこともできます。`-XX:+PrintCompilation`
> を付けて Java プログラムを動かすと、どのメソッドが何レベルでコンパイル
> されたかが流れます。`-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining`
> でインライン化の判断も見えます。本章で説明した「熱くなって段を上がり、
> インライン化され、ときにデオプトする」様子を、実物で観察してみて
> ください。

## まとめ

- **HotSpot** は SELF の系譜を継ぎ、[デオプト](deopt-osr.md)・[型
  フィードバック](profiling.md)・[インラインキャッシュ](profiling.md)を
  実戦に持ち込んだ JIT の本流。
- **C1（速い）＋ C2（強い、[Sea of Nodes](ir.md)）** の[階層的コンパイル](tiered.md)。
  レベル 0〜4 を昇格する。
- 投機の主役は**仮想呼び出しの脱仮想化**。CHA と型フィードバックで
  単態・二態に絞り、インライン化。前提はクラスロードで崩れ、**uncommon
  trap**（デオプト）で戻る。
- **エスケープ解析＋スカラ置換**で、漏れ出さないオブジェクトの `new` を
  消す。Java の重要最適化。
- **Graal** は Java で書かれた新世代コンパイラで、[Truffle](research-partial-eval.md)の
  土台。**GraalVM** は JIT と AOT（Native Image）を両立。

次は、JavaScript を四段で速くする、ヒドゥンクラスとインラインキャッシュの
王国 —— V8 を見ます。
