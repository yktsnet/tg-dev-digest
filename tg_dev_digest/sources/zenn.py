import json

from ..item import Item

URL = "https://zenn.dev/api/articles?order=daily&count=50"


def parse(body: bytes, source: str = "zenn", label: str = "Zenn") -> list[Item]:
    data = json.loads(body)
    return [
        Item(
            source,
            label,
            a.get("title", ""),
            f"https://zenn.dev{a.get('path', '')}",
            [t["name"] for t in a.get("topics", []) if t.get("name")],
        )
        for a in data.get("articles", [])
        if a.get("path")
    ]
