# message

| 保証 | 対応テスト |
|---|---|
| `telegram.render` の返す各メッセージは `telegram.LIMIT`（4000字）以下である | `test_escapes_and_splits` |
| `telegram.render` は1通に収まらない記事を複数のメッセージに分ける | `test_escapes_and_splits` |
| `telegram.render` はタイトルを HTML エスケープする | `test_escapes_and_splits` |
| 選別した記事には `[ラベル]` の形で配信元のラベルを付ける | `test_filter_output_keeps_full_title_and_label` |
