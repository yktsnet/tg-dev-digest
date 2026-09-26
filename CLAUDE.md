@~/.claude/CLAUDE.md
@context/conventions.md
@context/structure.md
@context/domain.md

# tg-dev-digest

はてブ・Zenn・GitHub Trending から開発まわりの記事を集め、Claude Haiku に選ばせて Telegram へ送る日次バッチ。GitHub Actions だけで動き、サーバーを持たない。

フェーズは **MVP期**。相談者が開放チャットで直接実装してよい。保証台帳（`docs/guarantees.md`）が正式運用になった時点で Issueドリブン期へ上げる。

## コマンド

```bash
python -m tg_dev_digest --dry-run                    # 実データを取り、送らずに標準出力へ。seen も書かない
python -m tg_dev_digest --dry-run --sources trending # digest.toml から一部だけ
python -m unittest discover -s tests                 # テスト
```

`worker/` は定刻に `workflow_dispatch` を叩くだけの Cloudflare Worker（JS、依存なし）。デプロイと `wrangler secret` は user が行う。

依存は Python 3.11 以上の標準ライブラリだけ（`tomllib` を使う）。ビルドも pip install も無い。

## 検証手段

PR 前に必ず `python -m unittest discover -s tests` を通す。CI（`.github/workflows/ci.yml`）も同じコマンドを走らせる。

配信元の解析を触ったら `python -m tg_dev_digest --dry-run` で実データを1回取り、件数とメッセージの形を目視する。`ANTHROPIC_API_KEY` を渡さなければ選別は飛ばされ、「未選別」の見出しで出る。

## 検証手順の雛形

Agent 側で完結しない確認は user に渡す。

- Actions の `digest` を `dry_run` で手動起動し、ログの選別結果とメッセージを確かめる
- 本番の配信（Telegram に届くこと）と、`state` ブランチの `seen.txt` が更新されること

## 触るときの注意

- **Haiku にはタイトルを返させない。** 番号だけを返させ、タイトル・URL・配信元はこちらの `Item` から出す。タイトルを返させると突き合わせと JSON が壊れる
- **送信に成功した分だけ seen に入れる。** 失敗した分を入れると二度と届かない
- 外部とのやり取り（HTTP・LLM・Telegram）は `digest.run` の引数で受け取る。`digest.py` から `http` を import しない。テストは偽物を渡して回す
- 配信元・件数・選別の設定は `digest.toml` に置く。環境変数に構造のある設定を足さない（秘密情報と `DIGEST_SOURCES` の絞り込みだけ）
