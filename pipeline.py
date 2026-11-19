"""One screening run, shared by the CLI (main.py) and the web app (app.py)."""
import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clients.livecoinwatch import LiveCoinWatchClient
from dominance import DominanceData, fetch_dominance
from screener import ScreenResult, is_excluded, parse_coin


@dataclass
class Snapshot:
    """Raw API data from one fetch. Re-screening it costs no credits."""
    raw: list[dict[str, Any]]
    dominance: DominanceData
    min_volume_fetched: float          # volume floor used when paging; lower floors need a refetch
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    api_calls: int = 0


def fetch_snapshot(client: LiveCoinWatchClient, cfg: dict[str, Any]) -> Snapshot:
    scfg, api = cfg["screener"], cfg["api"]
    before = client.calls_made
    raw = client.coins_by_volume(scfg["quote_currency"], scfg["min_volume_btc"], api["page_size"], api["max_pages"])
    dom = fetch_dominance(client, cfg["dominance"]["history_days"])
    return Snapshot(raw=raw, dominance=dom, min_volume_fetched=scfg["min_volume_btc"],
                    api_calls=client.calls_made - before)


def excluded_codes(snap: Snapshot, scfg: dict[str, Any]) -> list[str]:
    """Non-alt coins above the volume floor that the exclusion rules removed."""
    return [c["code"] for c in snap.raw
            if c.get("code") != "BTC" and (c.get("volume") or 0) >= scfg["min_volume_btc"] and is_excluded(c, scfg)]


def save_csv(result: ScreenResult, dom: DominanceData, out_dir: Path) -> Path:
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"screen_{stamp}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bucket", "code", "name", "change_24h_pct_vs_btc", "volume_btc", "rate_btc", "btc_dominance_pct"])
        for bucket, coins in (("long", result.long), ("short", result.short), ("outlier", result.outliers)):
            for c in coins:
                w.writerow([bucket, c.code, c.name, round(c.change_24h_pct, 4), round(c.volume_btc, 4),
                            c.rate_btc, round(dom.current_pct, 4)])
    return path


def snapshot_to_dict(snap: Snapshot, scfg: dict[str, Any]) -> dict[str, Any]:
    """Shape a snapshot for the web page.

    The page does the long/short/outlier bucketing itself, so it gets every
    tradable alt from the fetch (exclusions already applied) and can re-screen
    instantly when the ranges change.
    """
    coins = []
    for raw in snap.raw:
        if is_excluded(raw, scfg):
            continue
        c = parse_coin(raw)
        if c is not None:
            coins.append({"code": c.code, "name": c.name, "pct": round(c.change_24h_pct, 3),
                          "vol": c.volume_btc, "rate": c.rate_btc})
    return {
        "fetched_at": snap.fetched_at.isoformat(timespec="seconds"),
        "api_calls": snap.api_calls,
        "fetched": len(snap.raw),
        "min_volume_fetched": snap.min_volume_fetched,
        "excluded": excluded_codes(snap, scfg),
        "coins": coins,
        "dominance": round(snap.dominance.current_pct, 3),
        "dominance_history": [[t, round(p, 3)] for t, p in snap.dominance.history],
    }
