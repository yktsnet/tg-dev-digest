import argparse
import sys
from datetime import datetime, timezone, timedelta

from . import digest, http, select, telegram
from .config import Config, _list

JST = timezone(timedelta(hours=9))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="tg-dev-digest")
    ap.add_argument("--dry-run", action="store_true", help="print messages instead of sending; do not save state")
    ap.add_argument("--sources", help="override DIGEST_SOURCES (comma separated)")
    args = ap.parse_args(argv)

    cfg = Config.from_env()
    if args.sources:
        cfg.sources = _list(args.sources)

    if args.dry_run:
        def send(text: str) -> None:
            print(text, end="\n\n---\n\n")
    elif cfg.telegram_token and cfg.telegram_chat_id:
        send = telegram.sender(cfg.telegram_token, cfg.telegram_chat_id, http.post_json)
    else:
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID are not set (use --dry-run to preview)", file=sys.stderr)
        return 2

    complete = (
        select.anthropic_complete(cfg.anthropic_key, cfg.model, http.post_json) if cfg.anthropic_key else None
    )
    log = lambda s: print(s, file=sys.stderr)
    return digest.run(
        cfg,
        fetch=http.get,
        complete=complete,
        send=send,
        today=datetime.now(JST).date(),
        save=not args.dry_run,
        log=log,
    )


if __name__ == "__main__":
    sys.exit(main())
