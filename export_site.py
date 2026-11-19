"""Build the static GitHub Pages site into _site/ (used by .github/workflows/site.yml).

Output: _site/index.html (the same page as the local app) and _site/data.json
(latest fetch + default settings from config.yaml). Costs ~3 API credits.
"""
import json
import shutil

from clients.livecoinwatch import LiveCoinWatchClient
from config import ROOT, get_api_key, load_config
from pipeline import fetch_snapshot, snapshot_to_dict

SITE_DIR = ROOT / "_site"


def main() -> None:
    cfg = load_config()
    scfg = cfg["screener"]
    client = LiveCoinWatchClient(get_api_key(), timeout=cfg["api"]["timeout_seconds"])
    snap = fetch_snapshot(client, cfg)

    SITE_DIR.mkdir(exist_ok=True)
    shutil.copy(ROOT / "web" / "index.html", SITE_DIR / "index.html")
    payload = {
        "settings": {k: scfg[k] for k in ("min_volume_btc", "long_range", "short_range")},
        "data": snapshot_to_dict(snap, scfg),
    }
    (SITE_DIR / "data.json").write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {SITE_DIR} with {len(payload['data']['coins'])} coins, {client.calls_made} API calls")


if __name__ == "__main__":
    main()
