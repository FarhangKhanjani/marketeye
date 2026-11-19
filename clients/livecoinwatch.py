"""Minimal LiveCoinWatch API client.

Docs: https://livecoinwatch.github.io/lcw-api-docs/
Every endpoint is POST + JSON with an `x-api-key` header.
Each request costs 1 credit from a daily allowance (resets at UTC midnight).
"""
from typing import Any

import time

import requests

BASE_URL = "https://api.livecoinwatch.com"
MAX_PAGE_SIZE = 100


class LiveCoinWatchError(RuntimeError):
    """Raised for network failures and API error responses."""


class LiveCoinWatchClient:
    def __init__(self, api_key: str, timeout: float = 15.0, retries: int = 1) -> None:
        self.timeout = timeout
        self.retries = retries
        self.calls_made = 0
        self.session = requests.Session()
        self.session.headers.update({"content-type": "application/json", "x-api-key": api_key})

    def _post(self, path: str, body: dict[str, Any] | None = None) -> Any:
        """POST with a short retry on network errors, 429 and 5xx (each retry may cost a credit)."""
        for attempt in range(self.retries + 1):
            try:
                resp = self._post_once(path, body)
            except LiveCoinWatchError:
                if attempt == self.retries:
                    raise
            else:
                retryable = resp.status_code == 429 or resp.status_code >= 500
                if not retryable or attempt == self.retries:
                    return self._parse(path, resp)
            time.sleep(2 * (attempt + 1))
        raise AssertionError("unreachable")

    def _post_once(self, path: str, body: dict[str, Any] | None) -> requests.Response:
        try:
            resp = self.session.post(f"{BASE_URL}{path}", json=body or {}, timeout=self.timeout)
        except requests.RequestException as exc:
            raise LiveCoinWatchError(f"{path}: request failed: {exc}") from exc
        self.calls_made += 1
        return resp

    def _parse(self, path: str, resp: requests.Response) -> Any:
        try:
            data = resp.json()
        except ValueError:
            raise LiveCoinWatchError(f"{path}: HTTP {resp.status_code}, non-JSON body: {resp.text[:200]}")

        if not resp.ok or (isinstance(data, dict) and "error" in data):
            err = data.get("error", {}) if isinstance(data, dict) else {}
            desc = err.get("description") or resp.reason
            raise LiveCoinWatchError(f"{path}: HTTP {resp.status_code} {desc}")
        return data

    def credits(self) -> dict[str, int]:
        """Remaining/total daily credits. Costs 1 credit."""
        return self._post("/credits")

    def coins_list(
        self,
        currency: str = "USD",
        sort: str = "volume",
        order: str = "descending",
        offset: int = 0,
        limit: int = MAX_PAGE_SIZE,
        meta: bool = True,
    ) -> list[dict[str, Any]]:
        """One page of coins (max 100)."""
        body = {
            "currency": currency,
            "sort": sort,
            "order": order,
            "offset": offset,
            "limit": min(limit, MAX_PAGE_SIZE),
            "meta": meta,
        }
        return self._post("/coins/list", body)

    def coins_by_volume(
        self, currency: str, min_volume: float, page_size: int = MAX_PAGE_SIZE, max_pages: int = 10
    ) -> list[dict[str, Any]]:
        """Coins sorted by volume (desc), paging only until volume drops below min_volume."""
        coins: list[dict[str, Any]] = []
        for page in range(max_pages):
            batch = self.coins_list(currency=currency, offset=page * page_size, limit=page_size)
            coins.extend(batch)
            last_volume = (batch[-1].get("volume") or 0) if batch else 0
            if len(batch) < page_size or last_volume < min_volume:
                break
        return coins

    def overview(self, currency: str = "USD") -> dict[str, Any]:
        """Market totals incl. btcDominance (a 0..1 ratio)."""
        return self._post("/overview", {"currency": currency})

    def overview_history(self, start_ms: int, end_ms: int, currency: str = "USD") -> list[dict[str, Any]]:
        """Historical market totals between two UNIX-ms timestamps."""
        return self._post("/overview/history", {"currency": currency, "start": start_ms, "end": end_ms})
