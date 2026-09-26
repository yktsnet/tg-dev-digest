import html

from .item import Item

LIMIT = 4000  # sendMessage は 4096 文字まで。見出しや区切りの分を残す


def format_item(it: Item, with_label: bool) -> str:
    label = f"[{html.escape(it.label)}] " if with_label else ""
    line = f"• {label}<b>{html.escape(it.title)}</b>"
    if it.description:
        line += f"\n{html.escape(it.description)}"
    return line + f"\n{html.escape(it.url)}"


def render(header: str, items: list[Item], with_label: bool = True) -> list[str]:
    """Split into messages that each fit under Telegram's length limit."""
    messages, current = [], f"<b>{html.escape(header)}</b>"
    for it in items:
        block = format_item(it, with_label)
        if len(current) + len(block) + 2 > LIMIT:
            messages.append(current)
            current = block
        else:
            current += "\n\n" + block
    messages.append(current)
    return messages


def sender(token: str, chat_id: str, post_json):
    def send(text: str) -> None:
        post_json(
            f"https://api.telegram.org/bot{token}/sendMessage",
            {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
            {},
        )

    return send
