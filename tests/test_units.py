import os
import tempfile
import tomllib
import unittest

from tg_dev_digest import config, select, sources, telegram
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
    def write(self, text):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "digest.toml")
        with open(path, "w") as f:
            f.write(text)
        return path

    def test_repo_config_loads(self):
        cfg = config.load({"DIGEST_CONFIG": "digest.toml"})
        self.assertEqual([s.name for s in cfg.sources], ["hatena", "zenn", "trending"])
        self.assertEqual(cfg.seen_max, 200)
        self.assertEqual([s.name for s in cfg.sources if s.filter], ["hatena", "zenn"])

    def test_env_selects_sources_and_empty_vars_are_ignored(self):
        path = self.write(TOML)
        cfg = config.load({"DIGEST_CONFIG": path, "DIGEST_SOURCES": "trending", "ANTHROPIC_API_KEY": ""})
        self.assertEqual([s.name for s in cfg.sources], ["trending"])
        cfg = config.load({"DIGEST_CONFIG": path, "DIGEST_SOURCES": " "})
        self.assertEqual([s.name for s in cfg.sources], ["zenn", "trending"])

    def test_disabled_and_unknown_sources(self):
        path = self.write(TOML)
        with self.assertRaises(ValueError):
            config.load({"DIGEST_CONFIG": path, "DIGEST_SOURCES": "qiita"})

    def test_extra_keys_become_options(self):
        cfg = config.parse(tomllib.loads(TOML))
        trending = cfg.sources[1]
        self.assertEqual(trending.options, {"language": "python"})
        self.assertEqual(sources.build(trending).url, "https://github.com/trending/python")


TOML = """
[[source]]
name = "zenn"
type = "zenn"
limit = 5
filter = true

[[source]]
name = "trending"
type = "trending"
language = "python"

[[source]]
name = "qiita"
url = "https://qiita.com/popular-items/feed"
enabled = false
"""


if __name__ == "__main__":
    unittest.main()
