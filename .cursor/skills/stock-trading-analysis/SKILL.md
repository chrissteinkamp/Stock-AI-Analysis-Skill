---
name: stock-trading-analysis
description: >-
  Tactical stock analysis with mandatory multi-timeframe review (monthly, weekly,
  daily, 3mo, 4H, 2H, 1H): RSI, MACD, Bollinger, golden/death cross, 50/200 SMA,
  Wyckoff, candlesticks, cup & handle, ascending triangle, falling/rising wedge, HTF/LTF conflict detection. Run
  TradingView MCP (when connected) + fetch_mtf_analysis.py for patterns.
  Log every analysis via trading_journal.py for
  outcome calibration. For horizons ≤3 months, price targets mean peak-in-span
  (highest/lowest touched during the window), not terminal close. Use for charts, tickers, entries, stops, targets,
  buying, shorting, or trade execution cards.
---

# Stock Trading Analysis

Tactical trade framework for **long or short** setups. Default horizon: **weeks to a few months**, not multi-year structural bets unless the user asks.

## Core principles

1. **Separate price from thesis** — A real bull story can still be overextended (short). A weak story can still bounce technically (long). State which you are trading.
2. **Context defines candlesticks** — Hammer at support ≠ Hanging Man at resistance. Always label pattern + location + trend.
3. **Higher timeframe leads** — Monthly/weekly for bias; daily/4H/2H/1H for entry timing only. **Never trade LTF alone against HTF exhaustion** (see [multi-timeframe.md](multi-timeframe.md)).
4. **Wait for confirmation** — Prefer closed candles (weekly/daily) before high-conviction entries; intraday is for timing only.
5. **Never chase** — Fade strength into resistance (short) or buy weakness into support (long) when possible.
6. **Risk first** — Every plan includes entry, stop, targets, position size (1% account risk default).
7. **Peak targets in span (≤3 months)** — When the user asks for price targets over a time span of **3 months or less**, they mean the **highest potential price reached at any point during that window** (lowest for shorts), **not** the expected closing price at the end of the period. Always label peak vs terminal explicitly (see Step 6).
8. **Learn from outcomes** — Log every analysis; calibrate probabilities from tracked win rates ([learning.md](learning.md)).
9. **TradingView informs — agent decides** — Use TradingView MCP for live quotes, TV-aligned indicators, and MTF confluence. **Never stop at TV's BUY/SELL label.** Always add independent analysis: Wyckoff, custom patterns, conflict resolution, bull/bear merge, and your own trade_bias (which may **override** TV when distribution, volume, or HTF/LTF conflicts disagree).
10. **Not financial advice** — Frame as technical analysis; user makes final decisions.

## Workflow

Copy this checklist and track progress:

```
Analysis Progress:
- [ ] 0. Run trading_journal.py update-outcomes + calibrate — read adjustments ([learning.md](learning.md))
- [ ] 1. Clarify direction (long / short / wait) and horizon
- [ ] 2. TradingView MCP: yahoo_price + multi_timeframe_analysis + coin_analysis (1W/1D) (if connected)
- [ ] 2b. Run fetch_mtf_analysis.py — all timeframes + patterns + conflicts (required)
- [ ] 2c. Reconcile TV vs script — note agreements AND disagreements (required)
- [ ] 2d. **Market baselines** — SPX, QQQ, NQ1!, BTC (required for scans & single-ticker calls)
- [ ] 3. Fill merged MTF Matrix + **Independent Agent Synthesis** (not TV verdict alone)
- [ ] 4. Apply journal calibration adjustments to scenario probabilities
- [ ] 5. Candlestick patterns at correct context per TF (see patterns.md)
- [ ] 5b. Chart patterns — cup & handle, ascending triangle, falling/rising wedge on weekly/daily (see chart-patterns.md)
- [ ] 6. Wyckoff phase mapping on weekly/monthly (see wyckoff.md)
- [ ] 7. Fundamental + sentiment research (web search)
- [ ] 8. Synthesize bull vs bear; build execution card
- [ ] 9. Log analysis to trading_journal.py with setup_tags (required)
- [ ] 10. State invalidation and "do not trade" zones
```

