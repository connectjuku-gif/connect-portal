# connect-portal（学習塾CONNECT 教材ポータル）

講師用の教材HTMLを1ページにまとめて開けるポータル。このファイルは、別の環境（Cursor など）の Claude や人が作業を引き継ぐための説明書。

---

## 1. 全体の仕組み

| 項目 | 内容 |
|---|---|
| リポジトリ | GitHub `connectjuku-gif/connect-portal`（ブランチは `main` のみ） |
| 公開先 | Cloudflare Workers（静的アセット配信）　本番URL：https://connect-portal.connect-juku.workers.dev |
| デプロイ | `main` に push すると Cloudflare 側の Git 連携で自動デプロイ（手動アップロード・ビルド作業なし） |
| 設定 | `wrangler.toml`：`main = "src/worker.js"`、`[assets] directory = "."`（リポジトリ直下をそのまま配信）、`run_worker_first = true` |
| ログイン | `src/worker.js` で講師共通のBasic認証（ID・パスワードもこのファイルに書いてある。変えるときはここを書きかえて push） |
| 配信しないもの | `.assetsignore` に書いたもの（`src/` `tools/` `README.md` `.git/` など） |

ビルド工程やフレームワークはない。**HTMLファイルをリポジトリ直下に置けば、そのファイル名のURLで開ける**（例：`foo.html` → `https://…workers.dev/foo.html`）。ただしポータルのトップに出すには、2 の手順で `index.html` にカードを足す必要がある。

### worker.js がしていること
1. Basic認証のチェック。
2. 教材ページ（`/`・`/index.html` 以外のHTML）に、左下の「← ポータル」ボタンを HTMLRewriter で差しこむ。教材ファイル自体は書きかえない。印刷時・iframe内・ダウンロードして file: で開いたときは表示されない。

---

## 2. 教材を追加してポータルに載せる手順

1. **教材HTMLをリポジトリ直下に置く**
   - 1教材＝1つの単一HTML（CSS・JSは中に書く。外部ファイルに頼らない）。
   - 必ず `<!DOCTYPE html>` と `<meta charset="UTF-8">` を持つ完全なHTMLにし、**UTF-8 BOM付き**で保存する（ダウンロードして開くと文字化けするのを防ぐため）。
   - ファイル名のつけ方（英小文字・ハイフン区切り）：
     - 学年＋教科＋内容：`g2-eng-check-u4-easy.html`、`math-g3-ch5-similarity-test.html`
     - 学校別の定期テスト予想問題：`g2-eng-nishishinjuku-kimatsu-standard.html`（学年-教科-学校-考査-レベル）
     - 小学生：`el6-…`、`elem-…`
2. **`index.html` にカードを1枚足す**（3 の構造を参照。似たカードをコピーして書きかえるのが確実）。
3. **サムネイルを作る**：`python3 tools/make_thumbs.py --new`（Playwright/Chromium が必要。新しいカードの教材1画面目を撮って `thumbs/<教材名>.jpg` を作り、index.html に画像を差しこむ）。
4. **リンク切れを確認**して commit → push。数十秒〜1分ほどで本番に反映。

---

## 3. index.html の構造

```
<header> … タイトル・検索ボックス（#searchInput）
<main>
  .filter-bar
    nav.subjects   教科（すべて／英語 #eng-top／数学 #math-top へのページ内リンク）
    nav.grades     学年ボタン  .gchip[data-grade="all|el|1|2|3|hs"]
  nav.schools      中学校ボタン .schip[data-school="all|中野東|西戸山|西新宿"]
  nav.tags         単元ボタン  .tchip[data-tag="文法|関数|…"]
  カテゴリへのリンク行
  <section id="eng-top" class="subject">   英語
    <div id="eng-grammar" class="category">  文法解説
    <div id="eng-check"   class="category">  文法確認テスト
    <div id="eng-teiki"   class="category">  定期テスト予想問題
    <div id="eng-exam"    class="category">  都立入試対策
    <div id="eng-vocab"   class="category">  単語・読解
  <section id="math-top" class="subject">  数学
    #math-teiki（定期テスト予想問題）／#math-formula（公式・総復習）／#math-exam（都立入試対策）／#math-calc（計算プリント）／#math-check（確認テスト）
```

### カード1枚の形

