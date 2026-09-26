from dataclasses import dataclass, field
from typing import Callable

from . import select, sources, telegram
from .item import Item
from .seen import SeenStore



@dataclass
class Section:
    header: str
    items: list[Item] = field(default_factory=list)
    # 選別で落ちた記事も含めて、この回で判定を終えたもの。送信に成功したら seen に入れる
    evaluated: list[str] = field(default_factory=list)
    with_label: bool = False


def collect(srcs, fetch, store: SeenStore, log) -> tuple[dict[str, list[Item]], list[str], int]:
    """Fetch every source and split each feed into new items and still-listed seen ones.

    Seen items that are still on a feed are returned as `alive` and moved to the
    newest end of the store, so a long-listed article never ages out and returns.
    New items past the limit are left untouched so a later run can still pick them.
    """
    fresh: dict[str, list[Item]] = {}
    alive: list[str] = []
    batch: set[str] = set()
    failures = 0
    for src in srcs:
        try:
            items = src.parse(fetch(src.url))
        except Exception as e:  # 1つの配信元が落ちても、残りは届ける
            log(f"{src.name}: fetch failed: {e}")
            failures += 1
            continue
        picked = []
        for it in items:
            if it.key in batch:
                continue
            if it.key in store:
                alive.append(it.key)
                batch.add(it.key)
            elif len(picked) < src.limit:
                picked.append(it)
                batch.add(it.key)
        fresh[src.name] = picked
        log(f"{src.name}: {len(items)} fetched, {len(picked)} new")
    return fresh, alive, failures


def run(
    cfg,
    *,
    fetch: Callable[[str], bytes],
    complete: Callable[[str], str] | None,
    send: Callable[[str], None],
    save: bool = True,
    log: Callable[[str], None] = print,
) -> int:
    store = SeenStore.load(cfg.state_path, cfg.seen_max)
    srcs = [sources.build(sc) for sc in cfg.sources]
    fresh, alive, failures = collect(srcs, fetch, store, log)
    store.touch(alive)

    sections: list[Section] = []
    pool = Section(cfg.filtered_header, with_label=True)
    for src in srcs:
        if src.name not in fresh:
            continue
        items = fresh[src.name]
        if src.cfg.filter:
            if not any(sec is pool for sec in sections):
                sections.append(pool)
            pool.items += items
        else:
            header = src.cfg.header or f"🗞 {src.cfg.label}"
            sections.append(Section(header, items, [it.key for it in items]))

    if pool.items:
        pool.evaluated = [it.key for it in pool.items]
        if complete is None:
            pool.header += "（未選別）"
            log("filter: ANTHROPIC_API_KEY not set, sending unfiltered")
        else:
            try:
                pool.items = select.select(pool.items, cfg.topic, complete)
                log(f"filter: {len(pool.evaluated)} -> {len(pool.items)}")
            except Exception as e:
                # 選別は緩くてよい用途なので、落ちた日は未選別のまま届ける
                pool.header += "（選別失敗・未選別）"
                log(f"filter: failed, sending unfiltered: {e}")
                failures += 1

    for sec in sections:
        try:
            if sec.items:
                for msg in telegram.render(sec.header, sec.items, sec.with_label):
                    send(msg)
        except Exception as e:
            log(f"send failed ({sec.header}): {e}")
            failures += 1
            continue
        store.touch(sec.evaluated)

    if save:
        store.save(cfg.state_path)
    return 1 if failures else 0
