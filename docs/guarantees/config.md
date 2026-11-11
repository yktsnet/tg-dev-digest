# config

| 保証 | 対応テスト |
|---|---|
| `DIGEST_SOURCES` を渡すと、`digest.toml` のうちその配信元だけを対象にする | `test_env_selects_sources_and_empty_vars_are_ignored` |
| 空白だけの環境変数は未設定として扱う | `test_env_selects_sources_and_empty_vars_are_ignored` |
| `DIGEST_SOURCES` に無効または未知の配信元を名指しすると `ValueError` を送出する | `test_disabled_and_unknown_sources` |
| `[[source]]` の未知のキーは `SourceConfig.options` に入る | `test_extra_keys_become_options` |
| `type = "trending"` の配信元に `language` を書くと、取得先は `https://github.com/trending/<language>` になる | `test_extra_keys_become_options` |
| `enabled = false` の配信元は対象に入らない | `test_disabled_source_is_not_loaded` |
