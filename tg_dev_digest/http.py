import json
import urllib.request

UA = "tg-dev-digest (+https://github.com/yktsnet/tg-dev-digest)"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read()


def post_json(url: str, payload: dict, headers: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json", "User-Agent": UA, **headers},
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.loads(res.read())
