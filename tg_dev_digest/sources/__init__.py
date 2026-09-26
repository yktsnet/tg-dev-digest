from dataclasses import dataclass
from typing import Callable

from ..config import SourceConfig
from ..item import Item
from . import feed, trending, zenn


@dataclass
class Source:
    cfg: SourceConfig
    url: str
    parse: Callable[[bytes], list[Item]]

    @property
    def name(self) -> str:
        return self.cfg.name

    @property
    def limit(self) -> int:
        return self.cfg.limit


def build(sc: SourceConfig) -> Source:
    if sc.type == "feed":
        if not sc.url:
            raise ValueError(f"{sc.name}: type = \"feed\" needs url")
        return Source(sc, sc.url, lambda b: feed.parse(b, sc.name, sc.label))
    if sc.type == "zenn":
        return Source(sc, sc.url or zenn.URL, lambda b: zenn.parse(b, sc.name, sc.label))
    if sc.type == "trending":
        url = sc.url or trending.url(sc.options.get("language", ""), sc.options.get("since", ""))
        return Source(sc, url, lambda b: trending.parse(b, sc.name, sc.label))
    raise ValueError(f"{sc.name}: unknown type {sc.type!r} (feed / zenn / trending)")