### Step 1 — Frame the trade

Ask or infer:

| Question | Why |
|----------|-----|
| Long or short? | Sets pattern interpretation and trigger logic |
| Tactical or swing? | Default tactical (2–8 weeks) |
| What vehicle? | Shares, options, or inverse/leveraged ETF |
| Target horizon? | If **≤3 months**: report **peak-in-span** highs/lows, not terminal close |

**Horizon target rule (user default):** For any requested span **≤3 months** (e.g. "1 month upside", "3-month targets", "peak gain in 4 weeks"):

| User means | Agent delivers |
|------------|----------------|
| **Peak during span** | Highest price (long) or lowest (short) **touched at any time** in the window |
| **NOT** | Where price is expected to **close** on the last day of the span |

Always state both when useful:
- *"Peak potential in 30 days: $19.25–$21.50"*
- *"Terminal close estimate (if different): $18–$19 chop"*

For horizons **>3 months**, peak-in-span still applies unless the user explicitly asks for an end-of-period close forecast.

**Short default thesis (when user is skeptical of parabolic moves):** Mean-reversion fade of FOMO/overbought exhaustion — **not** a bet that the business fails.

**Long default thesis:** Pullback entry in an intact uptrend, or reversal confirmation at support — **not** blind chase at all-time highs.

### Step 2 — Gather data

**Learning loop (run first — before MTF fetch):**

```bash
python ".cursor/skills/stock-trading-analysis/scripts/trading_journal.py" update-outcomes
python ".cursor/skills/stock-trading-analysis/scripts/trading_journal.py" calibrate
```

Read `journal/calibration.json`: apply `probability_adjustments`, cite `lessons` when relevant. Full rules: **[learning.md](learning.md)**.

**TradingView MCP (primary when connected — see [market-data.md](market-data.md)):**

Call these MCP tools **before** the local script when the `tradingview` server is available:

| Tool | Purpose |
|------|---------|
| `yahoo_price` | Live quote, 52w range, market state |
| `multi_timeframe_analysis` | TV MTF confluence (weekly → 15m) |
| `coin_analysis` | Full TV indicators per TF (1W, 1D, 1M) + BUY/SELL/HOLD |
| `combined_analysis` | Optional — TV TA + Reddit + news (do not treat as sole verdict) |

Use exchange prefix: `NASDAQ:FSLR`, `NYSE:CEG`, etc.

### TradingView + independent analysis (required)

TradingView MCP provides **data and one opinion** (`buy_sell_signal`, `stock_score`, `grade`, MTF `recommendation`). The **agent verdict** is separate and must appear in every response.

| Use TV MCP for | Add your own analysis for |
|----------------|---------------------------|
| Live price, 52w range | Wyckoff phase (weekly/monthly) |
| TV RSI, MACD, EMA/SMA values | Custom patterns (cup/handle, wedges, triangles) |
| TV MTF alignment score | `conflicts[]` from local script (distribution, extension) |
| Support/resistance pivots | Bull vs bear fundamental merge |
| `buy_sell_signal` as **one input** | **Final trade_bias** — may be `wait` when TV says BUY |
| Reddit/news from `combined_analysis` | Probability-weighted scenarios + execution card |

**Do NOT:**
- Copy TV `recommendation.action` or `buy_sell_signal` as your verdict without scrutiny
- Quote TV `stock_score` / `grade` as the conclusion — cite them, then resolve
- Skip local script because TV already said BUY or SELL
- Ignore conflicts when TV and script disagree (explain which source wins and why)

**DO:**
- Present a **TV MCP vs Agent** reconciliation block when they disagree
- Override TV when local script shows `distribution_warning`, weak rally volume, or high-severity conflicts
- Weight TV more for **live price** and **indicator cross-check**; weight local script more for **patterns and Wyckoff**
- State **your** entry, stop, targets — not TV's generic "cautious buy"

