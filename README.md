# connect-portal

## カードのサムネイル

- 各カード上部の画像は `thumbs/` にあり、`python3 tools/make_thumbs.py` で全カード分を撮り直せる（新しいカードだけなら `--new`）。
- 教材を追加・修正したら、このスクリプトを実行してから push する。
- 元の絵文字表示に戻すときは、index.html の `<body class="thumbs">` を `<body>` にするだけ（絵文字は各カードに残してある）。
