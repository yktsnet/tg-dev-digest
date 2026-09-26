import os


class SeenStore:
    """The most recent `max_size` URLs, oldest first.

    A URL that is still listed on a feed is moved to the end every run, so an
    article that stays on a ranking never falls out and gets re-sent. Only URLs
    that have dropped off every feed age out.
    """

    def __init__(self, urls: list[str], max_size: int):
        self.urls = list(dict.fromkeys(urls))
        self.max_size = max_size

    @classmethod
    def load(cls, path: str, max_size: int) -> "SeenStore":
        if not os.path.exists(path):
            return cls([], max_size)
        with open(path, encoding="utf-8") as f:
            return cls([line.strip() for line in f if line.strip()], max_size)

    def __contains__(self, key: str) -> bool:
        return key in self.urls

    def touch(self, keys) -> None:
        keys = list(dict.fromkeys(keys))
        moved = set(keys)
        self.urls = [u for u in self.urls if u not in moved] + keys
        self.urls = self.urls[-self.max_size :]

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(u + "\n" for u in self.urls)
