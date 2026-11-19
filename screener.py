"""Altcoin screener: filters BTC-denominated coins by volume and 24h change vs BTC."""
from dataclasses import dataclass
from typing import Any


@dataclass
class Coin:
    code: str
    name: str
    rate_btc: float
    volume_btc: float
    change_24h_pct: float


@dataclass
class ScreenResult:
    long: list[Coin]
    short: list[Coin]
    outliers: list[Coin]


def delta_to_pct(delta: float | None) -> float | None:
    """LiveCoinWatch delta is a multiplier (1.0437 = +4.37%)."""
    return None if delta is None else (delta - 1) * 100


def parse_coin(raw: dict[str, Any]) -> Coin | None:
    pct = delta_to_pct((raw.get("delta") or {}).get("day"))
    if pct is None or raw.get("volume") is None:
        return None
    return Coin(
        code=raw["code"],
        name=raw.get("name") or "",
        rate_btc=raw.get("rate") or 0.0,
        volume_btc=raw["volume"],
        change_24h_pct=pct,
    )


def is_excluded(raw: dict[str, Any], cfg: dict[str, Any]) -> bool:
    """True for BTC and non-alt assets (stablecoins, wrapped BTC, gold, tokenized stocks...)."""
    codes = {"BTC", *(c.upper() for c in cfg.get("exclude_codes") or [])}
    if raw.get("code", "").upper() in codes:
        return True
    if set(raw.get("categories") or []) & set(cfg.get("exclude_categories") or []):
        return True
    name = (raw.get("name") or "").lower()
    return any(k.lower() in name for k in cfg.get("exclude_name_keywords") or [])


def in_range(value: float, rng: dict[str, float]) -> bool:
    return rng["min_pct"] <= value <= rng["max_pct"]


def screen(raw_coins: list[dict[str, Any]], cfg: dict[str, Any]) -> ScreenResult:
    """Bucket coins into long / short / outliers.

    A coin inside both ranges (overlap zone) appears in both long and short.
    Outliers = passed the volume filter but fit neither range.
    """
    result = ScreenResult(long=[], short=[], outliers=[])

    for raw in raw_coins:
        if is_excluded(raw, cfg):
            continue
        coin = parse_coin(raw)
        if coin is None or coin.volume_btc < cfg["min_volume_btc"]:
            continue
        is_long = in_range(coin.change_24h_pct, cfg["long_range"])
        is_short = in_range(coin.change_24h_pct, cfg["short_range"])
        if is_long:
            result.long.append(coin)
        if is_short:
            result.short.append(coin)
        if not (is_long or is_short):
            result.outliers.append(coin)

    result.long.sort(key=lambda c: c.change_24h_pct, reverse=True)
    result.short.sort(key=lambda c: c.change_24h_pct)
    result.outliers.sort(key=lambda c: abs(c.change_24h_pct), reverse=True)
    return result
