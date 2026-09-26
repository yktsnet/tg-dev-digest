"""GitHub Trending has no API, so the HTML is read directly. A DOM change on GitHub's side breaks this."""

from html.parser import HTMLParser

from ..item import Item


def url(language: str = "", since: str = "") -> str:
    base = "https://github.com/trending"
    if language:
        base += f"/{language}"
    return base + (f"?since={since}" if since else "")


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.repos: list[dict] = []
        self._repo = None
        self._in_h2 = False
        self._in_p = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article":
            self._repo = {"name": "", "description": ""}
        if self._repo is None:
            return
        if tag == "h2":
            self._in_h2 = True
        elif tag == "a" and self._in_h2:
            href = attrs.get("href") or ""
            if href.count("/") == 2:
                self._repo["name"] = href.lstrip("/")
        elif tag == "p":
            self._in_p = True

    def handle_endtag(self, tag):
        if tag == "h2":
            self._in_h2 = False
        elif tag == "p":
            self._in_p = False
        elif tag == "article" and self._repo is not None:
            if self._repo["name"]:
                self.repos.append(self._repo)
            self._repo = None

    def handle_data(self, data):
        if self._repo is not None and self._in_p:
            self._repo["description"] += data.strip()


def parse(html: bytes, source: str = "trending", label: str = "GitHub") -> list[Item]:
    parser = _Parser()
    parser.feed(html.decode("utf-8", errors="replace"))
    return [
        Item(source, label, r["name"], f"https://github.com/{r['name']}", description=r["description"])
        for r in parser.repos
    ]
