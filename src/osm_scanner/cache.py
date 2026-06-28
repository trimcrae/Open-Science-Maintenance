"""Content-addressed, on-disk JSON cache.

Makes scans idempotent: a warm cache yields byte-identical output and issues zero
network calls, which is exactly what lets the test suite (and CI) run offline.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any


class Cache:
    def __init__(self, root: str, enabled: bool = True, refresh: bool = False):
        self.root = root
        self.enabled = enabled
        self.refresh = refresh  # if True, ignore reads but still write
        if enabled:
            os.makedirs(root, exist_ok=True)

    @staticmethod
    def key(source: str, method: str, url: str, params: dict | None) -> str:
        parts = [source, method.upper(), url]
        if params:
            parts.append(json.dumps(params, sort_keys=True, separators=(",", ":")))
        digest = hashlib.sha256("\n".join(parts).encode()).hexdigest()
        return digest

    def _path(self, key: str) -> str:
        return os.path.join(self.root, f"{key}.json")

    def get(self, key: str, ttl: float | None) -> dict | None:
        """Return cached entry dict {status, body, fetched_at} or None if absent/stale."""
        if not self.enabled or self.refresh:
            return None
        path = self._path(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, encoding="utf-8") as fh:
                entry = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return None
        if ttl is not None:
            age = time.time() - entry.get("_cached_ts", 0)
            if age > ttl:
                return None
        return entry

    def set(self, key: str, status: int, body: Any, fetched_at: str | None = None) -> None:
        if not self.enabled:
            return
        entry = {
            "status": status,
            "body": body,
            "fetched_at": fetched_at,
            "_cached_ts": time.time(),
        }
        tmp = self._path(key) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(entry, fh, sort_keys=True)
        os.replace(tmp, self._path(key))
