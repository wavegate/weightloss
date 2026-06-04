"""Shared HTTP fetch helpers for public event listing pages."""

from __future__ import annotations

import ssl
import urllib.error
import urllib.request

import certifi

USER_AGENT = "WeightlossEventBot/1.0 (+https://github.com/weightloss)"


def https_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def http_get(url: str, *, extra_headers: dict[str, str] | None = None) -> str:
    headers = {"User-Agent": USER_AGENT, **(extra_headers or {})}
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(
            request,
            timeout=30,
            context=https_context(),
        ) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(
            f"HTTP {exc.code} fetching {url}: {detail}",
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc.reason}") from exc
