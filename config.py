"""Loads settings from config.yaml and secrets from .env."""
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.yaml"
OUTPUT_DIR = ROOT / "output"


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_api_key() -> str:
    load_dotenv(ROOT / ".env")
    key = os.getenv("LCW_API_KEY", "").strip()
    if not key or key == "your-key-here":
        raise SystemExit("LCW_API_KEY is missing. Copy .env.example to .env and set your key.")
    return key


def save_screener_settings(min_volume_btc: float, long_range: dict[str, float],
                           short_range: dict[str, float], path: Path = CONFIG_PATH) -> None:
    """Write the tunable screener numbers back to config.yaml, keeping its comments.

    Only these five numbers are touched; everything else in the file stays as written.
    """
    import re

    text = path.read_text(encoding="utf-8")
    num = r"-?\d+(?:\.\d+)?"
    subs = [
        (rf"(min_volume_btc:\s*){num}", rf"\g<1>{min_volume_btc:g}"),
        (rf"(long_range:\s*\n\s*min_pct:\s*){num}(\s*\n\s*max_pct:\s*){num}",
         rf"\g<1>{long_range['min_pct']:g}\g<2>{long_range['max_pct']:g}"),
        (rf"(short_range:[^\n]*\n\s*min_pct:\s*){num}(\s*\n\s*max_pct:\s*){num}",
         rf"\g<1>{short_range['min_pct']:g}\g<2>{short_range['max_pct']:g}"),
    ]
    for pattern, repl in subs:
        text, n = re.subn(pattern, repl, text, count=1)
        if n != 1:
            raise ValueError(f"config.yaml layout changed; could not update {pattern.split(':')[0]}")
    path.write_text(text, encoding="utf-8")

    saved = load_config(path)["screener"]
    if (saved["min_volume_btc"], saved["long_range"], saved["short_range"]) != (min_volume_btc, long_range, short_range):
        raise ValueError("config.yaml did not round-trip; check the file by hand")
