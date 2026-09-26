from dataclasses import dataclass, field
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = {"fbclid", "gclid", "ref", "ref_src"}


@dataclass
class Item:
    source: str
    label: str
    title: str
    url: str
    tags: list[str] = field(default_factory=list)
    description: str = ""

    @property
    def key(self) -> str:
        return normalize_url(self.url)


def normalize_url(url: str) -> str:
    """Collapse URLs that point at the same page so the seen list can match them."""
    parts = urlsplit(url.strip())
    host = parts.netloc.lower()
    # http と https で同じ記事が配られることがあるため、スキームは区別しない
    query = urlencode(
        [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if not k.startswith("utm_") and k not in TRACKING_PARAMS
        ]
    )
    path = parts.path.rstrip("/") or "/"
    return urlunsplit(("https", host, path, query, ""))
