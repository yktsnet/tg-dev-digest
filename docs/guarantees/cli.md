# cli

| 保証 | 対応テスト |
|---|---|
| `--sources` を渡すと、`digest.toml` のうちその配信元だけを対象にする | `test_sources_flag_selects_sources` |
| Telegram の認証情報が無く `--dry-run` でもなければ、実行せずに終了コード 2 を返す | `test_missing_telegram_credentials_exit_2_without_running` |
