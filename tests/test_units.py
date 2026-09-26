import unittest

from tg_dev_digest import select, telegram
from tg_dev_digest.config import Config
from tg_dev_digest.item import Item, normalize_url
from tg_dev_digest.sources import feed


class NormalizeUrlTest(unittest.TestCase):
    def test_collapses_variants(self):
        base = normalize_url("https://example.com/a")
        for v in [
            "http://example.com/a",
            "https://EXAMPLE.com/a/",
            "https://example.com/a#top",
            "https://example.com/a?utm_source=x&utm_medium=y",
        ]:
            self.assertEqual(normalize_url(v), base, v)

    def test_keeps_meaningful_query(self):
        self.assertNotEqual(normalize_url("https://e.com/?p=1"), normalize_url("https://e.com/?p=2"))


class FeedTest(unittest.TestCase):
    def test_rss2(self):
        xml = b"<rss><channel><item><title>T</title><link>https://e.com/1</link><category>c</category></item></channel></rss>"
        [it] = feed.parse(xml, "s", "S")
        self.assertEqual((it.title, it.url, it.tags), ("T", "https://e.com/1", ["c"]))

    def test_atom(self):
        xml = (
            b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>T</title>'
            b'<link rel="alternate" href="https://e.com/1"/><category term="c"/></entry></feed>'
        )
        [it] = feed.parse(xml, "s", "S")
        self.assertEqual((it.title, it.url, it.tags), ("T", "https://e.com/1", ["c"]))


class SelectTest(unittest.TestCase):
    def test_parse_ids_ignores_out_of_range_and_duplicates(self):
        self.assertEqual(select.parse_ids('ok {"ids":[2, 2, 9, 0, "1"]}', 3), [0, 1])

    def test_parse_ids_rejects_missing_list(self):
        with self.assertRaises(ValueError):
            select.parse_ids('{"items":[]}', 3)


class TelegramTest(unittest.TestCase):
    def test_escapes_and_splits(self):
        items = [Item("s", "L", "<b>&" + str(i), f"https://e.com/{i}") for i in range(200)]
        msgs = telegram.render("H", items)
        self.assertGreater(len(msgs), 1)
        self.assertTrue(all(len(m) <= telegram.LIMIT for m in msgs))
        self.assertIn("&lt;b&gt;&amp;0", msgs[0])


class ConfigTest(unittest.TestCase):
    def test_empty_actions_vars_fall_back_to_defaults(self):
        cfg = Config.from_env({"DIGEST_SOURCES": "", "DIGEST_SEEN_TTL_DAYS": " "})
        self.assertEqual(cfg.sources, ["hatena", "zenn", "trending"])
        self.assertEqual(cfg.ttl_days, 30)

    def test_feeds_and_limits(self):
        cfg = Config.from_env(
            {"DIGEST_FEEDS": "pk=https://e.com/feed?a=1", "DIGEST_LIMITS": "zenn=5, pk=3"}
        )
        self.assertEqual(cfg.feeds, {"pk": "https://e.com/feed?a=1"})
        self.assertEqual((cfg.limit("zenn", 20), cfg.limit("pk", 10), cfg.limit("hatena", 20)), (5, 3, 20))


if __name__ == "__main__":
    unittest.main()
