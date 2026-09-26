"""RSS 1.0 (RDF) / RSS 2.0 / Atom をまとめて読む。"""

import xml.etree.ElementTree as ET

from ..item import Item

RSS1 = "{http://purl.org/rss/1.0/}"
ATOM = "{http://www.w3.org/2005/Atom}"
DC = "{http://purl.org/dc/elements/1.1/}"


def parse(xml: bytes, source: str, label: str) -> list[Item]:
    root = ET.fromstring(xml)
    items = []
    for node in root.iter():
        if node.tag in (f"{RSS1}item", "item"):
            ns = RSS1 if node.tag.startswith(RSS1) else ""
            title = _text(node, f"{ns}title")
            url = _text(node, f"{ns}link")
            tags = [t.text for t in node.findall(f"{DC}subject") + node.findall("category") if t.text]
        elif node.tag == f"{ATOM}entry":
            title = _text(node, f"{ATOM}title")
            link = node.find(f"{ATOM}link[@rel='alternate']")
            if link is None:
                link = node.find(f"{ATOM}link")
            url = link.get("href", "") if link is not None else ""
            tags = [c.get("term", "") for c in node.findall(f"{ATOM}category") if c.get("term")]
        else:
            continue
        if title and url:
            items.append(Item(source, label, title, url, tags))
    return items


def _text(node, tag: str) -> str:
    child = node.find(tag)
    return (child.text or "").strip() if child is not None else ""
