# Chart Patterns — Cup & Handle, Ascending Triangle, Falling & Rising Wedges

Multi-bar patterns for **continuation and reversal**. Use on **weekly (primary)** and **daily (entry)**. Always combine with MTF alignment, volume, and Wyckoff — never trade pattern alone.

**Sources:** [William O'Neil / IBD](https://www.investors.com/how-to-invest/investors-corner/cup-with-handle-everything-you-need-to-know-about-handles-in-bases/), [StockCharts ascending triangle](https://school.stockcharts.com/doku.php?id=chart_analysis:chart_patterns:ascending_triangle_continuation), [StockCharts falling wedge](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/falling-wedge), [StockCharts rising wedge](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/rising-wedge), [Investopedia rising wedge](https://www.investopedia.com/articles/trading/07/rising_wedge.asp), [TradingSim wedges](https://www.tradingsim.com/blog/how-to-trade-rising-and-falling-wedges).

---

## Pattern context rules (all chart patterns)

| Rule | Requirement |
|------|-------------|
| **Timeframe** | State weekly vs daily; weekly pattern > daily pattern for bias |
| **Trend** | Continuation patterns need prior trend; wedges work as **reversal or continuation** (see each pattern) |
| **Volume** | Required for **confirmation**; optional for **early** staging |
| **Location** | Cup/handle after advance; ascending triangle in uptrend or late base |
| **HTF** | Weekly/monthly not in distribution; not extended >25% above 200 SMA without caution |

---

## Cup and Handle (bullish continuation)

William O'Neil's classic base-before-breakout. Wyckoff analog: **accumulation Phase B/C** (cup) → **test** (handle) → **markup** (breakout).

### Structure

```text
        Left rim ───────────── Right rim ── Handle ── BREAKOUT →
              \               /    \    /
               \   U-cup     /      \  /  (≤12% dip)
                \___________/        \/
```

| Component | Ideal criteria (O'Neil / IBD) |
|-----------|-------------------------------|
| **Prior trend** | ≥30% advance before base (swing trades: intact weekly uptrend minimum) |
| **Cup depth** | **12–35%** from left rim high to cup low |
| **Cup shape** | **Rounded U** — not sharp V |
| **Cup duration** | **7–65 weeks** weekly; **~3–6 months** typical; daily analog **35–130 bars** |
| **Handle** | **≥5 days** (≥1 week on weekly chart) |
| **Handle depth** | **≤12%** pullback from right-rim / handle high |
| **Handle location** | **Upper half** of cup; above **10-week (50-day) SMA** |
| **Handle slope** | **Downward drift** — upward-wedging handle is **flawed** |
| **Pivot / buy point** | Handle high + $0.10 (O'Neil); or close above handle high |

### Volume signature (critical)

| Phase | Volume | Meaning |
|-------|--------|---------|
| Left side of cup (decline) | **Heavy** | Climax selling |
| Right side of cup (rise) | **Lighter** | Supply drying up |
| Handle | **Dry up** — below **50-day avg** | Sellers exhausted |
| **Breakout day** | **+40–50%** above 50-day avg (min); higher = stronger | Institutional buying |

### Pattern states (script output)

| State | Meaning | Action |
|-------|---------|--------|
| `cup_forming` | U-base developing; no handle yet | Watch — no entry |
| `handle_forming` | Pullback in upper cup; volume drying | **Early play** — stalk, don't chase |
| `handle_ready` | Handle depth/location valid; at/near pivot | **Set alert** at pivot; wait for breakout |
| `breakout_confirmed` | Close above pivot + volume surge | **Confirmed long** — enter or add on retest |
| `breakout_weak` | Price above pivot but volume <40% avg | **Wait** — high fail risk |
| `failed` | V-shaped cup, wedging handle, or handle >12% | **Avoid** — pattern invalid |

### Entry styles

| Style | Trigger | Stop | Est. edge (if pattern + volume valid) |
|-------|---------|------|--------------------------------------|
| **Early (aggressive)** | Handle forming + volume dry-up + hold 50 SMA | Below handle low or 50 SMA | **~50–55%** — higher false signal rate |
| **Standard (O'Neil)** | Close above pivot on **40%+ volume** | Below handle low | **~60–65%** |
| **Conservative** | Breakout then **retest** of pivot as support | Below retest low | **~65–70%** |

### Probability adjustments

| Confluence | Long thesis |
|------------|-------------|
| Weekly + daily both `handle_ready` or `breakout_confirmed` | **+10%** |
| Handle volume dry-up confirmed | **+8%** |
| Breakout volume ≥40% above 50-day avg | **+10%** |
| V-cup or wedging handle | **−20%** — treat as no pattern |
| HTF overbought (weekly RSI >70) at breakout | **−10%** |
| Below 200 SMA on weekly | **−15%** |

### Setup tags for journal

`cup_and_handle_forming`, `cup_and_handle_ready`, `cup_and_handle_breakout`, `cup_and_handle_failed`

---

## Ascending Triangle (bullish continuation)

Flat **horizontal resistance** + **rising support** (higher lows). Bullish bias **before** breakout ([StockCharts](https://school.stockcharts.com/doku.php?id=chart_analysis:chart_patterns:ascending_triangle_continuation)).

### Structure

```text
Resistance ───────────────────  (flat top, ≥2 touches)
              /\    /\    /\
             /  \  /  \  /  \   higher lows
            /    \/    \/    \
           /                    → BREAKOUT
```

| Component | Ideal criteria |
|-----------|----------------|
| **Bias** | **Bullish continuation** in existing uptrend (reversal at bottom = lower win rate) |
| **Resistance** | Horizontal — highs within **~1.5–2%** band, **≥2–3 touches** |
| **Support** | Rising trendline — **≥3 higher lows** |
| **Duration** | **4–8 weeks** daily; proportionally longer on weekly |
| **Volume in pattern** | **Contracts** — coiling / supply absorption |
| **Breakout** | **Close** above resistance (not wick only) |
| **Breakout volume** | **≥1.5–2×** recent 5–20 bar average ([TradingSim](https://www.tradingsim.com/blog/ascending-triangle), [Strike](https://www.strike.money/technical-analysis/ascending-triangle)) |
| **Target** | **Measured move** = pattern height added to breakout price |

### Momentum confirmation (optional boost)

| Indicator | Bullish confirm |
|-----------|-----------------|
| RSI | **>50** and rising into breakout |
| MACD | Bullish crossover or rising histogram near apex |

### Pattern states (script output)

| State | Meaning | Action |
|-------|---------|--------|
| `triangle_forming` | Higher lows + flat resistance building | Watch |
| `apex_approaching` | Price compressing near resistance; volume low | **Early play** — prepare entry |
| `breakout_confirmed` | Close above resistance + volume expansion | **Confirmed long** |
| `breakout_weak` | Wick above resistance, weak volume, or close back inside | **Failed breakout** — avoid |
| `failed` | Lower lows develop (support breaks) | **Bearish** — pattern invalid |

### Entry styles

| Style | Trigger | Stop | Est. edge |
|-------|---------|------|-----------|
| **Early** | 3rd+ higher low hold + approaching resistance; RSI >50 | Below latest higher low | **~50–55%** |
| **Standard** | Close above resistance + **1.5× volume** | Below last swing low or 20 EMA | **~58–63%** |
| **Conservative** | Breakout + **retest** of resistance as support | Below retest low | **~62–68%** |

### Probability adjustments

| Confluence | Long thesis |
|------------|-------------|
| Continuation in weekly uptrend + aligned MTF | **+10%** |
| Volume contraction in pattern + expansion on breakout | **+8%** |
| Retest of broken resistance holds | **+5%** |
| Breakout on low volume | **−15%** |
| Reversal attempt at bottom of downtrend | **−10%** |
| HTF death cross / distribution | **−15%** |

### Setup tags for journal

`ascending_triangle_forming`, `ascending_triangle_apex`, `ascending_triangle_breakout`, `ascending_triangle_failed`

---

## Falling Wedge (bullish — recovery / continuation)

Downward-sloping **converging** trendlines: both lower highs and lower lows, but the **upper line falls faster** than the lower. Bullish bias **before** breakout ([StockCharts Falling Wedge](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/falling-wedge)). Unlike symmetrical triangles (neutral), falling wedges slope down with a built-in bullish lean.

### Structure

```text
    \  upper (steeper decline)
     \    /\    /\
      \  /  \  /  \   lower highs + lower lows
       \/    \/    \  converging → BREAKOUT UP
```

| Component | Ideal criteria |
|-----------|----------------|
| **Bias** | **Bullish** — resolves **upward** ~68% with volume confirm ([TradingSim](https://www.tradingsim.com/blog/how-to-trade-rising-and-falling-wedges)) |
| **Context** | **Reversal:** after downtrend exhaustion (bullish recovery). **Continuation:** pause within intact uptrend |
| **Trendlines** | Both slope **down**; **≥3 touches** each line; lines **converge** (not parallel) |
| **Slope** | Upper resistance declines **faster** than lower support |
| **Duration** | Weeks to months on daily; proportionally longer on weekly |
| **Volume in pattern** | **Contracts** — selling pressure fading ([Zipmex](https://zipmex.com/blog/falling-wedge/)) |
| **Breakout** | **Close** above upper resistance trendline (not wick only) |
| **Breakout volume** | **Essential** — expand **≥1.5–2×** recent average; weak volume = high fail rate |
| **Target** | **Measured move** = widest wedge height projected above breakout |

### Momentum confirmation (optional boost)

| Indicator | Bullish confirm |
|-----------|-----------------|
| RSI | **Bullish divergence** inside wedge (higher RSI lows while price makes lower lows) |
| MACD | Line crossing above signal at/near breakout |

### Pattern states (script output)

| State | Meaning | Action |
|-------|---------|--------|
| `wedge_forming` | Converging down-sloping lines building | Watch |
| `apex_approaching` | Price compressing near upper line; volume low | **Early stalk** — prepare long |
| `breakout_confirmed` | Close above upper line + volume expansion | **Confirmed long** |
| `breakout_weak` | Above upper line but volume <1.5× avg | **Wait** — false breakout risk |
| `failed` | Break **below** lower support instead | Pattern invalid — bearish |

### Entry styles

| Style | Trigger | Stop | Est. edge |
|-------|---------|------|-----------|
| **Early** | Apex + volume dry-up + RSI bullish divergence | Below lower trendline | **~50–55%** |
| **Standard** | Close above upper trendline + **1.5× volume** | Below last swing low in wedge | **~63–68%** |
| **Conservative** | Breakout + retest of upper line as support | Below retest low | **~65–70%** |

### Probability adjustments

| Confluence | Long thesis |
|------------|-------------|
| Reversal at weekly support / oversold RSI | **+8%** |
| Volume contraction in wedge + expansion on breakout | **+10%** |
| Weekly + daily both `apex_approaching` or `breakout_confirmed` | **+8%** |
| Breakout on thin volume | **−15%** |
| HTF death cross / distribution at breakout | **−12%** |
| Parallel channel (not converging) | **−20%** — not a wedge |

### Setup tags for journal

`falling_wedge_forming`, `falling_wedge_apex`, `falling_wedge_breakout`, `falling_wedge_failed`

---

## Rising Wedge (bearish — exhaustion / continuation)

Upward-sloping **converging** trendlines: higher highs and higher lows, but the **lower support line rises faster** than the upper resistance. Bearish bias **before** breakdown ([StockCharts Rising Wedge](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/rising-wedge), [Investopedia](https://www.investopedia.com/articles/trading/07/rising_wedge.asp)).

### Structure

```text
           /\    /\    /\   upper (shallower rise)
          /  \  /  \  /  \
         /    \/    \/    \  higher highs + higher lows
        /                  \  converging → BREAKDOWN
       /____________________\
      lower (steeper rise)
```

| Component | Ideal criteria |
|-----------|----------------|
| **Bias** | **Bearish** — resolves **downward** ~63% with volume confirm ([TradingSim](https://www.tradingsim.com/blog/how-to-trade-rising-and-falling-wedges)) |
| **Context** | **Reversal:** after uptrend exhaustion (distribution / FOMO fade). **Continuation:** bearish pause in downtrend |
| **Trendlines** | Both slope **up**; **≥3–5 touches** across lines; lines **converge** |
| **Slope** | Lower support rises **faster** than upper resistance — buyers squeezed |
| **Volume in pattern** | **Declines** as wedge matures — waning buying conviction |
| **Breakdown** | **Close** below lower support trendline |
| **Breakdown volume** | **Expansion** on break preferred — confirms supply won |
| **Target** | **Measured move** = widest wedge height projected below breakdown |

### Momentum confirmation (optional boost)

| Indicator | Bearish confirm |
|-----------|-----------------|
| RSI | **Bearish divergence** (lower highs on RSI while price makes higher highs) |
| MACD | Histogram fading / bearish cross near apex |

### Pattern states (script output)

| State | Meaning | Action |
|-------|---------|--------|
| `wedge_forming` | Converging up-sloping lines building | Watch |
| `apex_approaching` | Price compressing near lower line; volume declining | **Early stalk** — prepare short/fade |
| `breakdown_confirmed` | Close below lower line + volume expansion | **Confirmed short** |
| `breakdown_weak` | Below lower line but weak volume | **Wait** — bear trap risk |
| `failed` | Break **above** upper resistance instead | Pattern invalid — bullish |

### Entry styles

| Style | Trigger | Stop | Est. edge |
|-------|---------|------|-----------|
| **Early** | Apex + declining volume + bearish RSI divergence | Above upper trendline | **~50–55%** |
| **Standard** | Close below lower trendline + volume spike | Above last swing high in wedge | **~58–63%** |
| **Conservative** | Breakdown + retest of lower line as resistance | Above retest high | **~62–67%** |

### Probability adjustments

| Confluence | Short thesis |
|------------|--------------|
| Reversal after extended rally / weekly overbought | **+10%** |
| Volume contracts in wedge + expands on breakdown | **+8%** |
| Weekly distribution_warning + rising wedge | **+10%** |
| Breakdown on low volume | **−15%** |
| Strong weekly uptrend + shallow wedge | **−10%** |
| Accelerating volume on each rally leg (channel, not wedge) | **−15%** |

### Setup tags for journal

`rising_wedge_forming`, `rising_wedge_apex`, `rising_wedge_breakdown`, `rising_wedge_failed`

---

## Output requirement (every analysis)

When script detects a chart pattern, report:

```markdown
## Chart patterns
| Pattern | TF | State | Pivot / resistance | Volume confirm | Early vs confirmed |
|---------|----|-------|--------------------|----------------|--------------------|
| Cup & Handle | Weekly | handle_ready | $X | Handle dry: yes | Early — wait pivot break |
| Falling Wedge | Daily | apex_approaching | $X resistance | Contracting: yes | Early — wait upside break |
| Rising Wedge | Weekly | breakdown_confirmed | $X support | 1.8× vol: yes | Confirmed short |
```

State whether trade is **early stalk**, **confirmed entry**, or **wait/invalid**.

---

## Integration with Wyckoff

| Chart pattern | Wyckoff phase |
|---------------|---------------|
| Cup (right side rising) | Accumulation Phase B/C |
| Handle shakeout | Phase C test / Spring-like |
| Cup breakout | Phase D markup / SOS |
| Ascending triangle | Accumulation Phase B (compression) |
| Triangle breakout | Phase D / SOS |
| Falling wedge (recovery) | Late accumulation / selling climax drying up |
| Falling wedge breakout | Phase D markup / SOS |
| Rising wedge (top) | Distribution Phase B — narrowing range on highs |
| Rising wedge breakdown | Phase E markdown / UTAD resolution |

---

## Script detection

`fetch_mtf_analysis.py` runs detection on **weekly** and **daily** bars. Output field: `chart_patterns` per timeframe + aggregated `chart_patterns_summary` in JSON root (`bullish_primary`, `bearish_primary` when both exist).

Discount automated detection **~10%** vs manual chart review — confirm visually when possible.
