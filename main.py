"""Phase 1 entry point: screen alts vs BTC and show BTC dominance."""
from datetime import datetime, timezone

from clients.livecoinwatch import LiveCoinWatchClient, LiveCoinWatchError
from config import OUTPUT_DIR, get_api_key, load_config
from dominance import DominanceData
from pipeline import fetch_snapshot, save_csv
from screener import Coin, screen


def print_table(title: str, coins: list[Coin]) -> None:
    print(f"\n=== {title} ({len(coins)}) ===")
    if not coins:
        print("  (none)")
        return
    w = max(len("CODE"), *(len(c.code) for c in coins)) + 2  # LCW codes can be long (e.g. "___TRUMP")
    print(f"  {'CODE':<{w}}{'NAME':<26}{'24h % vs BTC':>14}{'VOLUME (BTC)':>16}")
    for c in coins:
        print(f"  {c.code:<{w}}{c.name[:25]:<26}{c.change_24h_pct:>+13.2f}%{c.volume_btc:>16,.0f}")


def print_dominance(dom: DominanceData) -> None:
    print(f"\nBTC dominance: {dom.current_pct:.2f}%")
    if dom.history:
        first_ts, first_pct = dom.history[0]
        first_date = datetime.fromtimestamp(first_ts / 1000, timezone.utc).date()
        print(f"  history: {len(dom.history)} points since {first_date} (first: {first_pct:.2f}%)")


def main() -> None:
    cfg = load_config()
    scfg, api = cfg["screener"], cfg["api"]
    client = LiveCoinWatchClient(get_api_key(), timeout=api["timeout_seconds"])

    try:
        snap = fetch_snapshot(client, cfg)
    except LiveCoinWatchError as exc:
        raise SystemExit(f"API error: {exc}")

    raw, dom = snap.raw, snap.dominance
    result = screen(raw, scfg)
    print(f"Screened {len(raw)} coins (min volume {scfg['min_volume_btc']} BTC) - PLACEHOLDER ranges")
    print_table(f"LONG candidates {scfg['long_range']}", result.long)
    print_table(f"SHORT candidates {scfg['short_range']}", result.short)
    print_table("OUTLIERS (outside both ranges)", result.outliers)
    print_dominance(dom)
    print(f"\nSaved: {save_csv(result, dom, OUTPUT_DIR)}")
    print(f"API calls this run: {client.calls_made}")


if __name__ == "__main__":
    main()
