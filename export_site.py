"""Build the static GitHub Pages site into _site/ (used by .github/workflows/site.yml).

Output: every file in web/ (the same pages as the local app) and _site/data.json
(latest fetch + default settings from config.yaml). Costs ~3 API credits.
"""
import json
import re
import shutil

import requests

from clients.livecoinwatch import LiveCoinWatchClient
from config import ROOT, get_api_key, load_config
from pipeline import fetch_snapshot, snapshot_to_dict

SITE_DIR = ROOT / "_site"


def ping_supabase() -> None:
    """Keep the free Supabase project awake (it pauses after ~7 idle days).

    One tiny query per run. Never fails the build: the site works without it.
    """
    cfg = (ROOT / "web" / "supabase-config.js").read_text(encoding="utf-8")
    url = re.search(r'SUPABASE_URL = "([^"]*)"', cfg).group(1)
    key = re.search(r'SUPABASE_ANON_KEY = "([^"]*)"', cfg).group(1)
    if not (url and key):
        return
    try:
        r = requests.get(f"{url}/rest/v1/searches?select=id&limit=1",
                         headers={"apikey": key, "Authorization": f"Bearer {key}"}, timeout=15)
        print(f"Supabase keep-alive: HTTP {r.status_code}")
    except requests.RequestException as exc:
        print(f"Supabase keep-alive failed (ignored): {exc}")


def main() -> None:
    cfg = load_config()
    scfg = cfg["screener"]
    client = LiveCoinWatchClient(get_api_key(), timeout=cfg["api"]["timeout_seconds"])
    snap = fetch_snapshot(client, cfg)

    SITE_DIR.mkdir(exist_ok=True)
    for f in (ROOT / "web").iterdir():   # pages, styles, scripts
        if f.is_file():
            shutil.copy(f, SITE_DIR / f.name)
    payload = {
        "settings": {k: scfg[k] for k in ("min_volume_btc", "long_range", "short_range")},
        "data": snapshot_to_dict(snap, scfg),
    }
    (SITE_DIR / "data.json").write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    ping_supabase()
    print(f"Wrote {SITE_DIR} with {len(payload['data']['coins'])} coins, {client.calls_made} API calls")


if __name__ == "__main__":
    main()
