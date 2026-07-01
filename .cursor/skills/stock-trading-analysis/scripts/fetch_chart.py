#!/usr/bin/env python3
"""Fetch live chart data for stock-trading-analysis skill.

Primary: Yahoo Finance chart API (no key) — stocks, ETFs, indices.
Crypto: CoinGecko (no key) or Yahoo (BTC-USD, ETH-USD, etc.).
Optional: FINNHUB_API_KEY, ALPHAVANTAGE_API_KEY from environment.

Usage:
  python fetch_chart.py IREN
  python fetch_chart.py BTC --crypto
  python fetch_chart.py SPY --interval 1wk --range 2y
  python fetch_chart.py AAPL --bars 30 --pretty
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

USER_AGENT = "Mozilla/5.0 (compatible; StockScreenerAI/1.0)"
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "ADA": "cardano",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
}


def http_get(url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={**(headers or {}), "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    k = 2 / (period + 1)
    result = sum(values[:period]) / period
    for v in values[period:]:
        result = v * k + result * (1 - k)
    return result


def rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(-period, 0):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def pct_change(current: float, prior: float) -> float | None:
    if prior == 0:
        return None
    return ((current / prior) - 1.0) * 100.0


def ma_stack(price: float, s50: float | None, s200: float | None) -> str:
    if s50 is None or s200 is None:
        return "insufficient_data"
    if price > s50 > s200:
        return "bullish"
    if price < s50 < s200:
        return "bearish"
    if price < s200 < s50:
        return "mixed_bearish"
    if price > s200 > s50:
        return "mixed_bullish"
    return "mixed"


def cross_status(s50: float | None, s200: float | None) -> str:
    if s50 is None or s200 is None:
        return "unknown"
    diff_pct = abs(s50 - s200) / s200 * 100 if s200 else 0
    if s50 > s200:
        return "golden_cross" if diff_pct > 0.5 else "golden_cross_forming"
    if s50 < s200:
        return "death_cross" if diff_pct > 0.5 else "death_cross_forming"
    return "neutral"


def parse_yahoo_bars(result: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    meta = result["meta"]
    q = result["indicators"]["quote"][0]
    ts = result["timestamp"]
    bars: list[dict[str, Any]] = []
    for i, t in enumerate(ts):
        close = q["close"][i]
        if close is None:
            continue
        bars.append(
            {
                "date": datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d"),
                "open": q["open"][i],
                "high": q["high"][i],
                "low": q["low"][i],
                "close": close,
                "volume": q["volume"][i],
            }
        )
    return bars, meta


def fetch_yahoo(symbol: str, interval: str, range_: str) -> dict[str, Any]:
    params = urllib.parse.urlencode({"interval": interval, "range": range_})
    url = f"{YAHOO_CHART.format(symbol=urllib.parse.quote(symbol.upper()))}?{params}"
    data = http_get(url)
    results = data.get("chart", {}).get("result")
    if not results:
        err = data.get("chart", {}).get("error", {}).get("description", "No chart data")
        raise RuntimeError(f"Yahoo Finance: {err}")
    bars, meta = parse_yahoo_bars(results[0])
    if not bars:
        raise RuntimeError(f"Yahoo Finance: no OHLC bars for {symbol}")
    closes = [b["close"] for b in bars]
    price = meta.get("regularMarketPrice") or closes[-1]
    prev_close = meta.get("previousClose") or (closes[-2] if len(closes) > 1 else price)
    s20 = sma(closes, 20)
    s50 = sma(closes, 50)
    s200 = sma(closes, 200)
    ext = pct_change(price, s200) if s200 else None
    avg_vol_20 = sma([float(b["volume"] or 0) for b in bars], 20)

    return {
        "source": "yahoo_finance",
        "symbol": meta.get("symbol", symbol.upper()),
        "currency": meta.get("currency", "USD"),
        "exchange": meta.get("fullExchangeName") or meta.get("exchangeName"),
        "interval": interval,
        "range": range_,
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "quote": {
            "price": round(price, 4),
            "previous_close": round(prev_close, 4),
            "change_pct": round(pct_change(price, prev_close) or 0, 2),
            "day_high": meta.get("regularMarketDayHigh"),
            "day_low": meta.get("regularMarketDayLow"),
            "fifty_two_week_high": meta.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": meta.get("fiftyTwoWeekLow"),
        },
        "technicals": {
            "sma_20": round(s20, 4) if s20 else None,
            "sma_50": round(s50, 4) if s50 else None,
            "sma_200": round(s200, 4) if s200 else None,
            "ema_20": round(ema(closes, 20), 4) if ema(closes, 20) else None,
            "rsi_14": round(rsi(closes), 2) if rsi(closes) else None,
            "extension_from_200sma_pct": round(ext, 2) if ext is not None else None,
            "ma_stack": ma_stack(price, s50, s200),
            "cross_status": cross_status(s50, s200),
            "avg_volume_20": round(avg_vol_20, 0) if avg_vol_20 else None,
            "latest_volume": bars[-1]["volume"],
            "volume_vs_avg_pct": round(pct_change(float(bars[-1]["volume"] or 0), avg_vol_20) or 0, 1)
            if avg_vol_20
            else None,
        },
        "performance": {
            "change_1m_pct": round(pct_change(closes[-1], closes[-22]), 2) if len(closes) >= 22 else None,
            "change_3m_pct": round(pct_change(closes[-1], closes[-66]), 2) if len(closes) >= 66 else None,
        },
        "bars": bars,
        "bar_count": len(bars),
    }


def fetch_coingecko(symbol: str, days: int = 365) -> dict[str, Any]:
    coin_id = COINGECKO_IDS.get(symbol.upper())
    if not coin_id:
        raise RuntimeError(f"Unknown crypto ticker {symbol}. Known: {', '.join(sorted(COINGECKO_IDS))}")

    price_url = (
        "https://api.coingecko.com/api/v3/simple/price?"
        + urllib.parse.urlencode(
            {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_7d_change": "true",
                "include_30d_change": "true",
            }
        )
    )
    price_data = http_get(price_url)[coin_id]

    chart_url = (
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
        f"?vs_currency=usd&days={days}"
    )
    ohlc = http_get(chart_url)
    bars = []
    for row in ohlc:
        ts_ms, o, h, l, c = row
        bars.append(
            {
                "date": datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": None,
            }
        )
    closes = [b["close"] for b in bars]
    price = price_data["usd"]
    s50 = sma(closes, 50)
    s200 = sma(closes, 200)
    ext = pct_change(price, s200) if s200 else None

    return {
        "source": "coingecko",
        "symbol": symbol.upper(),
        "coin_id": coin_id,
        "currency": "USD",
        "interval": "1d",
        "range": f"{days}d",
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "quote": {
            "price": price,
            "change_24h_pct": round(price_data.get("usd_24h_change", 0), 2),
            "change_7d_pct": round(price_data.get("usd_7d_change", 0), 2) if price_data.get("usd_7d_change") is not None else None,
            "change_30d_pct": round(price_data.get("usd_30d_change", 0), 2) if price_data.get("usd_30d_change") is not None else None,
        },
        "technicals": {
            "sma_50": round(s50, 4) if s50 else None,
            "sma_200": round(s200, 4) if s200 else None,
            "rsi_14": round(rsi(closes), 2) if rsi(closes) else None,
            "extension_from_200sma_pct": round(ext, 2) if ext is not None else None,
            "ma_stack": ma_stack(price, s50, s200),
            "cross_status": cross_status(s50, s200),
        },
        "bars": bars,
        "bar_count": len(bars),
    }


def fetch_finnhub_quote(symbol: str) -> dict[str, Any] | None:
    key = os.environ.get("FINNHUB_API_KEY")
    if not key:
        return None
    url = "https://finnhub.io/api/v1/quote?" + urllib.parse.urlencode({"symbol": symbol.upper(), "token": key})
    try:
        q = http_get(url)
        if q.get("c") == 0 and q.get("h") == 0:
            return None
        return {
            "source": "finnhub",
            "price": q["c"],
            "open": q["o"],
            "high": q["h"],
            "low": q["l"],
            "previous_close": q["pc"],
            "change_pct": round(pct_change(q["c"], q["pc"]) or 0, 2),
        }
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
        return None


def trim_payload(payload: dict[str, Any], bars_to_keep: int) -> dict[str, Any]:
    if bars_to_keep and payload.get("bars"):
        payload = dict(payload)
        payload["bars"] = payload["bars"][-bars_to_keep:]
        payload["bars_trimmed"] = True
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch live chart data for analysis")
    parser.add_argument("symbol", help="Ticker (IREN, SPY) or crypto (BTC with --crypto)")
    parser.add_argument("--crypto", action="store_true", help="Use CoinGecko for crypto")
    parser.add_argument("--interval", default="1d", help="Yahoo interval: 1d, 1wk, 1mo, 1h, etc.")
    parser.add_argument("--range", dest="range_", default="1y", help="Yahoo range: 1mo, 3mo, 6mo, 1y, 2y, 5y")
    parser.add_argument("--bars", type=int, default=30, help="Recent bars to include in output (0 = all)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--no-finnhub", action="store_true", help="Skip Finnhub quote overlay")
    args = parser.parse_args()

    try:
        if args.crypto:
            payload = fetch_coingecko(args.symbol)
        else:
            payload = fetch_yahoo(args.symbol, args.interval, args.range_)
            if not args.no_finnhub:
                overlay = fetch_finnhub_quote(args.symbol)
                if overlay:
                    payload["finnhub_quote"] = overlay

        payload = trim_payload(payload, args.bars)
        indent = 2 if args.pretty else None
        print(json.dumps(payload, indent=indent))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc), "symbol": args.symbol.upper()}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
