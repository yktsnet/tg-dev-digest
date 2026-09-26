[🇯🇵 日本語](guarantees.md) | [🇬🇧 English](guarantees.en.md)

# Guarantee Ledger

## Guarantees

### 1. `tests/test_digest.py` — tg_dev_digest/digest.py (run)

- An article that stays on a feed is never re-sent, no matter how many other articles come through
- An article whose send failed is not recorded and is sent again on the next run
- A `--dry-run` run does not write `seen.txt`, and the next real run sends the same articles
- The same URL arriving from different sources is sent only once
- When the filter response cannot be parsed, everything is sent with an "未選別" (unfiltered) header
- If fetching one source fails, the remaining sources are still sent

| Guarantee (summary) | Test |
|---|---|
| No re-send while listed | `test_article_staying_on_ranking_is_not_resent` |
| Failed sends are retried | `test_failed_send_is_retried_next_run` |
| Dry run does not write seen | `test_dry_run_does_not_write_seen` |
| Cross-source URL duplicates | `test_same_url_from_two_sources_is_sent_once` |
| Unfiltered fallback on filter failure | `test_broken_filter_falls_back_to_unfiltered` |
| Source failures are contained | `test_one_source_failing_does_not_block_others` |

### 2. `tests/test_units.py` — tg_dev_digest/config.py (load)

- Passing `DIGEST_SOURCES` sends only those sources from `digest.toml`. An empty value is treated as unset

| Guarantee (summary) | Test |
|---|---|
| Narrowing by environment variable | `test_env_selects_sources_and_empty_vars_are_ignored` |

## About

Covers only what a run sends and records, and how `DIGEST_SOURCES` is interpreted. Details checked by other tests, such as parsing and message splitting, are not part of the promise. **Behavior not listed here is not a promise and may change without notice.** This document has the same standing as design-decisions.md.
