import os
from dataclasses import dataclass


def _list(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class Config:
    sources: list[str]
    filter_sources: list[str]
    topic: str
    feeds: dict[str, str]
    limits: dict[str, int]
    hatena_category: str
    trending_language: str
    trending_since: str
    ttl_days: int
    state_path: str
    model: str
    anthropic_key: str
    telegram_token: str
    telegram_chat_id: str

    def limit(self, source: str, default: int) -> int:
        return self.limits.get(source, default)

    @classmethod
    def from_env(cls, env=os.environ) -> "Config":
        # Actions の vars.* は未設定だと空文字で渡ってくるので、空は未設定として扱う
        def get(key: str, default: str = "") -> str:
            return env.get(key, "").strip() or default

        feeds = {}
        for pair in _list(get("DIGEST_FEEDS")):
            name, sep, url = pair.partition("=")
            if not sep:
                raise ValueError(f"DIGEST_FEEDS entry must be name=url: {pair}")
            feeds[name.strip()] = url.strip()

        limits = {}
        for pair in _list(get("DIGEST_LIMITS")):
            name, _, n = pair.partition("=")
            limits[name.strip()] = int(n)

        return cls(
            sources=_list(get("DIGEST_SOURCES", "hatena,zenn,trending")),
            filter_sources=_list(get("DIGEST_FILTER_SOURCES", "hatena,zenn")),
            topic=get("DIGEST_TOPIC", "AIやソフトウェア開発"),
            feeds=feeds,
            limits=limits,
            hatena_category=get("HATENA_CATEGORY", "it"),
            trending_language=get("TRENDING_LANGUAGE"),
            trending_since=get("TRENDING_SINCE"),
            ttl_days=int(get("DIGEST_SEEN_TTL_DAYS", "30")),
            state_path=get("DIGEST_STATE", "state/seen.json"),
            model=get("ANTHROPIC_MODEL", "claude-haiku-4-5"),
            anthropic_key=get("ANTHROPIC_API_KEY"),
            telegram_token=get("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=get("TELEGRAM_CHAT_ID"),
        )
