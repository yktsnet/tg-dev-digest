from dataclasses import dataclass
from typing import Callable

from ..item import Item
from . import feed, trending, zenn


@dataclass
class Source:
    name: str
    url: str
    parse: Callable[[bytes], list[Item]]
    limit: int


def build(cfg) -> list[Source]:
    """Resolve DIGEST_SOURCES into fetchable sources, in the configured order."""
    builtin = {
        "hatena": lambda: Source(
            "hatena",
            f"https://b.hatena.ne.jp/hotentry/{cfg.hatena_category}.rss",
            lambda b: feed.parse(b, "hatena", "はてブ"),
            cfg.limit("hatena", 20),
        ),
        "zenn": lambda: Source("zenn", zenn.URL, zenn.parse, cfg.limit("zenn", 20)),
        "trending": lambda: Source(
            "trending",
            trending.url(cfg.trending_language, cfg.trending_since),
            trending.parse,
            cfg.limit("trending", 3),
        ),
    }
    out = []
    for name in cfg.sources:
        if name in builtin:
            out.append(builtin[name]())
        elif name in cfg.feeds:
            out.append(
                Source(
                    name,
                    cfg.feeds[name],
                    lambda b, n=name: feed.parse(b, n, n),
                    cfg.limit(name, 10),
                )
            )
        else:
            raise ValueError(f"unknown source: {name} (define it in DIGEST_FEEDS)")
    return out
