#!/usr/bin/env python3
"""Scan NASDAQ for fresh golden crosses with bullish confluence."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from fetch_chart import USER_AGENT, COINGECKO_IDS, fetch_yahoo, pct_change, rsi, sma
from fetch_mtf_analysis import run_mtf_analysis

PHASE1_TREND_LABEL = "Trend Candidate"
PHASE1_SCENARIO_EMERGING = "emerging_pre_gc"
PHASE1_SCENARIO_GOLDEN_CROSS = "golden_cross_zone"
EMERGING_SMA_RISING_BARS = 10
EMERGING_SMA_GAP_MIN_PCT = 2.0
EMERGING_SMA_GAP_MAX_PCT = 5.0
GC_SPREAD_MIN_PCT = 0.0
GC_SPREAD_MAX_PCT = 8.0

# Legacy aliases (unified Phase 1)
ESTABLISHED_TREND_LABEL = PHASE1_TREND_LABEL
EMERGING_TREND_LABEL = PHASE1_TREND_LABEL

PHASE1_CRITERIA = {
    "trend_label": PHASE1_TREND_LABEL,
    "price": "above both 50 and 200 SMA",
    "sma200": "flat or rising over 10 bars (exclude declining 200 SMA)",
    "scenario_emerging_pre_gc": {
        "sma50_below_sma200_gap_pct": "2%–5%",
        "sma50_rising_bars": EMERGING_SMA_RISING_BARS,
    },
    "scenario_golden_cross_zone": {
        "sma50_above_sma200_pct": "0%–8%",
        "covers": "emerging golden cross through confirmed golden cross",
    },
    "timeframes": "daily and/or weekly (pass if either qualifies)",
    "asset_types": "stocks and crypto (Yahoo {COIN}-USD)",
}


def sort_phase1_hits(hits: list[dict[str, Any]]) -> None:
    """Unified Phase 1 rank: both TFs, golden-cross zone, emerging, tighter SMA spread."""
    hits.sort(
        key=lambda x: (
            (x.get("phase1_daily") and x.get("phase1_weekly")),
            x.get("golden_cross_weekly", False),
            x.get("golden_cross_daily", False),
            x.get("emerging_weekly", False),
            x.get("emerging_daily", False),
            -(x.get("weekly_sma50_above_200_pct") or x.get("weekly_sma50_200_gap_pct") or 99),
            -(x.get("daily_sma50_above_200_pct") or x.get("daily_sma50_200_gap_pct") or 99),
        ),
        reverse=True,
    )


# Backward-compatible alias
sort_established_phase1_hits = sort_phase1_hits

def fetch_nasdaq_symbols() -> list[str]:
    sources = [
        "https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed.csv",
        "https://ftp.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
    ]
    last_err: Exception | None = None
    for url in sources:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=45) as resp:
                text = resp.read().decode()
            if url.endswith(".csv"):
                return _parse_nasdaq_csv(text)
            return _parse_nasdaq_txt(text)
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"Could not fetch NASDAQ symbol list: {last_err}")


def _parse_nasdaq_csv(text: str) -> list[str]:
    symbols: list[str] = []
    for line in text.splitlines()[1:]:
        parts = line.split(",")
        if not parts:
            continue
        sym = parts[0].strip().strip('"')
        if not sym:
            continue
        if len(sym) > 5 or "$" in sym or "." in sym:
            continue
        symbols.append(sym)
    return symbols


def _parse_nasdaq_txt(text: str) -> list[str]:
    symbols: list[str] = []
    for line in text.splitlines()[1:]:
        if line.startswith("File"):
            break
        parts = line.split("|")
        if len(parts) < 7:
            continue
        sym, etf, test = parts[0], parts[5], parts[3]
        if etf != "N" or test != "N":
            continue
        if len(sym) > 5 or "$" in sym or "." in sym:
            continue
        symbols.append(sym)
    return symbols


def sma_at(closes: list[float], period: int, end: int) -> float | None:
    """SMA of `closes` using bars up to index `end` (exclusive)."""
    if end < period:
        return None
    return sma(closes[:end], period)


def sma50_rising_days(closes: list[float], days: int = EMERGING_SMA_RISING_BARS) -> bool:
    """True if SMA50 rose each step over the last `days` bars."""
    if len(closes) < 200 + days:
        return False
    vals: list[float] = []
    base = len(closes) - days
    for end in range(base, len(closes) + 1):
        v = sma_at(closes, 50, end)
        if v is None:
            return False
        vals.append(v)
    for i in range(1, len(vals)):
        if vals[i] < vals[i - 1] * 0.9995:
            return False
    return vals[-1] > vals[0]


def sma200_flat_or_rising(closes: list[float], days: int = EMERGING_SMA_RISING_BARS) -> bool:
    """Exclude symbols whose 200 SMA is still trending down."""
    if len(closes) < 200 + days:
        return False
    start = sma_at(closes, 200, len(closes) - days)
    end = sma_at(closes, 200, len(closes))
    if start is None or end is None:
        return False
    return end >= start * 0.998


def check_phase1_on_closes(
    closes: list[float],
    price: float,
    *,
    rising_bars: int = EMERGING_SMA_RISING_BARS,
) -> dict[str, Any] | None:
    """
    Unified Phase 1 per timeframe — pass if either:
      A) Emerging pre-GC: 50 SMA 2%–5% below 200, 50 rising, 200 flat/rising, price above both
      B) Golden-cross zone: 50 SMA 0%–8% above 200, 200 flat/rising, price above both
    """
    if len(closes) < 200 + rising_bars or price <= 0:
        return None

    s50 = sma(closes, 50)
    s200 = sma(closes, 200)
    if not s50 or not s200:
        return None
    if price <= s50 or price <= s200:
        return None
    if not sma200_flat_or_rising(closes, rising_bars):
        return None

    if s50 < s200:
        gap_pct = round((1 - s50 / s200) * 100, 2)
        if gap_pct < EMERGING_SMA_GAP_MIN_PCT or gap_pct > EMERGING_SMA_GAP_MAX_PCT:
            return None
        if not sma50_rising_days(closes, rising_bars):
            return None
        return {
            "scenario": PHASE1_SCENARIO_EMERGING,
            "sma50_200_gap_pct": gap_pct,
            "sma50_above_200_pct": None,
            "sma_50": round(s50, 4),
            "sma_200": round(s200, 4),
        }

    spread_pct = round((s50 / s200 - 1) * 100, 2)
    if spread_pct < GC_SPREAD_MIN_PCT or spread_pct > GC_SPREAD_MAX_PCT:
        return None

    return {
        "scenario": PHASE1_SCENARIO_GOLDEN_CROSS,
        "sma50_200_gap_pct": None,
        "sma50_above_200_pct": spread_pct,
        "sma_50": round(s50, 4),
        "sma_200": round(s200, 4),
    }


def phase1_rank(hit: dict[str, Any]) -> float:
    """Prefer both TFs; golden-cross zone; emerging gap near 3.5% below or ~4% above."""
    score = 0.0
    if hit.get("phase1_daily") and hit.get("phase1_weekly"):
        score += 30
    if hit.get("golden_cross_weekly"):
        score += 15
    if hit.get("golden_cross_daily"):
        score += 12
    if hit.get("emerging_weekly"):
        score += 10
    if hit.get("emerging_daily"):
        score += 8
    for key, ideal in (
        ("daily_sma50_200_gap_pct", 3.5),
        ("weekly_sma50_200_gap_pct", 3.5),
        ("daily_sma50_above_200_pct", 4.0),
        ("weekly_sma50_above_200_pct", 4.0),
    ):
        val = hit.get(key)
        if val is not None:
            score += max(0, 6 - abs(val - ideal)) * 3
    return score


# Backward-compatible alias
emerging_trend_rank = phase1_rank


def yahoo_symbol_for(symbol: str, asset_type: str = "stock") -> str:
    sym = symbol.upper().strip()
    if asset_type == "crypto":
        if sym.endswith("-USD"):
            return sym
        return f"{sym}-USD"
    return symbol


def fetch_crypto_symbols() -> list[str]:
    return [f"{coin}-USD" for coin in COINGECKO_IDS]


def _apply_tf_hit(out: dict[str, Any], tf: str, hit: dict[str, Any]) -> None:
    out[f"phase1_{tf}"] = True
    if hit["scenario"] == PHASE1_SCENARIO_EMERGING:
        out[f"emerging_{tf}"] = True
        out[f"{tf}_sma50_200_gap_pct"] = hit["sma50_200_gap_pct"]
    else:
        out[f"golden_cross_{tf}"] = True
        out[f"{tf}_sma50_above_200_pct"] = hit["sma50_above_200_pct"]


def phase1_screen(
    symbol: str,
    *,
    asset_type: str = "stock",
    yahoo_symbol: str | None = None,
) -> dict[str, Any] | None:
    """Unified Phase 1: emerging pre-GC and/or golden-cross zone on daily and/or weekly."""
    ysym = yahoo_symbol or yahoo_symbol_for(symbol, asset_type)
    try:
        dy = fetch_yahoo(ysym, "1d", "2y")
        wk = fetch_yahoo(ysym, "1wk", "5y")
    except Exception:
        return None

    d_closes = [b["close"] for b in dy["bars"]]
    w_closes = [b["close"] for b in wk["bars"]]
    w_t, d_t = wk["technicals"], dy["technicals"]
    price = dy["quote"]["price"]
    w_price = wk["quote"].get("price") or (w_closes[-1] if w_closes else price)
    hi52 = dy["quote"].get("fifty_two_week_high")
    lo52 = dy["quote"].get("fifty_two_week_low")

    daily_hit = check_phase1_on_closes(d_closes, price)
    weekly_hit = check_phase1_on_closes(w_closes, w_price)
    if not daily_hit and not weekly_hit:
        return None

    pct_from_ath = pct_change(price, hi52) if hi52 else None
    upside_to_high = round((hi52 / price - 1) * 100, 1) if hi52 and price > 0 else None

    out: dict[str, Any] = {
        "symbol": ysym if asset_type == "crypto" else symbol,
        "yahoo_symbol": ysym,
        "asset_type": asset_type,
        "price": price,
        "phase1_trend_label": PHASE1_TREND_LABEL,
        "phase1_daily": False,
        "phase1_weekly": False,
        "emerging_daily": False,
        "emerging_weekly": False,
        "golden_cross_daily": False,
        "golden_cross_weekly": False,
        "weekly_cross": w_t.get("cross_status"),
        "daily_cross": d_t.get("cross_status"),
        "weekly_ma_stack": w_t.get("ma_stack"),
        "weekly_ext_pct": w_t.get("extension_from_200sma_pct"),
        "weekly_rsi": w_t.get("rsi_14"),
        "daily_rsi": d_t.get("rsi_14"),
        "weekly_chg_3m": wk["performance"].get("change_3m_pct"),
        "daily_chg_3m": dy["performance"].get("change_3m_pct"),
        "pct_below_52wk_high": round(pct_from_ath, 1) if pct_from_ath is not None else None,
        "pct_above_52wk_low": round(pct_change(price, lo52), 1) if lo52 else None,
        "upside_to_52wk_high_pct": upside_to_high,
        # Legacy fields for Phase 2 scoring
        "weekly_gc_fresh": False,
        "daily_gc_fresh": False,
        "weekly_gc_age_bars": None,
        "daily_gc_age_bars": None,
    }

    if daily_hit:
        _apply_tf_hit(out, "daily", daily_hit)
        if daily_hit["scenario"] == PHASE1_SCENARIO_GOLDEN_CROSS:
            out["daily_gc_fresh"] = True
    if weekly_hit:
        _apply_tf_hit(out, "weekly", weekly_hit)
        if weekly_hit["scenario"] == PHASE1_SCENARIO_GOLDEN_CROSS:
            out["weekly_gc_fresh"] = True

    scenarios: list[str] = []
    if out["emerging_daily"]:
        scenarios.append("emerging_daily")
    if out["emerging_weekly"]:
        scenarios.append("emerging_weekly")
    if out["golden_cross_daily"]:
        scenarios.append("golden_cross_daily")
    if out["golden_cross_weekly"]:
        scenarios.append("golden_cross_weekly")
    out["phase1_scenarios"] = scenarios
    return out


def quick_screen(symbol: str) -> dict[str, Any] | None:
    """Alias for unified Phase 1 screen (stocks)."""
    return phase1_screen(symbol, asset_type="stock")


def screen_emerging_trend(
    symbol: str,
    *,
    asset_type: str = "stock",
    yahoo_symbol: str | None = None,
) -> dict[str, Any] | None:
    """Alias for unified Phase 1 screen."""
    return phase1_screen(symbol, asset_type=asset_type, yahoo_symbol=yahoo_symbol)


def bull_score(mtf: dict[str, Any], screen: dict[str, Any]) -> dict[str, Any]:
    tfs = mtf.get("timeframes", {})
    syn = mtf.get("synthesis", {})
    conflicts = mtf.get("conflicts", [])
    high_conf = sum(1 for c in conflicts if c.get("severity") == "high")

    score = 0
    reasons: list[str] = []
    penalties: list[str] = []

    if screen.get("golden_cross_weekly") or screen.get("weekly_gc_fresh"):
        spread = screen.get("weekly_sma50_above_200_pct")
        score += 15
        reasons.append(
            f"weekly golden-cross zone (50 SMA +{spread}% above 200)"
            if spread is not None
            else "weekly golden-cross zone"
        )
    elif screen.get("emerging_weekly"):
        score += 10
        gap = screen.get("weekly_sma50_200_gap_pct")
        reasons.append(f"weekly emerging pre-GC (50 SMA {gap}% below 200)" if gap else "weekly emerging pre-GC")
    if screen.get("golden_cross_daily") or screen.get("daily_gc_fresh"):
        spread = screen.get("daily_sma50_above_200_pct")
        score += 10
        reasons.append(
            f"daily golden-cross zone (50 SMA +{spread}% above 200)"
            if spread is not None
            else "daily golden-cross zone"
        )
    elif screen.get("emerging_daily"):
        score += 8
        gap = screen.get("daily_sma50_200_gap_pct")
        reasons.append(f"daily emerging pre-GC (50 SMA {gap}% below 200)" if gap else "daily emerging pre-GC")

    w = tfs.get("weekly", {})
    d = tfs.get("daily", {})
    if w.get("ma_stack") == "bullish":
        score += 12
        reasons.append("weekly bullish MA stack")
    elif w.get("ma_stack") == "mixed_bullish":
        score += 6
        reasons.append("weekly mixed-bullish MA stack")

    if d.get("ma_stack") in ("bullish", "mixed_bullish"):
        score += 5

    w_rsi = w.get("rsi_14")
    if w_rsi and w_rsi < 60:
        score += 5
        reasons.append(f"weekly RSI {w_rsi} not overbought")
    elif w_rsi and w_rsi > 65:
        penalties.append(f"weekly RSI {w_rsi} elevated")

    ext = w.get("extension_from_200sma_pct")
    if ext is not None and ext < 15:
        score += 8
        reasons.append(f"only +{ext}% above weekly 200 SMA (room to run)")
    elif ext is not None and ext > 18:
        penalties.append(f"weekly extended +{ext}% from 200 SMA")

    wy = w.get("wyckoff_hint")
    if wy == "accumulation_possible":
        score += 8
        reasons.append("weekly Wyckoff accumulation possible")
    elif wy == "distribution_warning":
        score -= 15
        penalties.append("weekly distribution warning")

    if syn.get("verdict") == "bullish_aligned":
        score += 15
        reasons.append("MTF bullish aligned")
    elif syn.get("verdict") == "bullish_but_conflicted":
        score += 5
        penalties.append("MTF bullish but conflicted")
    elif syn.get("trade_bias") in ("wait", "short_or_avoid"):
        score -= 10
        penalties.append(f"MTF trade_bias={syn.get('trade_bias')}")

    score -= high_conf * 8
    if high_conf:
        penalties.append(f"{high_conf} high-severity MTF conflict(s)")

    cp = mtf.get("chart_patterns_summary", {})
    tags = cp.get("setup_tags", [])
    if any("breakout" in t for t in tags):
        score += 5
        reasons.append("bullish chart pattern breakout")
    if any("rising_wedge" in t for t in tags):
        score -= 8
        penalties.append("rising wedge detected")

    if screen.get("pct_below_52wk_high") and screen["pct_below_52wk_high"] < -25:
        score += 4
        reasons.append("still well below 52wk high (not crowded)")

    return {
        "bull_score": score,
        "reasons": reasons,
        "penalties": penalties,
        "mtf_verdict": syn.get("verdict"),
        "mtf_trade_bias": syn.get("trade_bias"),
        "mtf_conflicts_high": high_conf,
        "weekly_bias": w.get("bias", {}).get("bias"),
        "daily_bias": d.get("bias", {}).get("bias"),
        "chart_tags": tags,
    }


def fetch_sp500_symbols() -> list[str]:
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as resp:
        text = resp.read().decode()
    symbols: list[str] = []
    for line in text.splitlines()[1:]:
        sym = line.split(",")[0].strip().strip('"')
        if sym:
            symbols.append(sym.replace(".", "-"))
    return symbols


def _mtf_symbol(hit: dict[str, Any]) -> str:
    return hit.get("yahoo_symbol") or hit["symbol"]


def _screen_for_bull_score(hit: dict[str, Any]) -> dict[str, Any]:
    return {
        "weekly_gc_fresh": hit.get("weekly_gc_fresh", False),
        "daily_gc_fresh": hit.get("daily_gc_fresh", False),
        "golden_cross_weekly": hit.get("golden_cross_weekly", False),
        "golden_cross_daily": hit.get("golden_cross_daily", False),
        "emerging_weekly": hit.get("emerging_weekly", False),
        "emerging_daily": hit.get("emerging_daily", False),
        "weekly_sma50_200_gap_pct": hit.get("weekly_sma50_200_gap_pct"),
        "daily_sma50_200_gap_pct": hit.get("daily_sma50_200_gap_pct"),
        "weekly_sma50_above_200_pct": hit.get("weekly_sma50_above_200_pct"),
        "daily_sma50_above_200_pct": hit.get("daily_sma50_above_200_pct"),
        "pct_below_52wk_high": hit.get("pct_below_52wk_high"),
    }


def _phase2_mtf_score(hits: list[dict[str, Any]], top_mtf: int) -> list[dict[str, Any]]:
    finalists = hits[:top_mtf]
    results: list[dict[str, Any]] = []
    for h in finalists:
        try:
            mtf = run_mtf_analysis(_mtf_symbol(h), bars_keep=0)
            scored = bull_score(mtf, _screen_for_bull_score(h))
            results.append({**h, **scored})
        except Exception as exc:
            results.append({**h, "error": str(exc)})
    results.sort(key=lambda x: x.get("bull_score", -999), reverse=True)
    return results


def run_unified_phase1_scan(
    symbols: list[str],
    universe: str,
    workers: int,
    top_mtf: int,
    pretty: bool,
    *,
    asset_type: str = "stock",
    phase2: bool = True,
) -> int:
    """NASDAQ-base stock scan: unified Phase 1; optional Phase 2 MTF + bull_score."""
    print(f"Phase 1 unified screen: {len(symbols)} {universe}", file=sys.stderr)

    def _screen_one(sym: str) -> dict[str, Any] | None:
        at = asset_type
        if at == "stock" and sym.upper().endswith("-USD"):
            at = "crypto"
        return phase1_screen(sym, asset_type=at)

    hits: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_screen_one, s): s for s in symbols}
        done = 0
        for fut in as_completed(futs):
            done += 1
            if done % 200 == 0:
                print(f"  screened {done}/{len(symbols)}, hits={len(hits)}", file=sys.stderr)
            r = fut.result()
            if r:
                hits.append(r)

    sort_phase1_hits(hits)

    out: dict[str, Any] = {
        "scan_date": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d"),
        "universe": universe,
        "asset_type": asset_type,
        "phase1_mode": "unified",
        "phase1_criteria": PHASE1_CRITERIA,
        "phase2_mode": "bull_score" if phase2 else None,
        "symbols_screened": len(symbols),
        "phase1_hits": len(hits),
    }

    if not phase2:
        out["hits"] = hits
        print(json.dumps(out, indent=2 if pretty else None))
        return 0

    print(f"Phase 2: MTF + bull_score on top {min(top_mtf, len(hits))}...", file=sys.stderr)
    results = _phase2_mtf_score(hits, top_mtf)
    out["top_candidates"] = results
    out["other_screen_hits"] = [
        h["symbol"] for h in hits if h["symbol"] not in {r["symbol"] for r in results}
    ]
    print(json.dumps(out, indent=2 if pretty else None))
    return 0


def run_emerging_trend_scan(
    symbols: list[str],
    universe: str,
    workers: int,
    top_mtf: int,
    pretty: bool,
    *,
    asset_type: str = "stock",
) -> int:
    return run_unified_phase1_scan(symbols, universe, workers, top_mtf, pretty, asset_type=asset_type)


def run_phase1_combined_scan(
    symbols: list[str],
    universe: str,
    workers: int,
    top_mtf: int,
    pretty: bool,
    established_fn: Any = None,
    *,
    asset_type: str = "stock",
) -> int:
    """Unified Phase 1 (single pass). `established_fn` kept for CLI compatibility."""
    del established_fn
    return run_unified_phase1_scan(symbols, universe, workers, top_mtf, pretty, asset_type=asset_type)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stock screener: NASDAQ-base Phase 1 + Phase 2 (bull_score) for all universes.",
    )
    parser.add_argument("--sp500-weekly", action="store_true", help="S&P 500 Phase 1 only (no MTF)")
    parser.add_argument(
        "--sp500-upside",
        action="store_true",
        help="S&P 500 scan (alias; same Phase 1 + bull_score as NASDAQ default)",
    )
    parser.add_argument(
        "--sp500-upside-1mo",
        action="store_true",
        help="S&P 500 scan (alias; same Phase 1 + bull_score as NASDAQ default)",
    )
    parser.add_argument("--emerging-trend", action="store_true", help="NASDAQ scan (alias; same as default)")
    parser.add_argument("--sp500-emerging-trend", action="store_true", help="S&P 500 scan (alias; same as default)")
    parser.add_argument("--crypto-emerging-trend", action="store_true", help="Major crypto (Yahoo *-USD)")
    parser.add_argument("--phase1-combined", action="store_true", help="NASDAQ scan (alias; same as default)")
    parser.add_argument("--sp500-phase1-combined", action="store_true", help="S&P 500 scan (same as default)")
    parser.add_argument(
        "--symbols",
        default="",
        help="Comma-separated tickers (e.g. AAPL,BTC-USD,ETH-USD)",
    )
    parser.add_argument("--weeks", type=int, default=5, help="Unused legacy flag (kept for compatibility)")
    parser.add_argument("--limit", type=int, default=0, help="Max symbols to scan (0=all, NASDAQ only)")
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--top-mtf", type=int, default=12, help="Full MTF on top N screen hits")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    phase2 = not args.sp500_weekly

    if args.symbols.strip():
        symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
        universe = "custom"
        asset_type = "crypto" if args.crypto_emerging_trend else "stock"
    elif args.sp500_weekly or args.sp500_upside or args.sp500_upside_1mo or args.sp500_emerging_trend or args.sp500_phase1_combined:
        symbols = fetch_sp500_symbols()
        universe = "S&P 500"
        asset_type = "stock"
    elif args.crypto_emerging_trend:
        symbols = fetch_crypto_symbols()
        universe = "crypto"
        asset_type = "crypto"
    else:
        symbols = fetch_nasdaq_symbols()
        universe = "NASDAQ"
        asset_type = "stock"

    if args.limit and universe == "NASDAQ":
        symbols = symbols[: args.limit]

    return run_unified_phase1_scan(
        symbols,
        universe,
        args.workers,
        args.top_mtf,
        args.pretty,
        asset_type=asset_type,
        phase2=phase2,
    )


if __name__ == "__main__":
    sys.exit(main())
