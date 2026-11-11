# run

## seen と再送

| 保証 | 対応テスト |
|---|---|
| フィードに載り続けている記事は、ほかの記事が何件流れてきても再送されない | `test_article_staying_on_ranking_is_not_resent` |
| seen から押し出された記事は、再びフィードに載れば送られる | `test_article_returns_after_pushed_out` |
| `seen.txt` は `[seen].max` 件を超えて URL を持たない | `test_store_keeps_at_most_max` |
| タイトルに空白を含む記事も、送ったあとは再送されない | `test_title_with_spaces_is_remembered` |
| 配信元の `limit` を超えて扱わなかった新着は、次の実行で候補になる | `test_items_past_limit_stay_candidates` |
| 選別しない配信元は、次の実行で、まだ送っていない続きの記事を送る | `test_trending_sends_next_unseen_repos` |

## 失敗と dry-run

| 保証 | 対応テスト |
|---|---|
| 送信に失敗した記事は覚えず、次の実行で送り直す | `test_failed_send_is_retried_next_run` |
| 送信に失敗した回は終了コード 1 を返す | `test_failed_send_is_retried_next_run` |
| `save=False`（`--dry-run`）の回は `seen.txt` を書かない | `test_dry_run_does_not_write_seen` |
| `save=False`（`--dry-run`）の回に出した記事は、次の本番の実行で送る | `test_dry_run_does_not_write_seen` |
| 1つの配信元の取得に失敗しても、残りの配信元は送る | `test_one_source_failing_does_not_block_others` |
| 配信元の取得に失敗した回は終了コード 1 を返す | `test_one_source_failing_does_not_block_others` |
| 取得・選別・送信に失敗が無い回は終了コード 0 を返す | `test_clean_run_returns_zero` |

## 選別

| 保証 | 対応テスト |
|---|---|
| 選別で選ばれなかった記事は送らない | `test_rejected_by_filter_is_not_reevaluated` |
| 選別で選ばれなかった記事は、次の実行で選別モデルに再び渡さない | `test_rejected_by_filter_is_not_reevaluated` |
| 選別で選ばれた記事は、配信元の完全なタイトルで送る | `test_filter_output_keeps_full_title_and_label` |
| 選別の応答が解釈できないときは、見出しに「未選別」を付けて全件を送る | `test_broken_filter_falls_back_to_unfiltered` |
| 選別の応答が解釈できなかった回は終了コード 1 を返す | `test_broken_filter_falls_back_to_unfiltered` |
| `filter = true` でない配信元の記事は選別モデルに渡さず、選別の結果によらず送る | `test_unfiltered_source_is_not_sent_to_model` |

## 重複除外

| 保証 | 対応テスト |
|---|---|
| 別の配信元から同じ URL が来ても、1回だけ送る | `test_same_url_from_two_sources_is_sent_once` |
| スキーム・ホストの大小・末尾のスラッシュ・フラグメント・`utm_` パラメータだけが違う URL は同じ記事として扱う | `test_collapses_variants` |
| 意味のあるクエリが違う URL は別の記事として扱う | `test_keeps_meaningful_query` |
