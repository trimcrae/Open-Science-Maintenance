import pytest
from tests.conftest import FakeTransport, path_is

from osm_scanner.cache import Cache
from osm_scanner.http import HttpClient, HttpError, RateLimited


def make_client(tmp_path, transport, **kw):
    cache = Cache(str(tmp_path / "cache"), enabled=True)
    return HttpClient(cache=cache, transport=transport, sleep=lambda s: None, **kw)


def test_cache_avoids_second_network_call(tmp_path):
    t = FakeTransport().add(path_is("/thing"), body={"v": 1})
    http = make_client(tmp_path, t)
    a = http.get_json("https://x.test/thing", ttl=3600)
    b = http.get_json("https://x.test/thing", ttl=3600)
    assert a == b == {"v": 1}
    assert t.call_count == 1  # second call served from cache


def test_refresh_bypasses_read_but_writes(tmp_path):
    t = FakeTransport().add(path_is("/thing"), body={"v": 1})
    cache = Cache(str(tmp_path / "cache"), enabled=True, refresh=True)
    http = HttpClient(cache=cache, transport=t, sleep=lambda s: None)
    http.get_json("https://x.test/thing", ttl=3600)
    http.get_json("https://x.test/thing", ttl=3600)
    assert t.call_count == 2  # refresh ignores cached reads


def test_ttl_expiry(tmp_path):
    key = Cache.key("s", "GET", "u", None)
    cache = Cache(str(tmp_path / "cache"), enabled=True)
    cache.set(key, 200, {"v": 1})
    assert cache.get(key, ttl=3600) is not None
    assert cache.get(key, ttl=-1) is None  # already older than a negative ttl


def test_404_raises_and_is_cached(tmp_path):
    t = FakeTransport().add(path_is("/missing"), status=404, body={"message": "nope"})
    http = make_client(tmp_path, t)
    with pytest.raises(HttpError):
        http.get_json("https://x.test/missing", ttl=3600)
    with pytest.raises(HttpError):
        http.get_json("https://x.test/missing", ttl=3600)
    assert t.call_count == 1  # 404 cached, not refetched


def test_retry_on_500_then_success(tmp_path):
    calls = {"n": 0}

    def flaky(method, url, headers):
        calls["n"] += 1
        if calls["n"] < 3:
            return (500, {}, "")
        return (200, {}, '{"ok": true}')

    http = make_client(tmp_path, flaky)
    assert http.get_json("https://x.test/y", ttl=3600) == {"ok": True}
    assert calls["n"] == 3


def test_ratelimit_raises_when_wait_too_long(tmp_path):
    def limited(method, url, headers):
        return (403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "99999999999"}, "")

    http = make_client(tmp_path, limited, max_ratelimit_wait=1.0)
    with pytest.raises(RateLimited):
        http.get_json("https://api.github.com/x", ttl=3600)
