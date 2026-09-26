import json
import os
import tempfile
import unittest
from datetime import date, timedelta

from tg_dev_digest import digest
from tg_dev_digest.config import Config


def zenn_body(paths):
    return json.dumps(
        {"articles": [{"title": f"title {p}", "path": f"/u/articles/{p}", "topics": []} for p in paths]}
    ).encode()


def trending_body(names):
    arts = "".join(f'<article><h2><a href="/{n}">{n}</a></h2><p>desc {n}</p></article>' for n in names)
    return f"<html>{arts}</html>".encode()


class Harness:
    def __init__(self, **env):
        self.dir = tempfile.mkdtemp()
        base = {"DIGEST_STATE": os.path.join(self.dir, "seen.json"), "DIGEST_SOURCES": "zenn"}
        base.update(env)
        self.cfg = Config.from_env(base)
        self.bodies = {}
        self.sent = []

    def fetch(self, url):
        for prefix, body in self.bodies.items():
            if url.startswith(prefix):
                if isinstance(body, Exception):
                    raise body
                return body
        raise AssertionError(url)

    def run(self, day, complete=None, send=None):
        self.sent = []
        return digest.run(
            self.cfg,
            fetch=self.fetch,
            complete=complete,
            send=send or self.sent.append,
            today=day,
            log=lambda s: None,
        )

    def sent_text(self):
        return "\n".join(self.sent)


D0 = date(2026, 9, 1)


class SeenTest(unittest.TestCase):
    def test_article_staying_on_ranking_is_not_resent_every_other_day(self):
        h = Harness()
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        h.run(D0)
        self.assertIn("title a", h.sent_text())
        for i in range(1, 5):
            h.run(D0 + timedelta(days=i))
            self.assertEqual(h.sent, [], f"resent on day {i}")

    def test_article_listed_longer_than_ttl_is_not_resent(self):
        h = Harness(DIGEST_SEEN_TTL_DAYS="3")
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        h.run(D0)
        for i in range(1, 10):
            h.run(D0 + timedelta(days=i))
            self.assertEqual(h.sent, [], f"resent on day {i}")

    def test_article_returns_after_absent_for_ttl(self):
        h = Harness(DIGEST_SEEN_TTL_DAYS="3")
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        h.run(D0)
        h.bodies["https://zenn.dev"] = zenn_body([])
        h.run(D0 + timedelta(days=4))
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        h.run(D0 + timedelta(days=5))
        self.assertIn("title a", h.sent_text())

    def test_items_past_limit_stay_candidates(self):
        h = Harness(DIGEST_LIMITS="zenn=2")
        h.bodies["https://zenn.dev"] = zenn_body(["a", "b", "c"])
        h.run(D0)
        self.assertNotIn("title c", h.sent_text())
        h.run(D0 + timedelta(days=1))
        self.assertIn("title c", h.sent_text())
        self.assertNotIn("title a", h.sent_text())

    def test_rejected_by_filter_is_not_reevaluated(self):
        h = Harness()
        h.bodies["https://zenn.dev"] = zenn_body(["a", "b"])
        prompts = []

        def complete(prompt):
            prompts.append(prompt)
            return '{"ids":[1]}'

        h.run(D0, complete)
        self.assertNotIn("title b", h.sent_text())
        h.run(D0 + timedelta(days=1), complete)
        self.assertEqual(len(prompts), 1)

    def test_failed_send_is_retried_next_run(self):
        h = Harness()
        h.bodies["https://zenn.dev"] = zenn_body(["a"])

        def boom(_):
            raise OSError("telegram down")

        self.assertEqual(h.run(D0, send=boom), 1)
        h.run(D0 + timedelta(days=1))
        self.assertIn("title a", h.sent_text())

    def test_trending_sends_next_unseen_repos(self):
        h = Harness(DIGEST_SOURCES="trending", DIGEST_LIMITS="trending=2")
        h.bodies["https://github.com/trending"] = trending_body(["o/a", "o/b", "o/c"])
        h.run(D0)
        h.run(D0 + timedelta(days=1))
        self.assertIn("o/c", h.sent_text())
        self.assertNotIn("o/a", h.sent_text())


class PipelineTest(unittest.TestCase):
    def test_same_url_from_two_sources_is_sent_once(self):
        h = Harness(DIGEST_SOURCES="hatena,zenn")
        h.bodies["https://b.hatena.ne.jp"] = (
            b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/">'
            b"<item><title>title a</title><link>https://zenn.dev/u/articles/a?utm_source=hb</link></item>"
            b"</rdf:RDF>"
        )
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        h.run(D0)
        self.assertEqual(h.sent_text().count("title a"), 1)
        self.assertIn("[はてブ]", h.sent_text())

    def test_filter_output_keeps_full_title_and_label(self):
        h = Harness()
        long = "x" * 100
        h.bodies["https://zenn.dev"] = json.dumps(
            {"articles": [{"title": long, "path": "/u/articles/a", "topics": []}]}
        ).encode()
        h.run(D0, lambda p: '{"ids":[1]}')
        self.assertIn(long, h.sent_text())
        self.assertIn("[Zenn]", h.sent_text())

    def test_broken_filter_falls_back_to_unfiltered(self):
        h = Harness()
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        self.assertEqual(h.run(D0, lambda p: "sorry"), 1)
        self.assertIn("未選別", h.sent_text())
        self.assertIn("title a", h.sent_text())

    def test_one_source_failing_does_not_block_others(self):
        h = Harness(DIGEST_SOURCES="zenn,trending")
        h.bodies["https://zenn.dev"] = OSError("zenn down")
        h.bodies["https://github.com/trending"] = trending_body(["o/a"])
        self.assertEqual(h.run(D0), 1)
        self.assertIn("o/a", h.sent_text())

    def test_unfiltered_source_is_not_sent_to_model(self):
        h = Harness(DIGEST_SOURCES="zenn,trending")
        h.bodies["https://zenn.dev"] = zenn_body(["a"])
        h.bodies["https://github.com/trending"] = trending_body(["o/a"])
        prompts = []
        h.run(D0, lambda p: prompts.append(p) or '{"ids":[]}')
        self.assertNotIn("o/a", prompts[0])
        self.assertIn("o/a", h.sent_text())
        self.assertNotIn("title a", h.sent_text())


if __name__ == "__main__":
    unittest.main()
