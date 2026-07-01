#!/usr/bin/env python3
"""Scan NASDAQ for fresh golden crosses with bullish confluence (under-the-radar bias)."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from fetch_chart import USER_AGENT, cross_status, fetch_yahoo, ma_stack, pct_change, rsi, sma
from fetch_mtf_analysis import run_mtf_analysis

MEGA_CAPS = {
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST",
    "NFLX", "AMD", "INTC", "QCOM", "ADBE", "CRM", "ORCL", "CSCO", "PYPL", "UBER",
    "ABNB", "COIN", "MSTR", "PLTR", "SMCI", "ARM", "MU", "LRCX", "KLAC", "AMAT",
    "MRVL", "WDC", "SNPS", "CDNS", "CRWD", "PANW", "FTNT", "DDOG", "SNOW", "NET",
}


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
        if not sym or sym in MEGA_CAPS:
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
        if etf != "N" or test != "N" or sym in MEGA_CAPS:
            continue
        if len(sym) > 5 or "$" in sym or "." in sym:
            continue
        symbols.append(sym)
    return symbols


def fresh_golden_cross(closes: list[float], lookback: int) -> tuple[bool, int | None]:
    if len(closes) < 210:
        return False, None
    s50_n, s200_n = sma(closes, 50), sma(closes, 200)
    if not s50_n or not s200_n or s50_n <= s200_n:
        return False, None
    for lb in range(1, lookback + 1):
        sub = closes[:-lb]
        if len(sub) < 200:
            continue
        s50, s200 = sma(sub, 50), sma(sub, 200)
        if s50 and s200 and s50 < s200 * 0.998:
            return True, lb
    return False, None


def quick_screen(symbol: str) -> dict[str, Any] | None:
    try:
        wk = fetch_yahoo(symbol, "1wk", "5y")
        dy = fetch_yahoo(symbol, "1d", "2y")
    except Exception:
        return None

    w_closes = [b["close"] for b in wk["bars"]]
    d_closes = [b["close"] for b in dy["bars"]]
    w_t, d_t = wk["technicals"], dy["technicals"]
    price = dy["quote"]["price"]
    hi52 = dy["quote"].get("fifty_two_week_high")
    lo52 = dy["quote"].get("fifty_two_week_low")

    w_fresh, w_age = fresh_golden_cross(w_closes, 12)
    d_fresh, d_age = fresh_golden_cross(d_closes, 30)
    if not w_fresh and not d_fresh:
        return None

    # Under-the-radar / not already extended filters (weekly primary)
    w_ext = w_t.get("extension_from_200sma_pct")
    w_rsi = w_t.get("rsi_14")
    d_rsi = d_t.get("rsi_14")
    w_chg3 = wk["performance"].get("change_3m_pct")
    d_chg3 = dy["performance"].get("change_3m_pct")

    if w_ext is not None and w_ext > 22:
        return None
    if w_rsi is not None and w_rsi > 68:
        return None
    if d_rsi is not None and d_rsi > 72:
        return None
    if w_chg3 is not None and w_chg3 > 45:
        return None

    pct_from_ath = pct_change(price, hi52) if hi52 else None
    if pct_from_ath is not None and pct_from_ath > -3:
        return None  # at/near 52wk high — likely already noticed

    w_cross = w_t["cross_status"]
    d_cross = d_t["cross_status"]
    if "death_cross" in w_cross and "forming" not in w_cross and d_fresh:
        return None  # daily GC inside weekly DC — skill flags as risky

    stack = w_t["ma_stack"]
    if stack == "bearish":
        return None

    return {
        "symbol": symbol,
        "price": price,
        "weekly_gc_fresh": w_fresh,
        "weekly_gc_age_bars": w_age,
        "daily_gc_fresh": d_fresh,
        "daily_gc_age_bars": d_age,
        "weekly_cross": w_cross,
        "daily_cross": d_cross,
        "weekly_ma_stack": stack,
        "weekly_ext_pct": w_ext,
        "weekly_rsi": w_rsi,
        "daily_rsi": d_rsi,
        "weekly_chg_3m": w_chg3,
        "daily_chg_3m": d_chg3,
        "pct_below_52wk_high": round(pct_from_ath, 1) if pct_from_ath is not None else None,
        "pct_above_52wk_low": round(pct_change(price, lo52), 1) if lo52 else None,
    }


def bull_score(mtf: dict[str, Any], screen: dict[str, Any]) -> dict[str, Any]:
    tfs = mtf.get("timeframes", {})
    syn = mtf.get("synthesis", {})
    conflicts = mtf.get("conflicts", [])
    high_conf = sum(1 for c in conflicts if c.get("severity") == "high")

    score = 0
    reasons: list[str] = []
    penalties: list[str] = []

    if screen["weekly_gc_fresh"]:
        score += 15
        age = screen.get("weekly_gc_age_bars")
        reasons.append(f"fresh weekly golden cross (~{age}w ago)" if age else "fresh weekly golden cross")
    if screen["daily_gc_fresh"]:
        score += 10
        age = screen.get("daily_gc_age_bars")
        reasons.append(f"fresh daily golden cross (~{age}d ago)" if age else "fresh daily golden cross")

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


def screen_sp500_weekly_gc(symbol: str, lookback_weeks: int) -> dict[str, Any] | None:
    try:
        wk = fetch_yahoo(symbol, "1wk", "5y")
    except Exception:
        return None
    closes = [b["close"] for b in wk["bars"]]
    fresh, age = fresh_golden_cross(closes, lookback_weeks)
    if not fresh:
        return None
    t = wk["technicals"]
    s50, s200 = t.get("sma_50"), t.get("sma_200")
    spread = round((s50 / s200 - 1) * 100, 2) if s50 and s200 else None
    hi = wk["quote"].get("fifty_two_week_high")
    price = wk["quote"]["price"]
    return {
        "symbol": symbol,
        "price": price,
        "weeks_since_cross": age,
        "cross_status": t["cross_status"],
        "ma_stack": t["ma_stack"],
        "spread_50_over_200_pct": spread,
        "weekly_rsi": t["rsi_14"],
        "ext_200sma_pct": t["extension_from_200sma_pct"],
        "chg_3m_pct": wk["performance"].get("change_3m_pct"),
        "pct_below_52wk_high": round(pct_change(price, hi), 1) if hi else None,
    }


def screen_sp500_bullish_upside(symbol: str) -> dict[str, Any] | None:
    try:
        wk = fetch_yahoo(symbol, "1wk", "5y")
        dy = fetch_yahoo(symbol, "1d", "2y")
    except Exception:
        return None
    wt, dt = wk["technicals"], dy["technicals"]
    price = dy["quote"]["price"]
    hi52 = dy["quote"].get("fifty_two_week_high")
    if not hi52 or price <= 0:
        return None
    upside_to_high = round((hi52 / price - 1) * 100, 1)
    w_stack = wt["ma_stack"]
    if w_stack not in ("bullish", "mixed_bullish", "mixed"):
        return None
    if "death_cross" in wt.get("cross_status", "") and "forming" not in wt.get("cross_status", ""):
        return None
    w_ext, w_rsi = wt.get("extension_from_200sma_pct"), wt.get("rsi_14")
    if w_ext is not None and w_ext > 35:
        return None
    if w_rsi is not None and w_rsi > 72:
        return None
    if upside_to_high < 8:
        return None
    closes_w = [b["close"] for b in wk["bars"]]
    w_gc, w_gc_age = fresh_golden_cross(closes_w, 16)
    d_gc, d_gc_age = fresh_golden_cross([b["close"] for b in dy["bars"]], 30)
    return {
        "symbol": symbol,
        "price": price,
        "upside_to_52wk_high_pct": upside_to_high,
        "weekly_ma_stack": w_stack,
        "weekly_cross": wt["cross_status"],
        "daily_cross": dt["cross_status"],
        "weekly_gc_fresh": w_gc,
        "weekly_gc_age_bars": w_gc_age,
        "daily_gc_fresh": d_gc,
        "daily_gc_age_bars": d_gc_age,
        "weekly_ext_pct": w_ext,
        "weekly_rsi": w_rsi,
        "weekly_chg_3m": wk["performance"].get("change_3m_pct"),
    }


def upside_score(mtf: dict[str, Any], screen: dict[str, Any]) -> dict[str, Any]:
    bull = bull_score(mtf, screen)
    syn = mtf.get("synthesis", {})
    tfs = mtf.get("timeframes", {})
    w, m = tfs.get("weekly", {}), tfs.get("monthly", {})
    score = bull["bull_score"]
    upside = screen.get("upside_to_52wk_high_pct") or 0
    score += min(upside * 1.2, 40)
    cp = mtf.get("chart_patterns_summary", {})
    primary = cp.get("primary") or {}
    peak_target = screen["price"] * (1 + upside / 100)
    target_note = f"52-wk high ${peak_target:.2f}"
    mt = primary.get("measured_target")
    if mt and mt > screen["price"]:
        pattern_upside = (mt / screen["price"] - 1) * 100
        if pattern_upside > upside * 0.5:
            peak_target = mt
            target_note = f"pattern target ${mt:.2f}"
            score += min(pattern_upside * 0.3, 15)
    if syn.get("verdict") == "bullish_aligned":
        score += 12
    elif syn.get("verdict") == "bullish_but_conflicted":
        score += 4
    elif syn.get("trade_bias") in ("short_or_avoid", "wait"):
        score -= 8
    if m.get("rsi_14") and m["rsi_14"] > 75:
        score -= 10
    if w.get("wyckoff_hint") == "distribution_warning":
        score -= 12
    est_peak_gain_pct = round((peak_target / screen["price"] - 1) * 100, 1)
    prob = 50
    if syn.get("verdict") == "bullish_aligned":
        prob += 10
    if screen.get("weekly_gc_fresh") or screen.get("daily_gc_fresh"):
        prob += 5
    prob -= 10 * bull["mtf_conflicts_high"]
    prob = max(35, min(72, prob))
    return {
        **bull,
        **screen,
        "upside_score": round(score, 1),
        "est_peak_target": round(peak_target, 2),
        "est_peak_gain_pct": est_peak_gain_pct,
        "target_basis": target_note,
        "reach_prob_3mo_pct": prob,
        "pattern": primary.get("pattern"),
        "pattern_state": primary.get("state"),
    }


def upside_score_1mo(mtf: dict[str, Any], screen: dict[str, Any]) -> dict[str, Any]:
    """Score peak gain potential over ~4 weeks (1 month)."""
    bull = bull_score(mtf, screen)
    syn = mtf.get("synthesis", {})
    tfs = mtf.get("timeframes", {})
    w, d, h4 = tfs.get("weekly", {}), tfs.get("daily", {}), tfs.get("4h", {})
    price = screen["price"]
    score = bull["bull_score"]

    if syn.get("verdict") == "bullish_aligned":
        score += 18
    elif syn.get("verdict") == "bullish_but_conflicted":
        score += 6
    elif syn.get("trade_bias") in ("short_or_avoid",):
        score -= 15

    if d.get("bias", {}).get("bias") == "bullish":
        score += 10
    if h4.get("bias", {}).get("bias") == "bullish":
        score += 6

    if screen.get("daily_gc_fresh"):
        score += 12
    if screen.get("weekly_gc_fresh"):
        score += 10

    cp = mtf.get("chart_patterns_summary", {})
    primary = cp.get("primary") or {}
    state = primary.get("state", "")
    pattern = primary.get("pattern", "")

    if state == "breakout_confirmed":
        score += 16
    elif state in ("handle_ready", "apex_approaching"):
        score += 14
    elif state in ("wedge_forming", "triangle_forming", "handle_forming"):
        score += 8

    if pattern == "rising_wedge" and state in ("apex_approaching", "wedge_forming"):
        score -= 10

    pivot = primary.get("pivot") or primary.get("resistance")
    peak_target = price
    target_note = "near-term resistance"

    if pivot and pivot > price:
        peak_target = pivot * 1.02
        target_note = f"pivot/resistance ${pivot:.2f}"

    mt = primary.get("measured_target")
    if mt and mt > price:
        one_mo_cap = price * 1.18
        peak_target = min(mt, one_mo_cap)
        target_note = f"pattern target (1mo cap) ${peak_target:.2f}"

    hi_upside = screen.get("upside_to_52wk_high_pct") or 0
    if hi_upside <= 15 and hi_upside >= 3:
        ath_target = price * (1 + hi_upside / 100)
        if ath_target > peak_target:
            peak_target = ath_target
            target_note = f"52-wk high ${ath_target:.2f}"

    if w.get("wyckoff_hint") == "distribution_warning":
        score -= 14
    if w.get("rsi_14") and w["rsi_14"] > 68:
        score -= 6
    if d.get("rsi_14") and d["rsi_14"] > 72:
        score -= 8

    est_peak_gain_pct = round((peak_target / price - 1) * 100, 1)
    est_peak_gain_pct = min(est_peak_gain_pct, 20.0)

    prob = 48
    if syn.get("verdict") == "bullish_aligned":
        prob += 12
    if state in ("breakout_confirmed", "handle_ready", "apex_approaching"):
        prob += 8
    if screen.get("daily_gc_fresh") or screen.get("weekly_gc_fresh"):
        prob += 5
    prob -= 12 * bull["mtf_conflicts_high"]
    prob = max(38, min(75, prob))

    return {
        **bull,
        **screen,
        "horizon": "1 month",
        "upside_score_1mo": round(score, 1),
        "est_peak_target": round(peak_target, 2),
        "est_peak_gain_pct": est_peak_gain_pct,
        "target_basis": target_note,
        "reach_prob_1mo_pct": prob,
        "pattern": pattern,
        "pattern_state": state,
    }


def run_sp500_upside_1mo_scan(workers: int, top_mtf: int, pretty: bool) -> int:
    symbols = fetch_sp500_symbols()
    print(f"Phase 1: {len(symbols)} S&P 500 (1-month upside)...", file=sys.stderr)
    hits: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(screen_sp500_bullish_upside, s): s for s in symbols}
        for i, fut in enumerate(as_completed(futs), 1):
            if i % 100 == 0:
                print(f"  {i}/{len(symbols)} hits={len(hits)}", file=sys.stderr)
            r = fut.result()
            if r:
                if r.get("upside_to_52wk_high_pct", 0) > 25:
                    r["upside_to_52wk_high_pct"] = min(r["upside_to_52wk_high_pct"], 25)
                hits.append(r)

    hits.sort(
        key=lambda x: (
            x.get("daily_gc_fresh", False),
            x.get("weekly_gc_fresh", False),
            x.get("weekly_ma_stack") == "bullish",
            -(x.get("weekly_ext_pct") or 99),
        ),
        reverse=True,
    )
    finalists = hits[:top_mtf]
    print(f"Phase 2: MTF on {len(finalists)}...", file=sys.stderr)
    results: list[dict[str, Any]] = []
    for h in finalists:
        try:
            mtf = run_mtf_analysis(h["symbol"], bars_keep=0)
            results.append(upside_score_1mo(mtf, h))
        except Exception as exc:
            results.append({**h, "error": str(exc)})

    results.sort(key=lambda x: x.get("upside_score_1mo", -999), reverse=True)
    out = {
        "horizon": "1 month peak gain estimate",
        "universe": "S&P 500",
        "symbols_screened": len(symbols),
        "phase1_hits": len(hits),
        "top_picks": results[:5],
        "runners_up": results[5:10],
    }
    print(json.dumps(out, indent=2 if pretty else None))
    return 0


def run_sp500_upside_scan(workers: int, top_mtf: int, pretty: bool) -> int:
    symbols = fetch_sp500_symbols()
    print(f"Phase 1: {len(symbols)} S&P 500 bullish upside screen...", file=sys.stderr)
    hits: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(screen_sp500_bullish_upside, s): s for s in symbols}
        for i, fut in enumerate(as_completed(futs), 1):
            if i % 100 == 0:
                print(f"  {i}/{len(symbols)} hits={len(hits)}", file=sys.stderr)
            r = fut.result()
            if r:
                hits.append(r)
    hits.sort(key=lambda x: x["upside_to_52wk_high_pct"], reverse=True)
    finalists = hits[:top_mtf]
    print(f"Phase 2: MTF on {len(finalists)}...", file=sys.stderr)
    results: list[dict[str, Any]] = []
    for h in finalists:
        try:
            mtf = run_mtf_analysis(h["symbol"], bars_keep=0)
            results.append(upside_score(mtf, h))
        except Exception as exc:
            results.append({**h, "error": str(exc)})
    results.sort(key=lambda x: x.get("upside_score", -999), reverse=True)
    out = {
        "horizon": "3 months peak gain estimate",
        "universe": "S&P 500",
        "symbols_screened": len(symbols),
        "phase1_hits": len(hits),
        "top_picks": results[:5],
        "runners_up": results[5:10],
    }
    print(json.dumps(out, indent=2 if pretty else None))
    return 0


def run_sp500_weekly_gc_scan(lookback_weeks: int, workers: int, pretty: bool) -> int:
    symbols = fetch_sp500_symbols()
    print(f"Screening {len(symbols)} S&P 500 symbols (weekly GC within {lookback_weeks} weeks)...", file=sys.stderr)
    hits: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(screen_sp500_weekly_gc, s, lookback_weeks): s for s in symbols}
        for i, fut in enumerate(as_completed(futs), 1):
            if i % 100 == 0:
                print(f"  {i}/{len(symbols)}", file=sys.stderr)
            r = fut.result()
            if r:
                hits.append(r)
    hits.sort(key=lambda x: (x["weeks_since_cross"], x["symbol"]))
    out = {
        "universe": "S&P 500",
        "timeframe": "weekly",
        "lookback_weeks": lookback_weeks,
        "matches": len(hits),
        "hits": hits,
    }
    print(json.dumps(out, indent=2 if pretty else None))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sp500-weekly", action="store_true", help="Screen S&P 500 for weekly golden cross only")
    parser.add_argument("--sp500-upside", action="store_true", help="Top S&P 500 peak-gain candidates (3mo)")
    parser.add_argument("--sp500-upside-1mo", action="store_true", help="Top S&P 500 peak-gain candidates (1mo)")
    parser.add_argument("--weeks", type=int, default=5, help="Weekly GC lookback (5 weeks ~ 1 month)")
    parser.add_argument("--limit", type=int, default=0, help="Max symbols to scan (0=all)")
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--top-mtf", type=int, default=12, help="Full MTF on top N screen hits")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    if args.sp500_weekly:
        return run_sp500_weekly_gc_scan(args.weeks, args.workers, args.pretty)
    if args.sp500_upside:
        return run_sp500_upside_scan(args.workers, max(args.top_mtf, 20), args.pretty)
    if args.sp500_upside_1mo:
        return run_sp500_upside_1mo_scan(args.workers, max(args.top_mtf, 30), args.pretty)

    symbols = fetch_nasdaq_symbols()
    if args.limit:
        symbols = symbols[: args.limit]

    print(f"Scanning {len(symbols)} NASDAQ symbols...", file=sys.stderr)
    hits: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(quick_screen, s): s for s in symbols}
        done = 0
        for fut in as_completed(futs):
            done += 1
            if done % 200 == 0:
                print(f"  screened {done}/{len(symbols)}, hits={len(hits)}", file=sys.stderr)
            r = fut.result()
            if r:
                hits.append(r)

    # Rank screen: weekly GC preferred, lower extension, lower RSI
    hits.sort(
        key=lambda x: (
            x["weekly_gc_fresh"],
            x["daily_gc_fresh"],
            -(x["weekly_ext_pct"] or 99),
            -(x["weekly_rsi"] or 99),
        ),
        reverse=True,
    )

    finalists = hits[: args.top_mtf]
    results: list[dict[str, Any]] = []
    for h in finalists:
        try:
            mtf = run_mtf_analysis(h["symbol"], bars_keep=0)
            scored = bull_score(mtf, h)
            results.append({**h, **scored})
        except Exception as exc:
            results.append({**h, "error": str(exc)})

    results.sort(key=lambda x: x.get("bull_score", -999), reverse=True)
    out = {
        "scan_date": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d"),
        "symbols_screened": len(symbols),
        "phase1_hits": len(hits),
        "criteria": {
            "fresh_weekly_gc": "within 12 weeks",
            "fresh_daily_gc": "within 30 days",
            "max_weekly_extension_200sma": "22%",
            "max_weekly_rsi": 68,
            "max_3m_weekly_gain": "45%",
            "min_below_52wk_high": "3%",
            "excluded": "mega-cap hype list",
        },
        "top_candidates": results,
        "other_screen_hits": [h["symbol"] for h in hits if h["symbol"] not in {r["symbol"] for r in results}],
    }
    print(json.dumps(out, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
