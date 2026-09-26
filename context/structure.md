# 構成

```
tg_dev_digest/
├── __main__.py      # CLI。config を読み、本物の http / Anthropic / Telegram を組み立てて digest.run に渡す
├── config.py        # digest.toml と環境変数の読み込み
├── digest.py        # 取得 → 重複除外 → 選別 → 送信 → seen 更新
├── item.py          # Item と URL の正規化
├── seen.py          # seen.txt（直近 N 件の URL）
├── select.py        # Haiku へのプロンプトと番号の解釈
├── telegram.py      # メッセージの組み立てと分割、sendMessage
├── http.py          # urllib の GET / POST JSON
└── sources/
    ├── __init__.py  # SourceConfig の type から取得先と解析関数を決める
    ├── feed.py      # RSS 1.0 / 2.0 / Atom
    ├── zenn.py      # Zenn API（デイリーランキング）
    └── trending.py  # GitHub Trending の HTML
tests/
├── test_digest.py   # digest.run を偽物の fetch / complete / send で回す
└── test_units.py    # 正規化・フィード解析・番号の解釈・分割・設定
digest.toml          # 配信元・件数・選別の設定
.github/workflows/
├── digest.yml       # 日次実行。state ブランチの読み書きもここ
└── ci.yml           # テスト
worker/
├── wrangler.jsonc   # Cron Trigger と dispatch 先
└── src/index.js     # scheduled で workflow_dispatch を POST するだけ
```

## 起動の経路

定刻の起動は `worker/` の Cron Trigger が `workflow_dispatch` で行う。`digest.yml` の schedule は保険で、`Load state` が `state` ブランチの最終コミットを見て、20時間以内なら後続の step を飛ばす。この判定は schedule のときだけで、手動や Worker からの dispatch には効かない。

## 1回の実行の流れ

1. `config.load` が `digest.toml` を読み、`DIGEST_SOURCES` があればその配信元だけに絞る
2. `digest.collect` が配信元ごとに取得し、各フィードを3つに分ける
   - seen にある URL → `alive`（新しい側へ移すだけ）
   - seen に無く、上限以内 → その回の新着
   - seen に無く、上限を超えた → 触らない（翌日以降の候補に残る）
3. `filter = true` の配信元の新着を1つの `Section` に集め、`select.select` で Haiku に番号を選ばせる。それ以外の配信元は配信元ごとの `Section` になる
4. `Section` ごとに `telegram.render` で 4000 字以下に分けて送る。送れた `Section` の `evaluated`（選別で落ちた分を含む）を seen に入れる
5. `seen.txt` を直近 `[seen].max` 件に切り詰めて保存する

## state ブランチ

`seen.txt` は main ではなく `state` ブランチに置く。`digest.yml` が実行前に `git show` で取り出し、実行後に `hash-object` → `mktree` → `commit-tree` で親の無い1コミットを作って force-push する。履歴は残らず、main も汚れない。

`--dry-run` と `dry_run` 入力のときは保存しない。
