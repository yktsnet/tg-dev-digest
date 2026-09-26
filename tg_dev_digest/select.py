import json
import re
from typing import Callable
from urllib.parse import urlsplit

from .item import Item

TITLE_CHARS = 60


def build_prompt(items: list[Item], topic: str) -> str:
    lines = []
    for i, it in enumerate(items, 1):
        tags = f" [{', '.join(it.tags)}]" if it.tags else ""
        lines.append(f"{i}. {it.title[:TITLE_CHARS]} ({urlsplit(it.url).netloc}){tags}")
    return (
        f"以下は技術系サイトの記事一覧。{topic}に関係する記事の番号を選べ。\n"
        "同じ出来事や同じ発表を扱う記事が複数あれば、1件だけ選べ。\n"
        '出力はJSONのみ: {"ids":[番号, ...]}\n\n' + "\n".join(lines)
    )


def parse_ids(text: str, count: int) -> list[int]:
    """Return 0-based indices. Raises ValueError when no id list can be found."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON in response: {text[:200]}")
    ids = json.loads(m.group()).get("ids")
    if not isinstance(ids, list):
        raise ValueError(f"no ids in response: {text[:200]}")
    picked = {int(i) - 1 for i in ids if str(i).lstrip("-").isdigit()}
    return sorted(i for i in picked if 0 <= i < count)


def select(items: list[Item], topic: str, complete: Callable[[str], str]) -> list[Item]:
    """Ask the model for numbers only.

    Asking for titles back made the model rewrite them, which broke the lookup
    and the JSON (quotes inside titles). Numbers avoid both and keep output tokens,
    the expensive side, to a few dozen.
    """
    if not items:
        return []
    ids = parse_ids(complete(build_prompt(items, topic)), len(items))
    return [items[i] for i in ids]


def anthropic_complete(api_key: str, model: str, post_json) -> Callable[[str], str]:
    def complete(prompt: str) -> str:
        result = post_json(
            "https://api.anthropic.com/v1/messages",
            {"model": model, "max_tokens": 512, "messages": [{"role": "user", "content": prompt}]},
            {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        )
        return result["content"][0]["text"]

    return complete
