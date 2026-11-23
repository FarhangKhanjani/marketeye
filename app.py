"""Local web UI for the Marketeye screener.

Run:  python app.py   then open http://127.0.0.1:8000
Binds to localhost only. Each "Refresh data" costs ~3 LiveCoinWatch credits;
changing ranges re-screens the last fetch for free.
"""
import threading
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

from clients.livecoinwatch import LiveCoinWatchClient, LiveCoinWatchError
from config import OUTPUT_DIR, ROOT, get_api_key, load_config, save_screener_settings
from pipeline import Snapshot, fetch_snapshot, save_csv, snapshot_to_dict
from screener import screen

app = Flask(__name__, static_folder=None)
_lock = threading.Lock()
_snapshot: Snapshot | None = None
_client: LiveCoinWatchClient | None = None


def client() -> LiveCoinWatchClient:
    global _client
    if _client is None:
        _client = LiveCoinWatchClient(get_api_key(), timeout=load_config()["api"]["timeout_seconds"])
    return _client


def settings_view(scfg: dict[str, Any]) -> dict[str, Any]:
    return {k: scfg[k] for k in ("min_volume_btc", "long_range", "short_range")}


def state() -> dict[str, Any]:
    scfg = load_config()["screener"]
    data = snapshot_to_dict(_snapshot, scfg) if _snapshot else None
    return {"settings": settings_view(scfg), "data": data}


def parse_settings(body: dict[str, Any]) -> dict[str, Any]:
    """Validate settings from the page. Raises ValueError with a readable message."""
    try:
        vol = float(body["min_volume_btc"])
        rngs = {k: {"min_pct": float(body[k]["min_pct"]), "max_pct": float(body[k]["max_pct"])}
                for k in ("long_range", "short_range")}
    except (KeyError, TypeError, ValueError):
        raise ValueError("Every field needs a number.")
    if vol <= 0:
        raise ValueError("Minimum volume must be above 0 BTC.")
    for name, r in rngs.items():
        if r["min_pct"] >= r["max_pct"]:
            raise ValueError(f"{name.split('_')[0].title()} range: the minimum must be below the maximum.")
    return {"min_volume_btc": vol, **rngs}


@app.get("/")
def index():
    return send_from_directory(ROOT / "web", "index.html")


@app.get("/<path:name>")
def web_file(name: str):
    """Other pages and assets (login.html, history.html, style.css, *.js)."""
    return send_from_directory(ROOT / "web", name)


@app.get("/api/state")
def get_state():
    return jsonify(state())


@app.post("/api/refresh")
def refresh():
    global _snapshot
    with _lock:
        cfg = load_config()
        try:
            _snapshot = fetch_snapshot(client(), cfg)
        except LiveCoinWatchError as exc:
            return jsonify({"error": f"LiveCoinWatch request failed: {exc}"}), 502
        csv_path = save_csv(screen(_snapshot.raw, cfg["screener"]), _snapshot.dominance, OUTPUT_DIR)
    return jsonify({**state(), "csv": csv_path.name})


@app.post("/api/settings")
def update_settings():
    try:
        s = parse_settings(request.get_json(force=True) or {})
        with _lock:
            save_screener_settings(s["min_volume_btc"], s["long_range"], s["short_range"])
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(state())


if __name__ == "__main__":
    get_api_key()  # fail fast if .env is missing
    app.run(host="127.0.0.1", port=8000, debug=False)
