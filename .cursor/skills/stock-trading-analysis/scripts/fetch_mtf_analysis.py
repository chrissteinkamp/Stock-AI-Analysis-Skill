#!/usr/bin/env python3
"""Multi-timeframe technical analysis for stock-trading-analysis skill.

Fetches all standard timeframes, computes indicators, detects conflicts,
and outputs a synthesis for every analysis prompt.

Usage:
  python fetch_mtf_analysis.py SOFI
  python fetch_mtf_analysis.py BTC-USD --pretty
  python fetch_mtf_analysis.py IREN --bars 5
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import urllib.parse
from datetime import datetime, timezone
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_chart import (
    USER_AGENT,
    YAHOO_CHART,
    cross_status,
    ema,
    http_get,
    ma_stack,
    parse_yahoo_bars,
    pct_change,
    rsi,
    sma,
)

# (label, yahoo_interval, yahoo_range, min_bars_for_200sma)
TIMEFRAME_SPECS: list[tuple[str, str, str]] = [
    ("monthly", "1mo", "20y"),
    ("weekly", "1wk", "10y"),
    ("daily", "1d", "2y"),
    ("3mo", "1d", "3mo"),
    ("1h", "1h", "3mo"),
]


def aggregate_bars(bars: list[dict[str, Any]], factor: int) -> list[dict[str, Any]]:
    """Aggregate lower-TF bars (e.g. 1h -> 4h)."""
    out: list[dict[str, Any]] = []
    chunk: list[dict[str, Any]] = []
    for b in bars:
        chunk.append(b)
        if len(chunk) == factor:
            vols = [float(x["volume"] or 0) for x in chunk]
            out.append(
                {
                    "date": chunk[0]["date"],
                    "open": chunk[0]["open"],
                    "high": max(x["high"] for x in chunk if x["high"] is not None),
                    "low": min(x["low"] for x in chunk if x["low"] is not None),
                    "close": chunk[-1]["close"],
                    "volume": sum(vols) if any(vols) else None,
                }
            )
            chunk = []
    return out


def macd(closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict[str, float | None]:
    if len(closes) < slow + signal:
        return {"macd": None, "signal": None, "histogram": None, "status": "unknown"}
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    if ema_fast is None or ema_slow is None:
        return {"macd": None, "signal": None, "histogram": None, "status": "unknown"}

    # Build MACD line series for signal EMA
    k_f, k_s = 2 / (fast + 1), 2 / (slow + 1)
    ef = sum(closes[:fast]) / fast
    es = sum(closes[:slow]) / slow
    macd_series: list[float] = []
    for i, c in enumerate(closes):
        if i >= fast:
            ef = c * k_f + ef * (1 - k_f)
        if i >= slow:
            es = c * k_s + es * (1 - k_s)
        if i >= slow - 1:
            macd_series.append(ef - es)

    if len(macd_series) < signal:
        return {"macd": None, "signal": None, "histogram": None, "status": "unknown"}

    macd_line = macd_series[-1]
    sig = ema(macd_series, signal)
    if sig is None:
        return {"macd": round(macd_line, 4), "signal": None, "histogram": None, "status": "unknown"}
    hist = macd_line - sig
    if hist > 0 and macd_line > 0:
        status = "bullish"
    elif hist < 0 and macd_line < 0:
        status = "bearish"
    elif hist > 0 and macd_line < 0:
        status = "bullish_cross_forming"
    elif hist < 0 and macd_line > 0:
        status = "bearish_cross_forming"
    else:
        status = "neutral"
    return {
        "macd": round(macd_line, 4),
        "signal": round(sig, 4),
        "histogram": round(hist, 4),
        "status": status,
    }


def bollinger(closes: list[float], period: int = 20, mult: float = 2.0) -> dict[str, float | None]:
    if len(closes) < period:
        return {"upper": None, "middle": None, "lower": None, "position": "unknown", "width_pct": None}
    window = closes[-period:]
    mid = sum(window) / period
    variance = sum((x - mid) ** 2 for x in window) / period
    std = math.sqrt(variance)
    upper, lower = mid + mult * std, mid - mult * std
    price = closes[-1]
    if upper == lower:
        pos = "mid"
    elif price >= upper * 0.98:
        pos = "upper_band"
    elif price <= lower * 1.02:
        pos = "lower_band"
    elif price > mid:
        pos = "upper_half"
    else:
        pos = "lower_half"
    width = (upper - lower) / mid * 100 if mid else None
    return {
        "upper": round(upper, 4),
        "middle": round(mid, 4),
        "lower": round(lower, 4),
        "position": pos,
        "width_pct": round(width, 2) if width else None,
    }


def volume_analysis(bars: list[dict[str, Any]], lookback: int = 20) -> dict[str, Any]:
    vols = [float(b["volume"] or 0) for b in bars if b.get("volume")]
    if len(vols) < 5:
        return {"trend": "unknown", "vs_avg_pct": None, "price_volume_divergence": None}
    avg = sum(vols[-lookback:]) / min(lookback, len(vols[-lookback:]))
    latest = vols[-1]
    vs_avg = pct_change(latest, avg) if avg else None
    # Rally on declining volume: last 3 closes up, last 3 volumes down
    if len(bars) >= 4 and len(vols) >= 4:
        closes = [b["close"] for b in bars[-4:]]
        v4 = vols[-4:]
        rally = closes[-1] > closes[0]
        vol_declining = v4[-1] < v4[0] and v4[-2] < v4[1]
        pv_div = "bearish_rally_on_low_volume" if rally and vol_declining else None
        selloff = closes[-1] < closes[0]
        vol_rising = v4[-1] > v4[0]
        if selloff and vol_rising:
            pv_div = pv_div or "bearish_selloff_on_high_volume"
    else:
        pv_div = None
    recent_avg = sum(vols[-5:]) / 5
    prior_avg = sum(vols[-10:-5]) / 5 if len(vols) >= 10 else recent_avg
    if recent_avg > prior_avg * 1.1:
        trend = "increasing"
    elif recent_avg < prior_avg * 0.9:
        trend = "declining"
    else:
        trend = "stable"
    return {
        "trend": trend,
        "vs_avg_pct": round(vs_avg, 1) if vs_avg is not None else None,
        "price_volume_divergence": pv_div,
    }


def rsi_divergence(closes: list[float], period: int = 14, lookback: int = 20) -> str | None:
    if len(closes) < lookback + period + 1:
        return None
    segment = closes[-lookback:]
    mid = len(segment) // 2
    first_half, second_half = segment[:mid], segment[mid:]
    if not first_half or not second_half:
        return None

    def local_rsi(seg: list[float]) -> float | None:
        idx = len(closes) - lookback + closes[-lookback:].index(seg[-1])
        return rsi(closes[: idx + 1], period)

    # Simplified: higher price high but RSI not confirming
    r_now = rsi(closes, period)
    if r_now is None:
        return None
    price_hh = max(second_half) > max(first_half) * 1.01
    price_ll = min(second_half) < min(first_half) * 0.99
    r_prior = rsi(closes[:-5], period) if len(closes) > period + 6 else None
    if price_hh and r_prior and r_now < r_prior - 3:
        return "bearish_divergence"
    if price_ll and r_prior and r_now > r_prior + 3:
        return "bullish_divergence"
    return None


def detect_candlestick(bars: list[dict[str, Any]]) -> list[str]:
    if len(bars) < 2:
        return []
    patterns: list[str] = []
    c = bars[-1]
    p = bars[-2]
    o, h, l, cl = c["open"], c["high"], c["low"], c["close"]
    if None in (o, h, l, cl):
        return patterns
    body = abs(cl - o)
    rng = h - l if h > l else 0.001
    upper_wick = h - max(o, cl)
    lower_wick = min(o, cl) - l

    if body / rng < 0.1:
        patterns.append("doji")
    if lower_wick > body * 2 and upper_wick < body * 0.5:
        patterns.append("hammer_or_hanging_man")
    if upper_wick > body * 2 and lower_wick < body * 0.5:
        patterns.append("shooting_star_or_inverted_hammer")

    po, pc = p["open"], p["close"]
    if po is not None and pc is not None:
        if po > pc and cl > o and cl > po and o < pc:
            patterns.append("bullish_engulfing")
        if po < pc and cl < o and cl < po and o > pc:
            patterns.append("bearish_engulfing")
    return patterns


def wyckoff_hint(bars: list[dict[str, Any]], trend: str) -> str:
    vol = volume_analysis(bars)
    if len(bars) < 10:
        return "insufficient_data"
    closes = [b["close"] for b in bars]
    up_move = closes[-1] > closes[-10]
    if up_move and vol["trend"] == "declining":
        return "distribution_warning"
    if not up_move and vol["trend"] == "declining" and vol.get("price_volume_divergence") != "bearish_selloff_on_high_volume":
        return "accumulation_possible"
    if up_move and vol["trend"] == "increasing":
        return "markup_confirmed" if trend == "bullish" else "relief_rally"
    if not up_move and vol["trend"] == "increasing":
        return "markdown"
    return "range/consolidation"


def rsi_zone(r: float | None, tf: str) -> str:
    if r is None:
        return "unknown"
    if tf == "monthly" and r > 80:
        return "overbought_extreme" if r > 90 else "overbought"
    if tf in ("weekly", "monthly") and r > 70:
        return "overbought"
    if r > 70:
        return "overbought"
    if r < 30:
        return "oversold"
    if r < 40:
        return "weak"
    if r > 60:
        return "strong"
    return "neutral"


def tf_bias(ind: dict[str, Any], tf: str) -> dict[str, Any]:
    """Score single timeframe bullish/bearish/neutral."""
    score = 0
    reasons: list[str] = []

    stack = ind.get("ma_stack", "mixed")
    if stack == "bullish":
        score += 2
        reasons.append("bullish MA stack")
    elif stack == "bearish":
        score -= 2
        reasons.append("bearish MA stack")
    elif stack == "mixed_bearish":
        score -= 1
    elif stack == "mixed_bullish":
        score += 1

    cross = ind.get("cross_status", "")
    if "golden_cross" in cross and "forming" not in cross:
        score += 1
        reasons.append("golden cross")
    elif "death_cross" in cross and "forming" not in cross:
        score -= 1
        reasons.append("death cross")

    rz = ind.get("rsi_zone", "neutral")
    if rz in ("overbought", "overbought_extreme"):
        score -= 1
        reasons.append(f"RSI {rz}")
    elif rz == "oversold":
        score += 1
        reasons.append("RSI oversold")
    elif rz == "strong":
        score += 1

    ext = ind.get("extension_from_200sma_pct")
    if ext is not None and ext > 25:
        score -= 1
        reasons.append(f"extended +{ext}% from 200 SMA")
    elif ext is not None and ext < -10:
        score += 1
        reasons.append("below 200 SMA (potential value)")

    macd_s = ind.get("macd", {}).get("status", "")
    if macd_s == "bullish":
        score += 1
    elif macd_s == "bearish":
        score -= 1

    vol = ind.get("volume", {})
    if vol.get("price_volume_divergence") == "bearish_rally_on_low_volume":
        score -= 1
        reasons.append("rally on declining volume")

    div = ind.get("rsi_divergence")
    if div == "bearish_divergence":
        score -= 1
        reasons.append("bearish RSI divergence")
    elif div == "bullish_divergence":
        score += 1
        reasons.append("bullish RSI divergence")

    if score >= 2:
        label = "bullish"
    elif score <= -2:
        label = "bearish"
    else:
        label = "neutral"

    return {"bias": label, "score": score, "reasons": reasons}


def fetch_yahoo_raw(symbol: str, interval: str, range_: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    params = urllib.parse.urlencode({"interval": interval, "range": range_})
    url = f"{YAHOO_CHART.format(symbol=urllib.parse.quote(symbol.upper()))}?{params}"
    data = http_get(url)
    results = data.get("chart", {}).get("result")
    if not results:
        err = data.get("chart", {}).get("error", {}).get("description", "No chart data")
        raise RuntimeError(f"Yahoo Finance: {err}")
    return parse_yahoo_bars(results[0])


def analyze_timeframe(
    label: str,
    bars: list[dict[str, Any]],
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not bars:
        return {"timeframe": label, "error": "no bars"}
    closes = [b["close"] for b in bars]
    price = (meta or {}).get("regularMarketPrice") or closes[-1]
    s20, s50, s200 = sma(closes, 20), sma(closes, 50), sma(closes, 200)
    r = rsi(closes, 14)
    ext = pct_change(price, s200) if s200 else None

    ind: dict[str, Any] = {
        "timeframe": label,
        "price": round(price, 4),
        "bar_count": len(bars),
        "sma_20": round(s20, 4) if s20 else None,
        "sma_50": round(s50, 4) if s50 else None,
        "sma_200": round(s200, 4) if s200 else None,
        "ema_20": round(ema(closes, 20), 4) if ema(closes, 20) else None,
        "rsi_14": round(r, 2) if r else None,
        "rsi_zone": rsi_zone(r, label),
        "extension_from_200sma_pct": round(ext, 2) if ext is not None else None,
        "ma_stack": ma_stack(price, s50, s200),
        "cross_status": cross_status(s50, s200),
        "macd": macd(closes),
        "bollinger": bollinger(closes),
        "volume": volume_analysis(bars),
        "rsi_divergence": rsi_divergence(closes),
        "candlestick_patterns": detect_candlestick(bars),
        "wyckoff_hint": wyckoff_hint(bars, ma_stack(price, s50, s200)),
        "performance": {
            "change_1m_pct": round(pct_change(closes[-1], closes[-22]), 2) if len(closes) >= 22 else None,
            "change_3m_pct": round(pct_change(closes[-1], closes[-66]), 2) if len(closes) >= 66 else None,
        },
    }
    ind["bias"] = tf_bias(ind, label)
    return ind


def detect_conflicts(analyses: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    order = ["monthly", "weekly", "daily", "3mo", "4h", "2h", "1h"]
    by_label = {a["timeframe"]: a for a in analyses.values() if "error" not in a}

    def get(label: str) -> dict[str, Any] | None:
        return by_label.get(label)

    weekly, daily, h4, h1 = get("weekly"), get("daily"), get("4h"), get("1h")
    monthly = get("monthly")

    # LTF bullish entry vs HTF overbought
    ltf_bull = h4 and h4["bias"]["bias"] in ("bullish", "neutral") and h4.get("rsi_14", 0) < 70
    htf_ob = weekly and weekly.get("rsi_zone") in ("overbought", "overbought_extreme")
    htf_vol_decline = weekly and weekly.get("volume", {}).get("trend") == "declining"
    if ltf_bull and htf_ob:
        flags.append(
            {
                "severity": "high",
                "flag": "ltf_entry_vs_htf_overbought",
                "message": "Lower TF may show reasonable entry, but weekly/monthly is overbought — risky long.",
            }
        )
    if ltf_bull and htf_ob and htf_vol_decline:
        flags.append(
            {
                "severity": "high",
                "flag": "bullish_ltf_on_exhausted_htf",
                "message": "Intraday/daily bounce into weekly overbought with declining volume — classic bull trap risk.",
            }
        )

    # Daily golden cross vs weekly death cross
    if daily and weekly:
        d_golden = "golden_cross" in daily.get("cross_status", "") and "forming" not in daily.get("cross_status", "")
        w_death = "death_cross" in weekly.get("cross_status", "") and "forming" not in weekly.get("cross_status", "")
        if d_golden and w_death:
            flags.append(
                {
                    "severity": "medium",
                    "flag": "daily_weekly_cross_conflict",
                    "message": "Daily golden cross inside weekly death cross — likely pullback, not new bull market.",
                }
            )

    # Extended on HTF
    if monthly and (monthly.get("extension_from_200sma_pct") or 0) > 25:
        flags.append(
            {
                "severity": "medium",
                "flag": "monthly_extended",
                "message": f"Monthly extended {monthly['extension_from_200sma_pct']}% above 200 SMA — mean-reversion risk.",
            }
        )
    if weekly and (weekly.get("extension_from_200sma_pct") or 0) > 25:
        flags.append(
            {
                "severity": "medium",
                "flag": "weekly_extended",
                "message": "Weekly >25% above 200 SMA — reduce long size; favor fades at resistance.",
            }
        )

    # Rally on low volume (any HTF)
    for tf in ("weekly", "daily", "4h"):
        a = get(tf)
        if a and a.get("volume", {}).get("price_volume_divergence") == "bearish_rally_on_low_volume":
            flags.append(
                {
                    "severity": "medium",
                    "flag": f"weak_rally_{tf}",
                    "message": f"{tf.upper()}: price rising on declining volume — weak rally (Wyckoff effort vs result).",
                }
            )

    # Distribution warning on weekly
    if weekly and weekly.get("wyckoff_hint") == "distribution_warning":
        flags.append(
            {
                "severity": "high",
                "flag": "weekly_distribution",
                "message": "Weekly Wyckoff: distribution warning — institutions may be selling into strength.",
            }
        )

    # 1h oversold vs daily bearish — knife catch
    if h1 and daily:
        if h1.get("rsi_zone") == "oversold" and daily["bias"]["bias"] == "bearish":
            flags.append(
                {
                    "severity": "medium",
                    "flag": "oversold_ltf_in_bearish_htf",
                    "message": "1H oversold in daily bearish trend — bounce possible but catching a falling knife.",
                }
            )

    return flags


def synthesize_mtf(analyses: dict[str, dict[str, Any]], conflicts: list[dict[str, str]]) -> dict[str, Any]:
    weights = {"monthly": 3, "weekly": 4, "daily": 3, "3mo": 2, "4h": 1, "2h": 1, "1h": 1}
    total_w, weighted = 0, 0
    bias_counts = {"bullish": 0, "bearish": 0, "neutral": 0}

    for label, a in analyses.items():
        if "error" in a:
            continue
        w = weights.get(label, 1)
        b = a["bias"]["bias"]
        bias_counts[b] += 1
        score = a["bias"]["score"]
        weighted += score * w
        total_w += w

    avg = weighted / total_w if total_w else 0
    high_conflicts = sum(1 for c in conflicts if c["severity"] == "high")

    if avg >= 1.5 and high_conflicts == 0:
        verdict = "bullish_aligned"
        trade_bias = "long"
    elif avg >= 1.5 and high_conflicts > 0:
        verdict = "bullish_but_conflicted"
        trade_bias = "wait_or_reduce_size"
    elif avg <= -1.5 and high_conflicts == 0:
        verdict = "bearish_aligned"
        trade_bias = "short_or_avoid"
    elif avg <= -1.5:
        verdict = "bearish_but_conflicted"
        trade_bias = "wait"
    else:
        verdict = "mixed_neutral"
        trade_bias = "wait"

    htf = [analyses.get(k) for k in ("monthly", "weekly") if k in analyses and "error" not in analyses[k]]
    ltf = [analyses.get(k) for k in ("4h", "2h", "1h", "daily") if k in analyses and "error" not in analyses.get(k, {})]

    htf_bias = htf[1]["bias"]["bias"] if len(htf) > 1 else (htf[0]["bias"]["bias"] if htf else "unknown")
    ltf_biases = [x["bias"]["bias"] for x in ltf if x]

    return {
        "weighted_score": round(avg, 2),
        "bias_counts": bias_counts,
        "verdict": verdict,
        "trade_bias": trade_bias,
        "htf_bias": htf_bias,
        "ltf_biases": ltf_biases,
        "alignment": "aligned" if len(set(ltf_biases + [htf_bias])) <= 2 and htf_bias in ltf_biases else "conflicted",
        "conflict_count": len(conflicts),
        "high_severity_conflicts": high_conflicts,
        "rule": "Higher timeframe leads. Weekly overrides daily. Daily overrides 4H/1H. Never trade LTF signal alone against HTF exhaustion.",
    }


def run_mtf_analysis(symbol: str, bars_keep: int = 8) -> dict[str, Any]:
    analyses: dict[str, dict[str, Any]] = {}
    meta_global: dict[str, Any] = {}
    hourly_bars: list[dict[str, Any]] = []

    for label, interval, range_ in TIMEFRAME_SPECS:
        try:
            bars, meta = fetch_yahoo_raw(symbol, interval, range_)
            if label == "1h":
                hourly_bars = bars
            if not meta_global:
                meta_global = meta
            result = analyze_timeframe(label, bars, meta)
            if bars_keep and "bars" not in result:
                result["recent_bars"] = bars[-bars_keep:]
            analyses[label] = result
        except Exception as exc:
            analyses[label] = {"timeframe": label, "error": str(exc)}

    # Derive 2h and 4h from 1h
    if hourly_bars:
        for label, factor in (("4h", 4), ("2h", 2)):
            agg = aggregate_bars(hourly_bars, factor)
            if agg:
                analyses[label] = analyze_timeframe(label, agg, meta_global)
                if bars_keep:
                    analyses[label]["recent_bars"] = agg[-bars_keep:]

    conflicts = detect_conflicts(analyses)
    synthesis = synthesize_mtf(analyses, conflicts)

    price = meta_global.get("regularMarketPrice")
    return {
        "symbol": meta_global.get("symbol", symbol.upper()),
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "quote": {
            "price": price,
            "fifty_two_week_high": meta_global.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": meta_global.get("fiftyTwoWeekLow"),
        },
        "timeframes": analyses,
        "conflicts": conflicts,
        "synthesis": synthesis,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-timeframe technical analysis")
    parser.add_argument("symbol", help="Ticker symbol (e.g. SOFI, BTC-USD)")
    parser.add_argument("--bars", type=int, default=8, help="Recent bars per TF in output")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    try:
        payload = run_mtf_analysis(args.symbol, args.bars)
        print(json.dumps(payload, indent=2 if args.pretty else None))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc), "symbol": args.symbol.upper()}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
