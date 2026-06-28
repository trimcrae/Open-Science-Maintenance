"""Usage signal: recent monthly downloads from pypistats.org (no auth required)."""

from __future__ import annotations

from .. import config
from ..http import HttpClient, HttpError

BASE = "https://pypistats.org/api/packages"


def normalize_name(pkg: str) -> str:
    return pkg.strip().lower().replace("_", "-")


def fetch_monthly_downloads(
    http: HttpClient, pypi_name: str | None
) -> tuple[int | None, list[str]]:
    """Return (last_month_downloads, errors). Missing package -> (None, [...])."""
    if not pypi_name:
        return None, ["no pypi package configured"]
    pkg = normalize_name(pypi_name)
    url = f"{BASE}/{pkg}/recent"
    try:
        body = http.get_json(url, source="pypistats", ttl=config.CACHE_TTL["pypistats"])
    except HttpError as e:
        if e.status in (404, 410):
            return None, [f"pypistats: package {pkg!r} not found"]
        return None, [f"pypistats: {e}"]
    data = body.get("data", {}) if isinstance(body, dict) else {}
    val = data.get("last_month")
    return (int(val) if val is not None else None), []
