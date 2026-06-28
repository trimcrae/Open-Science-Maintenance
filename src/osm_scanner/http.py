"""Thin HTTP client with caching, retry/backoff, and GitHub rate-limit handling.

The actual network call is isolated behind a ``transport`` callable so tests can
inject a fake that serves fixture payloads — no HTTP-mocking library required.

A transport is ``(method, url, headers) -> (status, headers, body_text)``.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable

from .cache import Cache

Transport = Callable[[str, str, dict], "tuple[int, dict, str]"]


class HttpError(Exception):
    def __init__(self, status: int, url: str, message: str = ""):
        super().__init__(f"HTTP {status} for {url}: {message}")
        self.status = status
        self.url = url


class RateLimited(HttpError):
    """Raised when GitHub rate limit is exhausted and waiting is not viable."""


def urllib_transport(method: str, url: str, headers: dict) -> tuple[int, dict, str]:
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, dict(resp.headers), resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace") if e.fp else ""
        return e.code, dict(e.headers or {}), body
    except urllib.error.URLError as e:
        # Connection-level failure (DNS, TLS, or a proxy CONNECT denial). Map to an
        # HTTP-like status so sources can degrade instead of the run aborting.
        # A policy denial ("403"/"Tunnel connection failed") is not retryable -> 403;
        # anything else is treated as transient -> 503 (the client will back off/retry).
        msg = str(e.reason) if e.reason is not None else str(e)
        status = 403 if ("403" in msg or "Tunnel connection failed" in msg) else 503
        return status, {}, msg


class HttpClient:
    def __init__(
        self,
        cache: Cache,
        token: str | None = None,
        transport: Transport = urllib_transport,
        sleep: Callable[[float], None] = time.sleep,
        max_retries: int = 4,
        max_ratelimit_wait: float = 90.0,
    ):
        self.cache = cache
        self.token = token
        self.transport = transport
        self.sleep = sleep
        self.max_retries = max_retries
        self.max_ratelimit_wait = max_ratelimit_wait

    def get_json(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        source: str = "generic",
        ttl: float | None = None,
    ) -> dict | list:
        full_url = url
        if params:
            full_url = url + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

        key = Cache.key(source, "GET", full_url, None)
        cached = self.cache.get(key, ttl)
        if cached is not None:
            if cached["status"] >= 400:
                raise HttpError(cached["status"], full_url, "cached error")
            return cached["body"]

        status, resp_headers, body_text = self._request_with_retries("GET", full_url, headers or {})

        if status >= 400:
            # Cache only "definitive" client errors (e.g. 404 = no such package/release)
            # so we don't refetch them; never cache 5xx/429.
            if status in (404, 410):
                self.cache.set(key, status, None)
            raise HttpError(status, full_url, body_text[:200])

        body = json.loads(body_text) if body_text.strip() else {}
        self.cache.set(key, status, body, fetched_at=resp_headers.get("Date"))
        return body

    def _request_with_retries(self, method: str, url: str, headers: dict):
        hdrs = dict(headers)
        hdrs.setdefault("Accept", "application/json")
        hdrs.setdefault("User-Agent", "osm-scanner")
        if self.token and "api.github.com" in url:
            hdrs["Authorization"] = f"Bearer {self.token}"
            hdrs.setdefault("Accept", "application/vnd.github+json")

        attempt = 0
        while True:
            status, resp_headers, body = self.transport(method, url, hdrs)

            # GitHub rate limiting.
            if status in (403, 429) and resp_headers.get("X-RateLimit-Remaining") == "0":
                wait = self._ratelimit_wait(resp_headers)
                if wait <= self.max_ratelimit_wait:
                    self.sleep(wait)
                    attempt += 1
                    if attempt <= self.max_retries:
                        continue
                raise RateLimited(status, url, "rate limit exhausted")

            # Transient server errors -> exponential backoff.
            if status >= 500 and attempt < self.max_retries:
                self.sleep(2**attempt)
                attempt += 1
                continue

            return status, resp_headers, body

    @staticmethod
    def _ratelimit_wait(resp_headers: dict) -> float:
        reset = resp_headers.get("X-RateLimit-Reset")
        if reset:
            try:
                return max(0.0, float(reset) - time.time())
            except ValueError:
                pass
        return 60.0
