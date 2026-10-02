# 規約

## 標準ライブラリだけで書く

依存パッケージを持たない。HTTP は `urllib`、HTML は `html.parser`、XML は `xml.etree`、設定は `tomllib`。Actions でも手元でも `python -m tg_dev_digest` だけで動く状態を保つ。

足したくなったら、標準ライブラリで数十行で済まないかを先に確かめる。

## 外部とのやり取りは引数で受け取る

`digest.run` は `fetch` / `complete` / `send` を関数として受け取る。`select.gemini_complete` と `telegram.sender` は、`http.post_json` を受け取って関数を返す工場にしてある。本物を組み立てるのは `__main__.py` だけ。

テストは偽物の関数を渡すだけで回る。モックライブラリは使わない。

## 配信元の追加は type で分ける

フィードがあるサイトは `type = "feed"` と URL の設定だけで足し、コードを書かない。コードを書くのは、フィードが無いか、欲しい並び（ランキング）がフィードに無いときだけで、`sources/` に `parse(body, source, label) -> list[Item]` を1つ足して `sources/__init__.py` の `build` に分岐を足す。

`digest.toml` の `[[source]]` にある未知のキーは `SourceConfig.options` に入る。配信元固有の設定（`trending` の `language` など）はここから読む。

## 失敗を配信元ごとに閉じる

1つの配信元の取得失敗、選別の失敗、1通の送信失敗で、実行全体を止めない。失敗は `log` に出して数え、最後に終了コード 1 を返す。選別が失敗した日は、見出しに「未選別」と付けてそのまま送る。

## 文字列

- ログは英語、Telegram に出る見出しは日本語
- Telegram には HTML モードで送るので、タイトル・説明・URL は必ず `html.escape` を通す
- コメントは日本語で、なぜそうしているかが自明でないところにだけ書く
