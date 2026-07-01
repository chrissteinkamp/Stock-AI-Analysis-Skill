# Market Data APIs

Live chart data for the stock-trading-analysis skill.

## Data source priority

| Priority | Source | When |
|----------|--------|------|
| **1** | **TradingView MCP** | Connected in Cursor (see below) — live quote, MTF TA, TV-aligned indicators |
| **2** | **`fetch_mtf_analysis.py`** | Always — custom patterns (cup & handle, wedges, golden cross), Wyckoff, synthesis |
| **3** | **Web search** | Catalysts, news, analyst targets |
| **4** | **User chart screenshot** | Reconcile levels (especially 6M / log-scale views) |

**Every analysis:** TradingView MCP (if available) **+** `fetch_mtf_analysis.py` **+** web search for fundamentals.

---

## TradingView MCP (primary — live & analytical)

Configured in `.cursor/mcp.json`. Uses [tradingview-mcp-server](https://github.com/atilaahmettaner/tradingview-mcp) (third-party, not affiliated with TradingView Inc.).

### Setup (already done in this project)

```json
{
  "mcpServers": {
    "tradingview": {
      "command": "C:\\Users\\Owner\\.local\\bin\\uvx.exe",
      "args": ["--python", "3.13", "--from", "tradingview-mcp-server", "tradingview-mcp"]
    }
  }
}
```

**After config changes:** restart Cursor → **Settings → MCP** → confirm `tradingview` is green → start a **new agent chat**.

**Requirements:** `uv` + `uvx` at `C:\Users\Owner\.local\bin\` (pre-installed). Package pre-warmed via `uv tool install tradingview-mcp-server`.

### MCP tools to call (per analysis)

| Tool | Use |
|------|-----|
| `yahoo_price` | Live quote, change %, 52w high/low, market state |
| `get_technical_analysis` | Full TV TA — RSI, MACD, Bollinger, MAs, BUY/SELL/HOLD |
| `get_multi_timeframe_analysis` | Weekly → Daily → 4H → 1H → 15m alignment (confluence check) |
| `combined_analysis` | TV technicals + Reddit sentiment + news (optional, for high-conviction calls) |
| `get_candlestick_patterns` | TV candlestick pattern detector (cross-check our script) |
| `get_stock_decision` | 3-layer decision engine + trade setup quality score |
| `market_snapshot` | Macro context (SPX, VIX, sector mood) when relevant |

### Symbol format

Use TradingView exchange prefix:

| Market | Example |
|--------|---------|
| NASDAQ | `NASDAQ:FSLR`, `NASDAQ:AKAM` |
| NYSE | `NYSE:CEG` |
| Crypto | `BINANCE:BTCUSDT` or `BTC-USD` via yahoo_price |
| ETF | `AMEX:SPY` |

If a symbol fails, try `search_symbols` or bare ticker (`FSLR`) — MCP may resolve it.

### What TV MCP gives that Yahoo scripts don't

- **TradingView-aligned** indicator values and BUY/SELL ratings
- **Multi-timeframe confluence** in one call (`get_multi_timeframe_analysis`)
- **Live/near-real-time** quotes via `yahoo_price`
- **Screeners** (`screen_stocks`, `scan_by_signal`) for discovery
- **Backtesting** (`backtest_strategy`, `compare_strategies`) for strategy validation

### What our scripts still do (required)

`fetch_mtf_analysis.py` remains **mandatory** for:

- Custom **cup & handle**, **ascending triangle**, **falling/rising wedge** detection
- **Wyckoff** hints and **HTF/LTF conflict** synthesis
- **Golden/death cross** age and extension from 200 SMA
- **Monthly** bars and **6M-equivalent** macro structure (TV MCP MTF stops at weekly as highest in `get_multi_timeframe_analysis`)

### Reconciliation + independent verdict (required)

TradingView MCP is a **data layer**, not the final decision. The agent must produce an **independent synthesis** that may agree or disagree with TV.

#### What to pull from TradingView MCP

| TV field | How to use |
|----------|------------|
| `yahoo_price` | Anchor all levels to live quote |
| `multi_timeframe_analysis.alignment` | One input to MTF read — cite status + net_score |
| `coin_analysis` RSI/MACD/EMA/SMA | Cross-check against local script; note divergences |
| `buy_sell_signal` / `stock_score` / `grade` | **Cite, don't conclude** — e.g. "TV daily: BUY (score 36, Avoid grade)" |
| `support_resistance` pivots | Merge with pattern pivots from local script |
| `combined_analysis` Reddit/news | Sentiment context only — not a trade trigger |

#### What the agent adds (never skip)

1. **Local `fetch_mtf_analysis.py`** — patterns, Wyckoff, conflicts, synthesis
2. **Wyckoff phase** on weekly/monthly (TV does not provide this)
3. **Pattern battle** when bullish + bearish patterns coexist (e.g. falling wedge vs rising wedge)
4. **HTF/LTF conflict rules** — TV may say LEAN BULLISH while script flags distribution
5. **Fundamental bull/bear merge** + catalyst calendar
6. **Agent `trade_bias`** and execution card — entry/stop/targets with **your** probabilities

#### When sources disagree

| Disagreement | Resolution |
|--------------|--------------|
| Price / RSI (minor drift) | Live price → MCP; RSI → cite both, use trend direction |
| TV BUY vs script `wait` + distribution | **Agent waits** — distribution overrides TV BUY |
| TV LEAN BULLISH vs script `mixed_neutral` + 5 conflicts | **Agent waits or half size** — cite conflict count |
| TV bearish daily vs script golden cross weekly | **Transitioning** — neither full long nor short; define wedge/range |
| Pattern state | **Trust local script** (O'Neil cup rules, wedge detectors) |
| User TV screenshot (6M log cup) | Visual macro structure — reconcile with monthly bars |

#### Required response block (when TV MCP used)

```markdown
## TV MCP vs Agent Reconciliation
| Point | TradingView | Agent (local + synthesis) | Final call |
|-------|-------------|---------------------------|------------|
| MTF bias | | | |
| Near-term signal | | | |
| Pattern | N/A | | |
| Trade bias | | | |
```

**Final call** = agent verdict for the execution card. TV is wrong often enough on conflicted names (e.g. BUY signal + Avoid grade + distribution on weekly) that the agent must resolve explicitly.

#### Do not

- End analysis with only TV's `recommendation.action`
- Treat `stock_score` or Reddit sentiment as edge without technical conflicts review
- Skip `fetch_mtf_analysis.py` because TV MCP ran

---

## Market baselines & relative performance

**Always run for stock scans, portfolio reviews, and crypto calls.** Individual tickers do not exist in a vacuum — SPX/QQQ set the equity tide; **NQ1!** leads the Nasdaq cash open; **BTC** drives crypto beta.

### Baseline symbols

| Asset | Purpose | Yahoo / `fetch_mtf_analysis.py` | TradingView MCP |
|-------|---------|-----------------------------------|-----------------|
| **S&P 500 (SPX)** | Broad US equity benchmark | `^GSPC` or `SPY` (ETF proxy) | `market_snapshot`, `AMEX:SPY` |
| **Nasdaq 100 (QQQ)** | Growth / tech beta benchmark | `QQQ` | `NASDAQ:QQQ`, `combined_analysis` |
| **Nasdaq futures (NQ1!)** | **Overnight → cash open** lead indicator | `NQ=F` | `CME_MINI:NQ1!` |
| **Bitcoin** | Crypto market driver | `BTC-USD` | `coin_analysis` `BINANCE:BTCUSDT` 1W + 1D |

**Macro overlay:** `market_snapshot` — SPX, VIX, top crypto, SPY/QQQ in one call.

### When to use each baseline

| Question | Use |
|----------|-----|
| "Is the overall market supportive for longs?" | SPX + QQQ weekly bias, Wyckoff, RSI |
| "Will Nasdaq gap up/down at the open?" | **NQ1!** daily/4H vs prior close; handle break before 9:30 ET |
| "Should I prefer stock picking vs index?" | Compare pick **peak-in-span %** vs SPX/QQQ same horizon |
| "Is crypto risk-on or risk-off?" | BTC weekly bias; alts typically follow BTC |

### NQ1! → QQQ session logic

1. **NQ1! trades ~23 hours** — price action between US close and next open sets tone.
2. **Handle/breakout on NQ daily** often precedes QQQ tagging its 52-week high on the cash open.
3. **Conflict case:** NQ `distribution_warning` + weekly RSI >75 → fade chase on Nasdaq names even if daily golden cross.
4. **Gap rule:** NQ +0.5% overnight → expect QQQ to open firm; individual Nasdaq names inherit beta.

### Required comparison block (scans & conviction calls)

```markdown
## Market baseline — 1 month (peak-in-span)

| Driver | Price | Agent bias | 1-mo peak est. | vs prior scan picks |
|--------|-------|------------|----------------|---------------------|
| SPX | | | | hurdle rate |
| QQQ | | | | tech beta hurdle |
| NQ1! | | | | open trigger |
| BTC | | | | crypto regime |

**Relative alpha:** [ticker] +X% est. vs QQQ +Y% → +Z% excess if base case hits.
**Regime:** risk-on / risk-off / selective stock-picking
```

**Peak-in-span:** Same rule as single-ticker analysis — highest/lowest **touched** in ~4 weeks, not terminal close.

### Baseline fetch commands

```bash
python ".cursor/skills/stock-trading-analysis/scripts/fetch_mtf_analysis.py" ^GSPC --pretty
python ".cursor/skills/stock-trading-analysis/scripts/fetch_mtf_analysis.py" QQQ --pretty
python ".cursor/skills/stock-trading-analysis/scripts/fetch_mtf_analysis.py" NQ=F --pretty
python ".cursor/skills/stock-trading-analysis/scripts/fetch_mtf_analysis.py" BTC-USD --pretty
```

TradingView MCP: `market_snapshot` + `coin_analysis` (BTC 1W/1D) + `combined_analysis` (QQQ 1W).

---

## Bitcoin Rainbow Chart (macro cycle context)

Long-term valuation bands from log regression on full BTC history ([blockchaincenter.net](https://www.blockchaincenter.net/en/bitcoin-rainbow-chart/)). **Not a price predictor** — use with MTF + exchange data.

### When to run

- Estimating **cycle bottom ranges** (vs prior bear lows)
- Checking if price is in **capitulation / accumulation / euphoric** zone
- Reconciling social targets (e.g. “$40k”) against regression bands

### Data sources

| Source | Use |
|--------|-----|
| `fetch_mtf_analysis.py BTC-USD` | Weekly/monthly structure, Wyckoff |
| Kraken/Coinbase MCP | Live spot, OHLC |
| Rainbow regression | Macro band context |

### Band model (9 bands)

Centre line (classic V2): `log10(price) = 2.9065 × ln(days_since_genesis) − 19.493`

Bands are fixed **log10 offsets** from centre: capitulation (−0.40) → euphoric (+0.40).

Also fit a **power-law regression** on daily closes since 2012 (dynamic centre — better for current cycle).

| Band | Offset | Typical meaning |
|------|--------|-----------------|
| Capitulation | −0.40 | Prior cycle troughs (2015, 2018, 2022) |
| Deep value | −0.30 | DCA zone |
| Accumulation | −0.20 | Recovery begins |
| Fair value | 0.00 | Regression centre |

### Prior cycle drawdowns (from prior ATH)

| Bear | ATH → Low | Drawdown |
|------|-----------|----------|
| 2013→2015 | ~$1,177 → $152 | ~87% |
| 2017→2018 | ~$19,666 → $3,122 | ~84% |
| 2021→2022 | ~$69,000 → $15,476 | ~78% |

Diminishing drawdown trend suggests **~72–75%** as a stretch cap from current cycle ATH (~$126k), not repeating 84–87%.

### Agent rule

- Rainbow **capitulation** + **technical support** converging = higher-confidence bottom zone
- Price **below** rainbow capitulation = cycle is breaking historical band fit (rare; cite tail risk)
- Never cite rainbow alone — merge with `fetch_mtf_analysis.py` verdict

---

## Quick start — local scripts (required every analysis)

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

**Requirements:** Python 3.10+ (stdlib only — no pip install for scripts).

---

## Connected APIs (scripts)

### 1. Yahoo Finance Chart API (script primary — no key)

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

**With TradingView MCP connected:**

1. MCP: `yahoo_price` + `get_multi_timeframe_analysis` + `get_technical_analysis`
2. Script: `fetch_mtf_analysis.py TICKER --pretty`
3. Reconcile conflicts; cite both sources in the matrix

**Script only (MCP unavailable):**

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

1. **TradingView MCP** — live quote + MTF TA (if connected)
2. **Run `fetch_mtf_analysis.py`** — patterns, Wyckoff, synthesis (always)
3. **Web search** — news, catalysts, analyst targets, insider activity
4. **User chart screenshot** — reconcile with API levels per TF (especially 6M / log charts)

If Yahoo returns an error, try:
- TradingView MCP `yahoo_price` or `get_technical_analysis`
- Adding exchange suffix (`SHOP.TO`, `VOD.L`, `NASDAQ:FSLR`)
- Crypto via `--crypto` or `{COIN}-USD` on Yahoo
- Web search for quote as last resort (cite source)

---

## Error handling

Script exits code `1` and prints JSON to stderr on failure:

```json
{"error": "Yahoo Finance: No chart data", "symbol": "INVALID"}
```

MCP tools may return `{"error": {"code": "...", "message": "..."}}` — wait and retry on rate limits.

Do not invent prices if both MCP and script fail — report the error and fall back to web search.

---

## Troubleshooting (Windows)

| Symptom | Fix |
|---------|-----|
| MCP timeout on first launch | Pre-warm: `uv tool install --python 3.13 tradingview-mcp-server` |
| `uvx` not found | Use full path `C:\Users\Owner\.local\bin\uvx.exe` in mcp.json |
| Server not in chat | Restart Cursor; start **new** agent chat |
| Empty TA response | Retry after 30s (TV rate limit); use `NASDAQ:TICKER` format |
