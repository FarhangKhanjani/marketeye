"""Market regime classification — STUB (Phase 1).

The six regimes come from two inputs:
  * BTC trend:       bullish / bearish / range
  * BTC dominance:   bullish / bearish

The numeric rules for each classification are NOT defined yet. The functions
below raise NotImplementedError until those rules are supplied.
"""
from enum import Enum


class BtcTrend(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    RANGE = "range"


class DominanceTrend(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


class Action(str, Enum):
    LONG_BTC = "long BTC"
    LONG_ALTS = "long altcoins"
    BTC_OR_STRONG_ALTS = "BTC, or alts very strong vs BTC"
    SHORT_ALTS = "short altcoins"
    SHORT_BTC = "short BTC"


REGIME_ACTIONS: dict[tuple[BtcTrend, DominanceTrend], Action] = {
    (BtcTrend.BULLISH, DominanceTrend.BULLISH): Action.LONG_BTC,
    (BtcTrend.BULLISH, DominanceTrend.BEARISH): Action.LONG_ALTS,
    (BtcTrend.RANGE, DominanceTrend.BULLISH): Action.BTC_OR_STRONG_ALTS,
    (BtcTrend.RANGE, DominanceTrend.BEARISH): Action.LONG_ALTS,
    (BtcTrend.BEARISH, DominanceTrend.BULLISH): Action.SHORT_ALTS,
    (BtcTrend.BEARISH, DominanceTrend.BEARISH): Action.SHORT_BTC,
}


def classify_btc_trend(*args, **kwargs) -> BtcTrend:
    """TODO: classify BTC as bullish / bearish / range once rules are defined."""
    raise NotImplementedError("BTC trend rules not defined yet")


def classify_dominance_trend(history: list[tuple[int, float]]) -> DominanceTrend:
    """TODO: classify dominance trend from (timestamp_ms, pct) history once rules are defined."""
    raise NotImplementedError("Dominance trend rules not defined yet")


def action_for(btc: BtcTrend, dom: DominanceTrend) -> Action:
    """Look up the action for a regime. This part works today."""
    return REGIME_ACTIONS[(btc, dom)]
