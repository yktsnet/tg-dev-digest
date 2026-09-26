import json
import os
import tempfile
import unittest

from tg_dev_digest import config, digest

SOURCES = {
    "hatena": {"name": "hatena", "type": "feed", "label": "はてブ", "url": "https://b.hatena.ne.jp/x.rss", "limit": 20, "filter": True},
    "zenn": {"name": "zenn", "type": "zenn", "label": "Zenn", "limit": 20, "filter": True},
    "trending": {"name": "trending", "type": "trending", "label": "GitHub", "header": "🔥 GitHub Trending", "limit": 3},
}


def zenn_body(paths):
    return json.dumps(
        {"articles": [{"title": f"title {p}", "path": f"/u/articles/{p}", "topics": []} for p in paths]}
    ).encode()


def trending_body(names):
    arts = "".join(f'<article><h2><a href="/{n}">{n}</a></h2><p>desc {n}</p></article>' for n in names)
    return f"<html>{arts}</html>".encode()


class Harness:
    def __init__(self, sources=("zenn",), limits=None, seen_max=200):
        limits = limits or {}
        data = {
            "seen": {"max": seen_max},
            "source": [{**SOURCES[n], **({"limit": limits[n]} if n in limits else {})} for n in sources],
        }
        self.cfg = config.parse(data)
        self.cfg.state_path = os.path.join(tempfile.mkdtemp(), "seen.txt")
        self.bodies = {}
        self.sent = []

    def fetch(self, url):
        for prefix, body in self.bodies.items():
            if url.startswith(prefix):
                if isinstance(body, Exception):
                    raise body
                return body
        raise AssertionError(url)

    def run(self, complete=None, send=None, save=True):
        self.sent = []
        return digest.run(
            self.cfg,
            fetch=self.fetch,
            complete=complete,
            send=send or self.sent.append,
            save=save,
            log=lambda s: None,
        )

    def sent_text(self):
        return "\n".join(self.sent)


class SeenTest(unittest.TestCase):
    def test_article_staying_on_ranking_is_not_resent(self):
        h = Harness(seen_max=3)
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        h.run()
        self.assertIn("title a", h.sent_text())
        # 別の記事が何件流れてきても、載り続けている a は押し出されない
        for i in range(10):
            h.bodies["https://zenn.dev"] = zenn_body(["a", f"n{i}", f"m{i}"])
            h.run()
            self.assertNotIn("title a", h.sent_text(), f"resent on run {i}")

    def test_article_returns_after_pushed_out(self):
        h = Harness(seen_max=2)
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        h.run()
        h.bodies["https://zenn.dev"] = zenn_body(["b", "c"])
        h.run()
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        h.run()
        self.assertIn("title a", h.sent_text())

    def test_store_keeps_at_most_max(self):
        h = Harness(seen_max=5)
        h.bodies["https://zenn.dev"] = zenn_body([str(i) for i in range(12)])
        h.run()
        with open(h.cfg.state_path) as f:
            self.assertEqual(len(f.read().split()), 5)

    def test_title_with_spaces_is_remembered(self):
        h = Harness()
        h.bodies["https://zenn.dev"] = json.dumps(
            {"articles": [{"title": "Claude Opus 5.5 による検証", "path": "/u/articles/a", "topics": []}]}
        ).encode()
        h.run()
        h.run()
        self.assertEqual(h.sent, [])

    def test_items_past_limit_stay_candidates(self):
        h = Harness(limits={"zenn": 2})
        h.bodies["https://zenn.dev"] = zenn_body(["a", "b", "c"])
        h.run()
        self.assertNotIn("title c", h.sent_text())
        h.run()
        self.assertIn("title c", h.sent_text())
        self.assertNotIn("title a", h.sent_text())

    def test_rejected_by_filter_is_not_reevaluated(self):
        h = Harness()
        h.bodies["https://zenn.dev"] = zenn_body(["a", "b"])
        prompts = []

        def complete(prompt):
            prompts.append(prompt)
            return '{"ids":[1]}'

        h.run(complete)
        self.assertNotIn("title b", h.sent_text())
        h.run(complete)
        self.assertEqual(len(prompts), 1)

    def test_failed_send_is_retried_next_run(self):
        h = Harness()
        h.bodies["https://zenn.dev"] = zenn_body(["a"])

        def boom(_):
            raise OSError("telegram down")

        self.assertEqual(h.run(send=boom), 1)
        h.run()
        self.assertIn("title a", h.sent_text())

    def test_dry_run_does_not_write_seen(self):
        h = Harness()
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        h.run(save=False)
        self.assertFalse(os.path.exists(h.cfg.state_path))
        h.run()
        self.assertIn("title a", h.sent_text())

    def test_trending_sends_next_unseen_repos(self):
        h = Harness(sources=("trending",), limits={"trending": 2})
        h.bodies["https://github.com/trending"] = trending_body(["o/a", "o/b", "o/c"])
        h.run()
        h.run()
        self.assertIn("o/c", h.sent_text())
        self.assertNotIn("o/a", h.sent_text())


class PipelineTest(unittest.TestCase):
    def test_same_url_from_two_sources_is_sent_once(self):
        h = Harness(sources=("hatena", "zenn"))
        h.bodies["https://b.hatena.ne.jp"] = (
            b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/">'
            b"<item><title>title a</title><link>https://zenn.dev/u/articles/a?utm_source=hb</link></item>"
            b"</rdf:RDF>"
        )
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        h.run()
        self.assertEqual(h.sent_text().count("title a"), 1)
        self.assertIn("[はてブ]", h.sent_text())

    def test_filter_output_keeps_full_title_and_label(self):
        h = Harness()
        long = "x" * 100
        h.bodies["https://zenn.dev"] = json.dumps(
            {"articles": [{"title": long, "path": "/u/articles/a", "topics": []}]}
        ).encode()
        h.run(lambda p: '{"ids":[1]}')
        self.assertIn(long, h.sent_text())
        self.assertIn("[Zenn]", h.sent_text())

    def test_broken_filter_falls_back_to_unfiltered(self):
        h = Harness()
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        self.assertEqual(h.run(lambda p: "sorry"), 1)
        self.assertIn("未選別", h.sent_text())
        self.assertIn("title a", h.sent_text())

    def test_one_source_failing_does_not_block_others(self):
        h = Harness(sources=("zenn", "trending"))
        h.bodies["https://zenn.dev"] = OSError("zenn down")
        h.bodies["https://github.com/trending"] = trending_body(["o/a"])
        self.assertEqual(h.run(), 1)
        self.assertIn("o/a", h.sent_text())

    def test_unfiltered_source_is_not_sent_to_model(self):
        h = Harness(sources=("zenn", "trending"))
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        h.bodies["https://github.com/trending"] = trending_body(["o/a"])
        prompts = []
        h.run(lambda p: prompts.append(p) or '{"ids":[]}')
        self.assertNotIn("o/a", prompts[0])
        self.assertIn("o/a", h.sent_text())
        self.assertNotIn("title a", h.sent_text())


if __name__ == "__main__":
    unittest.main()
