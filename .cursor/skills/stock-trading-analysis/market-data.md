# Market Data APIs

Live chart data for the stock-trading-analysis skill. **Always run the MTF script before web search** when analyzing a ticker.

## Quick start (required — every analysis)

```bash
python ".cursor/skills/stock-trading-analysis/scripts/fetch_mtf_analysis.py" SOFI --pretty
```

Returns all timeframes (monthly → 1H), indicators, conflicts, and synthesis. See [multi-timeframe.md](multi-timeframe.md).

Single-TF fetch (optional deep dive):

```bash
python ".cursor/skills/stock-trading-analysis/scripts/fetch_chart.py" IREN --pretty
python ".cursor/skills/stock-trading-analysis/scripts/fetch_chart.py" SPY --interval 1wk --range 2y --bars 52
python ".cursor/skills/stock-trading-analysis/scripts/fetch_chart.py" BTC-USD --pretty
```

**Requirements:** Python 3.10+ (stdlib only — no pip install).

---

## Connected APIs

### 1. Yahoo Finance Chart API (primary — no key)

| | |
|---|---|
| **Endpoint** | `https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}` |
| **Auth** | None |
| **Coverage** | US stocks, ETFs, indices, many international tickers |
| **Data** | OHLCV, 52-week range, regular-market quote |
| **Intervals** | `1m`, `5m`, `15m`, `1h`, `1d`, `1wk`, `1mo` |
| **Ranges** | `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max` |

**Symbol examples:** `IREN`, `AAPL`, `SPY`, `BTC-USD`, `ETH-USD`

**Computed by script:** SMA 20/50/200, EMA 20, RSI 14, MA stack, golden/death cross status, extension from 200 SMA, 1M/3M performance, volume vs 20-bar average.

**MTF script adds per timeframe:** MACD, Bollinger Bands, volume trend, price–volume divergence, RSI divergence, candlestick detection, Wyckoff hint, bias score, conflict flags, synthesis verdict.

**Limits:** Unofficial API; rate-limit if hammering requests. Use one call per ticker per analysis.

---

### 2. CoinGecko (crypto — no key)

| | |
|---|---|
| **Endpoint** | `https://api.coingecko.com/api/v3/` |
| **Auth** | None (free tier) |
| **Coverage** | Major cryptocurrencies |
| **Data** | Spot price, 24h/7d/30d change, daily OHLC |
| **Flag** | `--crypto` |

**Built-in symbol map:** BTC, ETH, SOL, XRP, DOGE, ADA, AVAX, LINK

For other coins, use Yahoo `{COIN}-USD` (e.g. `BTC-USD`, `ETH-USD`) for **full daily OHLC + SMA/RSI**. Use `--crypto` for CoinGecko spot price and 24h change (OHLC is sparse on free tier).

**Limits:** ~10–30 calls/min on free tier. OHLC has no volume on free endpoint.

---

### 3. Finnhub (optional — API key)

| | |
|---|---|
| **Endpoint** | `https://finnhub.io/api/v1/quote` |
| **Auth** | `FINNHUB_API_KEY` environment variable |
| **Coverage** | Real-time US quotes (cross-check) |
| **Signup** | [finnhub.io](https://finnhub.io/) — free tier 60 calls/min |

When the key is set, the script adds a `finnhub_quote` overlay to Yahoo stock responses. Skip with `--no-finnhub`.

```powershell
# Windows PowerShell (session)
$env:FINNHUB_API_KEY = "your_key_here"
```

```bash
# macOS/Linux
export FINNHUB_API_KEY="your_key_here"
```

---

### 4. Alpha Vantage (optional — not wired by default)

| | |
|---|---|
| **Endpoint** | `https://www.alphavantage.co/query` |
| **Auth** | `ALPHAVANTAGE_API_KEY` |
| **Signup** | [alphavantage.co](https://www.alphavantage.co/support/#api-key) — 25 calls/day free |

Reserved for future use (fundamentals, earnings). For chart OHLC, Yahoo is sufficient. Set key in env if you extend the script later.

---

## Multi-timeframe workflow (default)

One command — all timeframes:

```bash
python ".cursor/skills/stock-trading-analysis/scripts/fetch_mtf_analysis.py" TICKER --pretty
```

Timeframes fetched: **monthly, weekly, daily, 3mo, 4H, 2H, 1H** (4H/2H aggregated from 1H).

Full rules: [multi-timeframe.md](multi-timeframe.md).

## Single-TF workflow (optional)

```bash
# Weekly bias only
python ".cursor/skills/stock-trading-analysis/scripts/fetch_chart.py" IREN --interval 1wk --range 2y --bars 26 --pretty

# Daily entry only
python ".cursor/skills/stock-trading-analysis/scripts/fetch_chart.py" IREN --interval 1d --range 1y --bars 30 --pretty
```

---

## Output fields (use in analysis)

| JSON path | Use in analysis |
|-----------|-----------------|
| `quote.price` | Current price for level map |
| `quote.fifty_two_week_high/low` | Extension context |
| `technicals.rsi_14` | Overbought/oversold (>70 / <30) |
| `technicals.sma_50`, `sma_200` | MA structure (see moving-averages.md) |
| `technicals.ma_stack` | `bullish`, `bearish`, `mixed_bearish`, `mixed_bullish` |
| `technicals.cross_status` | Golden/death cross state |
| `technicals.extension_from_200sma_pct` | Mean-reversion risk |
| `technicals.volume_vs_avg_pct` | Effort vs result (Wyckoff) |
| `performance.change_1m_pct` | Recent trend |
| `bars[]` | Candlestick patterns, support/resistance |

---

## Fallback order

1. **Run `fetch_mtf_analysis.py`** — primary data source (all timeframes)
2. **Web search** — news, catalysts, analyst targets, insider activity
3. **User chart screenshot** — reconcile with API levels per TF

If Yahoo returns an error, try:
- Adding exchange suffix (`SHOP.TO`, `VOD.L`)
- Crypto via `--crypto` or `{COIN}-USD` on Yahoo
- Web search for quote as last resort (cite source)

---

## Error handling

Script exits code `1` and prints JSON to stderr on failure:

```json
{"error": "Yahoo Finance: No chart data", "symbol": "INVALID"}
```

Do not invent prices if the script fails — report the error and fall back to web search.
