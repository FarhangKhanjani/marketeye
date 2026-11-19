"""BTC dominance data (current + history). Trend logic comes in a later phase."""
import time
from dataclasses import dataclass

from clients.livecoinwatch import LiveCoinWatchClient

DAY_MS = 24 * 60 * 60 * 1000


@dataclass
class DominanceData:
    current_pct: float
    history: list[tuple[int, float]]  # (timestamp_ms, dominance_pct)


def fetch_dominance(client: LiveCoinWatchClient, history_days: int = 30) -> DominanceData:
    """Two API calls: /overview and /overview/history."""
    current = client.overview()["btcDominance"] * 100
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - history_days * DAY_MS
    rows = client.overview_history(start_ms, end_ms)
    history = [(r["date"], r["btcDominance"] * 100) for r in rows if r.get("btcDominance") is not None]
    return DominanceData(current_pct=current, history=history)
