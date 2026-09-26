import os
import tomllib
from dataclasses import dataclass, field


@dataclass
class SourceConfig:
    name: str
    type: str
    label: str
    limit: int
    filter: bool = False
    url: str = ""
    header: str = ""
    options: dict = field(default_factory=dict)


@dataclass
class Config:
    sources: list[SourceConfig]
    model: str
    topic: str
    filtered_header: str
    seen_max: int
    state_path: str
    anthropic_key: str = ""
    telegram_token: str = ""
    telegram_chat_id: str = ""

    def select_sources(self, names: list[str]) -> None:
        by_name = {s.name: s for s in self.sources}
        unknown = [n for n in names if n not in by_name]
        if unknown:
            raise ValueError(f"unknown source: {', '.join(unknown)} (not in the config file)")
        self.sources = [by_name[n] for n in names]


def split_names(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def parse(data: dict) -> Config:
    filt = data.get("filter", {})
    sources = []
    for raw in data.get("source", []):
        raw = dict(raw)
        if not raw.pop("enabled", True):
            continue
        name = raw.pop("name")
        sources.append(
            SourceConfig(
                name=name,
                type=raw.pop("type", "feed"),
                label=raw.pop("label", name),
                limit=int(raw.pop("limit", 10)),
                filter=bool(raw.pop("filter", False)),
                url=raw.pop("url", ""),
                header=raw.pop("header", ""),
                options=raw,
            )
        )
    return Config(
        sources=sources,
        model=filt.get("model", "claude-haiku-4-5"),
        topic=filt.get("topic", "AIやソフトウェア開発"),
        filtered_header=filt.get("header", "📰 開発 digest"),
        seen_max=int(data.get("seen", {}).get("max", 200)),
        state_path="state/seen.txt",
    )


def load(env=os.environ) -> Config:
    """Structure lives in the TOML file; the environment only carries secrets and one-off overrides."""

    # Actions の vars.* / inputs.* は未設定だと空文字で渡ってくるので、空は未設定として扱う
    def get(key: str) -> str:
        return env.get(key, "").strip()

    with open(get("DIGEST_CONFIG") or "digest.toml", "rb") as f:
        cfg = parse(tomllib.load(f))
    if get("DIGEST_SOURCES"):
        cfg.select_sources(split_names(get("DIGEST_SOURCES")))
    cfg.state_path = get("DIGEST_STATE") or cfg.state_path
    cfg.anthropic_key = get("ANTHROPIC_API_KEY")
    cfg.telegram_token = get("TELEGRAM_BOT_TOKEN")
    cfg.telegram_chat_id = get("TELEGRAM_CHAT_ID")
    return cfg
