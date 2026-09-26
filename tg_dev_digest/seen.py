import json
import os
from datetime import date, timedelta


class SeenStore:
    """URL → the last date it was observed in any feed.

    Keeping the *last* observation rather than the first means an article that
    stays on a ranking for weeks is never re-sent; it only becomes new again
    after it has been absent from every feed for `ttl_days`.
    """

    def __init__(self, entries: dict[str, str], ttl_days: int):
        self.entries = dict(entries)
        self.ttl_days = ttl_days

    @classmethod
    def load(cls, path: str, ttl_days: int) -> "SeenStore":
        if not os.path.exists(path):
            return cls({}, ttl_days)
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f), ttl_days)

    def __contains__(self, key: str) -> bool:
        return key in self.entries

    def touch(self, keys, today: date) -> None:
        stamp = today.isoformat()
        for key in keys:
            self.entries[key] = stamp

    def prune(self, today: date) -> None:
        cutoff = (today - timedelta(days=self.ttl_days)).isoformat()
        self.entries = {k: v for k, v in self.entries.items() if v >= cutoff}

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dict(sorted(self.entries.items())), f, ensure_ascii=False, indent=0)
            f.write("\n")