Example override: *TV daily BUY + LEAN BULLISH MTF, but weekly distribution_warning and rising wedge on daily → agent verdict: **wait_or_reduce_size**, not full long.*

**Local MTF script (required for EVERY analysis — patterns + synthesis):**

```bash
python ".cursor/skills/stock-trading-analysis/scripts/fetch_mtf_analysis.py" TICKER --pretty
```

Reconcile TV MCP levels with script output — see [market-data.md](market-data.md) reconciliation table. **Agent synthesis merges both**; neither source is the final word alone.

**Market baselines (required for scans and conviction calls):**

Before ranking individual stocks or crypto, pull the **driving forces** for each asset class and compare 1-month **peak-in-span** upside. Full symbol map and comparison template: [market-data.md](market-data.md#market-baselines--relative-performance).

| Baseline | Role | Yahoo / script | TradingView |
|----------|------|----------------|-------------|
| **SPX** (`^GSPC`) | Broad US equity tide | `fetch_mtf_analysis.py ^GSPC` | `market_snapshot` |
| **QQQ** | Nasdaq growth / tech beta | `fetch_mtf_analysis.py QQQ` | `combined_analysis` NASDAQ:QQQ |
| **NQ1!** (`NQ=F`) | **Pre-market lead** — how cash session opens | `fetch_mtf_analysis.py NQ=F` | `CME_MINI:NQ1!` |
| **BTC** | Crypto market driver | `fetch_mtf_analysis.py BTC-USD` | `coin_analysis` BINANCE:BTCUSDT |

**BTC macro cycles:** For bottom-range / multi-year context, add **Rainbow Chart** regression bands — see [market-data.md](market-data.md#bitcoin-rainbow-chart-macro-cycle-context). Merge with MTF; rainbow alone is not a trade signal.

**Alpha rule:** A stock pick must justify itself vs **SPX/QQQ** (stocks) or **BTC** (crypto). If benchmark 1-mo peak is ~+2% and a name offers ~+10% with aligned MTF, cite **relative upside**. If benchmarks show distribution / `wait`, downgrade individual longs even when TV says BUY.

**NQ1! → QQQ:** Futures trade ~23h; overnight NQ breaks often gap QQQ/NDX at the US open. Report NQ handle/pivot levels as the **session trigger** for Nasdaq beta names.

This fetches **all standard timeframes** in one call:

| TF | Source | Role |
|----|--------|------|
| Monthly | Yahoo `1mo` | Macro bias, extension, RSI extremes |
| Weekly | Yahoo `1wk` | **Primary bias**, stops, Wyckoff |
| Daily | Yahoo `1d` | Entry triggers, crosses |
| 3-month | Yahoo `1d/3mo` | Recent structure |
| 4H / 2H | Aggregated from `1h` | Entry timing |
| 1H | Yahoo `1h` | Precise entry — never sole signal |

**Indicators computed per TF:** RSI 14, SMA 20/50/200, EMA 20, MACD, Bollinger Bands, MA stack, golden/death cross, volume trend, price–volume divergence, RSI divergence, candlestick patterns, **chart patterns (cup & handle, ascending triangle, falling/rising wedge on weekly/daily)**, Wyckoff hint, per-TF bias score.

Read `chart_patterns_summary` in JSON output — report pattern, state, direction (bullish/bearish), early vs confirmed play. Check `bullish_primary` and `bearish_primary` when both exist. Full rules: [chart-patterns.md](chart-patterns.md).

**Output includes:** `conflicts[]` (HTF vs LTF flags) and `synthesis` (verdict, trade_bias, alignment).

Full MTF rules, matrix template, and conflict resolution: **[multi-timeframe.md](multi-timeframe.md)**.

Single-TF deep dive (optional): [fetch_chart.py](scripts/fetch_chart.py) — see [market-data.md](market-data.md).

Crypto: `fetch_mtf_analysis.py BTC-USD --pretty` (Yahoo) or `fetch_chart.py BTC --crypto`.

**Do not guess prices or indicators** — run the script. **Do not skip MTF** even if the user asks about one timeframe only; always report HTF context.

**From user:** Chart screenshots — reconcile with API levels per timeframe.

**From web (after MTF fetch):** catalysts, analyst targets, insider activity, short interest, sector peers.

### Step 3 — Multi-timeframe technical analysis (required)

**Always present these blocks** (template in [multi-timeframe.md](multi-timeframe.md)):

1. **Multi-Timeframe Matrix** — all 8 TFs with bias, RSI, MA stack, cross, MACD, volume, Wyckoff
2. **MTF Conflicts** — every flag from script, especially `severity: high`
3. **MTF Synthesis** — HTF bias vs LTF setup, alignment, trade implication in plain English

Example trade implication: *"4H shows a reasonable entry, but weekly is overbought with declining volume and distribution warning — risky buy; wait or half size."*

#### Indicators and structure (every TF)

| Tool | What to assess |
|------|----------------|
| **RSI (14)** | Monthly >80 or weekly >70 = stretched; <30 = oversold. Flag **divergence**. Monthly RSI >90 = extreme exhaustion. Thresholds vary by TF — see [multi-timeframe.md](multi-timeframe.md). |
| **50 / 200 SMA** | Trend stack, dynamic S/R, extension from 200 SMA. Full rules: [moving-averages.md](moving-averages.md) |
| **EMA 20** | Intraday/short-term dynamic S/R |
| **MACD (12,26,9)** | Momentum direction; bullish/bearish cross forming vs confirmed |
| **Bollinger Bands** | Band position, squeeze (width_pct), mean-reversion at bands |
| **Golden / Death Cross** | **State timeframe**. Weekly overrides daily. Daily overrides 4H/1H. |
| **Volume** | Trend + price–volume divergence. Rally on declining volume = weak. Wyckoff effort vs result. |
| **Candlesticks** | Pattern + **timeframe + location + trend**. [patterns.md](patterns.md) |
| **Chart patterns** | Cup & handle, ascending triangle, **falling wedge** (bullish), **rising wedge** (bearish) on **weekly/daily**. [chart-patterns.md](chart-patterns.md) |
| **Wyckoff** | Weekly/monthly phase and hints. [wyckoff.md](wyckoff.md) |

#### HTF vs LTF conflict rules (mandatory)

| Condition | Verdict |
|-----------|---------|
| LTF bullish + HTF overbought + declining volume | **Risky buy** — do not cite LTF alone |
| LTF bullish + HTF distribution_warning | **Wait or fade** — not full-size long |
| Daily golden cross + weekly death cross | Pullback, not new bull market |
| All TFs overbought + extended >25% from 200 SMA | Tactical short or wait — not long |
| HTF bearish + LTF oversold | Counter-trend bounce only — tight stop |

Apply **−10% direction probability** per high-severity MTF conflict ([reference.md](reference.md)).

#### Timeframe roles

| TF | Role |
|----|------|
| Monthly | Macro extension, RSI extremes, major S/R |
| Weekly | **Primary bias**, pattern confirmation, main stop placement |
| Daily | Entry triggers, rejection candles |
| 3-month | Recent swing structure |
| 4H / 2H | Fine-tune entry, bounce-fade zones |
| 1H | Precise entry only — never sole signal |

### Step 4 — Fundamental + sentiment merge

Build a **two-column synthesis** (not one-sided):

**Bull case:** Catalyst, earnings growth, sector tailwind, analyst upgrades, contracted revenue, etc.

**Bear / skeptic case:** Valuation vs consensus targets, insider selling, cyclical industry history, stock above Street targets, parabolic move, extreme RSI, short interest rising.

**Resolution line:** State whether price appears to **price in perfection** or still has room. Example: *"Shortage is real; stock is 30% above consensus — tactical fade, not anti-fundamental."*

### Step 5 — Decision logic

#### Short triggers (pick applicable)

- Weekly reversal at resistance (hanging man, shooting star, red close below prior body)
- Failed retest of key resistance after breakdown
- RSI overbought + bearish divergence + declining volume on rally
- Rising wedge: close below lower trendline on expanding volume (bearish exhaustion)
- Price extended above 50/200 SMA and above analyst consensus

#### Long triggers (pick applicable)

- Pullback to rising 50 SMA or channel support with hold
- Hammer / reversal at support + volume capitulation
- Breakout and **hold** above resistance on volume
- Cup & handle: pivot break on **40%+ volume** (O'Neil) or handle dry-up for early stalk
- Ascending triangle: **close** above flat resistance on **1.5–2× volume**
- Falling wedge: **close** above upper trendline on **1.5–2× volume** (bullish recovery)
- RSI oversold bounce in intact weekly uptrend

#### Wait / no trade

- Price in no-man's land between key levels
- Candle not yet closed (weekly especially)
- Conflicting HTF (monthly extended) vs LTF (bounce) — reduce size or wait for LTF rejection/confirmation

#### Leveraged / inverse ETFs

If user mentions 2x short or inverse ETF (e.g. SNDQ for SNDK):
- Note **daily decay** — tactical only
- Inverse ETF bottoming (RSI oversold, channel support) can **confirm** underlying short thesis
- Do not treat as 1:1 mirror over long holds

### Step 6 — Probability-weighted scenarios (required output)

Every analysis must include **estimated probabilities** — ranges, not false precision. Label: *"Estimates based on pattern context, Wyckoff phase, MA structure, and historical studies — not guarantees."*

#### Peak-in-span targets (≤3 months — user default)

When the user requests targets, upside, or scenarios over **≤3 months**:

1. **T1 / T2 / T3** = **peak prices** likely to be **tagged at some point** during the span (scale-out zones), not the expected settlement price at horizon end.
2. **Scenario "peak zone"** = range of the **intraperiod high** (long) or **intraperiod low** (short), e.g. *"40% prob peak touches $21.50 in the next 30 days"*.
3. **Report peak gain %** from current price: *"+14% peak potential in 30 days"* — distinct from *"+6% if still at $19 on day 30"*.
4. If price may spike then fade, say so: *"Peak $21 possible week 2–3; terminal close may retreat to $19."*
5. Label every target table column: **"Peak (in span)"** not just "Target" when horizon ≤90 days.

**Shorts:** peak-in-span = **lowest** price touched in the window (maximum favorable excursion down).

**Journal:** log `targets[].price` as peak-in-span levels; `notes` may include terminal-close estimate if different.

**Method:** Start from MTF synthesis + **journal calibration adjustments** ([learning.md](learning.md)), then apply confluence from [reference.md](reference.md), [multi-timeframe.md](multi-timeframe.md), [patterns.md](patterns.md), [chart-patterns.md](chart-patterns.md), [wyckoff.md](wyckoff.md), [moving-averages.md](moving-averages.md).

When journal has **n ≥ 10 reviewed** outcomes, cite historical win rates for matching `setup_tags` or `mtf_alignment` in the analysis.

Deliver at minimum:

| Output block | Contents |
|--------------|----------|
| **Direction scenarios** | 2–3 outcomes with **peak zones in span** (not terminal close only) and **% ranges** summing ~100% |
| **Target reach** | Per T1/T2/T3: **peak-in-span** reach probability (e.g. T1 **55%** to touch $X at any point in 30 days) |
| **Confidence** | High / Medium / Low based on confluence count |
| **Key confluence** | Bullet list of what raised or lowered odds |

**Never** cite pattern win rates without trend context. Discount all stats **10–15%** for high-beta individual stocks vs index backtests.

### Step 7 — Execution card (required output)

Deliver a compact card for every completed analysis. Full template: [reference.md](reference.md).

Minimum fields:

| Field | Content |
|-------|---------|
| **Ticker / bias / horizon** | e.g. SNDK short, 2–8 weeks |
| **Thesis** | One sentence: what you're trading (price vs fundamentals) |
| **Wyckoff phase** | If applicable (e.g. Distribution Phase C/D) |
| **MA structure** | Per-TF golden/death cross and stack (from MTF matrix) |
| **Trigger** | What must happen before entry |
| **Entry zone** | Price range; prefer bounce-fade (short) or dip-buy (long) |
| **Stop** | Hard invalidation level |
| **T1 / T2 / T3** | **Peak-in-span** scale-out targets (≤3mo) with % to exit **and touch probability during window** |
| **Invalidation** | When to cover / exit entirely |
| **Size** | `Shares = (Account × Risk%) ÷ (Entry − Stop)`; default 1% risk |
| **Do not** | Chase, widen stop, average down against plan |

### Step 8 — Present clearly

Structure final response:

1. **Verdict** (long / short / wait) + confidence — one line
2. **Multi-Timeframe Matrix** + **MTF Conflicts** + **MTF Synthesis** (required)
3. **Technical summary** — HTF → LTF narrative; Wyckoff; key patterns
4. **Scenario probabilities** — direction + **peak-in-span** target reach table (MTF-adjusted)
5. **Fundamental + sentiment** — bull/bear merge
6. **Execution card**
7. **Risks** — what makes the trade wrong (3–5 bullets)
8. **Journal note** — "Logged to analysis journal" (when n reviewed > 0, cite relevant historical win rate)

Use ASCII level maps for clarity. Include chart OHLC when known.

### Step 9 — Log analysis (required — every prompt)

After delivering the analysis, log to the persistent journal:

```bash
python ".cursor/skills/stock-trading-analysis/scripts/trading_journal.py" log --file entry.json
```

Required fields: `symbol`, `asset_type`, `horizon`, `direction`, `verdict`, `trade_bias`, `mtf_verdict`, `mtf_alignment`, `mtf_conflicts_high`, `price_at_analysis`, `targets`, `stop`, `confidence`, `confluence_score`, `setup_tags` (3–8 tags).

See [learning.md](learning.md) for template and tag list. **Never skip logging** — this is how win rates improve over time.

## Entry timing preferences

| Setup | Preferred entry | Avoid |
|-------|-----------------|-------|
| Short after weekly reversal | Bounce into resistance that fails | Shorting flush into support |
| Long after pullback | Support hold + reversal candle | Buying extended breakout without retest |
| Breakout long | Close above resistance, enter retest or continuation | Chasing gap without stop plan |
| Breakdown short | Close below support, enter failed retest | Shorting into climax volume at lows |

## Risk rules (enforce in every plan)

- Max **1% account risk** per trade unless user specifies otherwise
- Stop is **fixed** — no widening
- No averaging down on losing positions
- High-beta names: **smaller size**, wider stops in dollars
- Time stop optional for tactical trades (4–8 weeks) if thesis stalls

## Additional resources

- **Learning loop + journal (required):** [learning.md](learning.md)
- Journal CLI: [scripts/trading_journal.py](scripts/trading_journal.py)
- **Multi-timeframe analysis (required reading):** [multi-timeframe.md](multi-timeframe.md)
- MTF fetch script: [scripts/fetch_mtf_analysis.py](scripts/fetch_mtf_analysis.py)
- Live chart APIs + single-TF script: [market-data.md](market-data.md)
- Execution templates, probability framework: [reference.md](reference.md)
- Candlestick patterns + win-rate tiers: [patterns.md](patterns.md)
- Cup & handle, ascending triangle, falling/rising wedge: [chart-patterns.md](chart-patterns.md)
- Wyckoff distribution/accumulation: [wyckoff.md](wyckoff.md)
- Golden/death cross by timeframe: [moving-averages.md](moving-averages.md)
- Worked example (SNDK tactical short): [examples.md](examples.md)
