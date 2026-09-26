# Guarantee Ledger

## Guarantees

### 1. `tests/test_digest.py` — tg_dev_digest/digest.py (run)

- フィードに載り続けている記事は、ほかの記事が何件流れてきても再送されない
- 送信に失敗した記事は覚えず、次の実行で送り直す
- `--dry-run` の回は `seen.txt` を書かず、次の本番の実行で同じ記事を送る
- 別の配信元から同じ URL が来ても1回だけ送る
- 選別の応答が解釈できないときは、見出しに「未選別」を付けて全件を送る
- 1つの配信元の取得に失敗しても、残りの配信元は送る

| 保証（要約） | 対応テスト |
|---|---|
| 載り続ける記事は再送しない | `test_article_staying_on_ranking_is_not_resent` |
| 送信失敗は送り直す | `test_failed_send_is_retried_next_run` |
| dry-run は seen を書かない | `test_dry_run_does_not_write_seen` |
| 配信元をまたぐ URL の重複 | `test_same_url_from_two_sources_is_sent_once` |
| 選別失敗時は未選別で送る | `test_broken_filter_falls_back_to_unfiltered` |
| 配信元の失敗を閉じ込める | `test_one_source_failing_does_not_block_others` |

### 2. `tests/test_units.py` — tg_dev_digest/config.py (load)

- `DIGEST_SOURCES` を渡すと、`digest.toml` のうちその配信元だけを送る。空の値は未設定として扱う

| 保証（要約） | 対応テスト |
|---|---|
| 環境変数での絞り込み | `test_env_selects_sources_and_empty_vars_are_ignored` |

## About

対象は、1回の実行で何を送り何を覚えるかと、`DIGEST_SOURCES` の解釈だけ。解析や分割などほかのテストが見ている細部は約束に含めない。**ここに載っていない振る舞いは約束ではなく、予告なく変わりうる。** 地位は design-decisions.md 相当のドキュメントと同格。