```html
<div class="card material-item" data-grade="2" data-tags="定期テスト 予想問題 西新宿 have to must">
  <div class="thumb"><span class="temoji">📝</span><span class="gbadge gb-2">中2</span></div>
  <div class="body">
    <div class="card-title">中2英語 2学期期末 予想問題（西新宿）</div>
    <div class="desc">NEW HORIZON 2 Unit 4・5／筆記70点</div>
    <div class="pills"><a href="g2-eng-nishishinjuku-kimatsu-standard.html" class="pill">標準</a><a href="…" class="pill">応用</a></div>
  </div>
</div>
```

- `data-grade`：学年ボタンでの絞り込みに使う。`el` `1` `2` `3` `hs`。複数学年はスペース区切り（`"1 2 3"`）。
- `gbadge` のクラス：`gb-1` `gb-2` `gb-3` `gb-el`、複数学年は `gb-multi`。
- `data-tags`：単元ボタン（`data-tag` と完全一致した語）と検索に使う。スペース区切り。
- **中学校ボタン**：カードの `card-title` に学校名（中野東・西戸山・西新宿）が入っていれば、そのボタンに自動で出る。タイトルに入れられないときは `data-school="中野東"` 属性を付ける。新しい学校を足すときは `nav.schools` にボタンを1つ追加する（件数は自動で数える）。
- ボタンの並べ方の種類：
  - `.pills`：ボタンを横に並べる（レベル違いなど）
  - `.prows > .prow > .plab`：行ごとにラベル＋ボタン（「単元名：やさしめ／標準」など）
  - `.ptable`：学年×レベルの表
- 絞り込みのJSは index.html の末尾（`updateVisibility()`）。学年・単元・中学校・検索をすべて満たすカードだけ表示し、空になったカテゴリはまるごと隠す。

---

## 4. 単元が多い教材は「まとめページ（ハブ）」にする

カードを増やしすぎないため、単元がたくさんある教材は **1ページ＋上部の単元ボタン、下にiframeで表示** の形にしている（塾長がこの形を気に入っている）。

| まとめページ | 中身 |
|---|---|
| `el6-math-check.html` | 小6算数 確認テスト（`el6-math-check-01〜12.html`） |
| `math-check-hub.html` | 数学 単元確認テスト 中1〜中3 |
| `eng-check-hub.html` | 英語 文法確認テスト（学年・教科書 → 単元 → やさしめ／標準） |
| `todai-math-hub.html` | 都立入試 数学 大問4・5（ドリル／演習） |
| `g3-eng-nakanohigashi-kouki-drill.html` | 中野東3年 大問別ドリル（大問5〜11） |

- 新しい単元を足すとき：個別の教材HTMLを置き、まとめページの `<script>` 内の `var D = {…}` の `units` に `{"name":"単元名","f":"ファイル名.html"}` を1行足す（レベル違いは `"f":{"やさしめ":"…-easy.html","標準":"…-standard.html"}`）。**ポータルのカードは増やさない。**
- `#g2u1l1`（2つ目の学年タブ・1つ目の単元・1つ目のレベル）のようなURLで、特定の単元を直接開ける。
- 「この教材を印刷」ボタンは、表示中のiframeの中身だけを印刷する。

---

## 5. 教材HTMLの共通ルール

- **定期テスト予想問題・確認テスト**：A4印刷用。1枚目＝問題用紙、2枚目＝解答・解説。
  - 解答・解説は生徒にも配るので「講師用」とは書かない。
  - 白黒印刷前提（正答は黒太字＋下線）。
  - 画面右上に「編集モード」（contenteditable）と「保存」ボタン（印刷時は非表示）。
  - 解答ページ冒頭のメモは生徒向けの言い回しで「■ テスト範囲と勉強のポイント」とする（古いファイルには「■ 出題範囲メモ」のままのものが残っている）。
- **ランダム生成系**（`*-review-*`、`vocab-test-*`、`math-calc-practice-*` など）：ページ内のJSが毎回問題を作る。データはHTML内の配列。
- `materials/` には一部教材のPDF版がある。

---

## 6. 作業するときの注意

- 作業前に `git pull`（別の環境からも push されることがある）。
- 既存の教材ファイルは消さない（古いリンクが生きているため）。まとめ直すときは表示用のページを新しく足す。
- 文章・ボタン名は日本語。塾長への説明も日本語で。
