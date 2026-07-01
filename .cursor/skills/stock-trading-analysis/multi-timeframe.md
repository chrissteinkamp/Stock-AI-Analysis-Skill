# Multi-Timeframe Analysis (MTF)

**Required for every stock analysis prompt.** Higher timeframe leads; lower timeframe times entries. Never trade an LTF signal that fights HTF exhaustion.

Run before any analysis:

```bash
python ".cursor/skills/stock-trading-analysis/scripts/fetch_mtf_analysis.py" TICKER --pretty
```

---

## Timeframe hierarchy

| Priority | Timeframe | Role | Key indicators |
|----------|-----------|------|----------------|
| 1 (highest) | **Monthly** | Macro trend, RSI extremes (>80 / >90), major S/R, extension from 200 SMA | RSI, 50/200 SMA, MACD, Wyckoff phase |
| 2 | **Weekly** | **Primary bias**, pattern confirmation, main stop placement, golden/death cross | RSI (>70 = stretched), volume vs prior weeks, candlesticks |
| 3 | **Daily** | Entry triggers, rejection candles, daily cross status | RSI, 50/200 SMA, MACD, Bollinger |
| 4 | **3-month (daily bars)** | Recent structure, swing context | Performance, support/resistance clusters |
| 5 | **4H** | Swing entry timing, bounce/fade zones | RSI, EMA20, volume divergence |
| 6 | **2H** | Fine-tune entry (aggregated from 1H) | Same as 4H |
| 7 (lowest) | **1H** | Scalp / precise entry only — **never sole signal** | RSI, short-term MA stack |

**Override rule:** Weekly overrides daily. Daily overrides 4H/2H/1H. Monthly overrides weekly for extension/exhaustion calls.

---

## Indicators computed per timeframe

| Indicator | Source | Use |
|-----------|--------|-----|
| **RSI (14)** | Script | Monthly >80, weekly >70 = stretched; <30 = oversold. Flag zone in output. |
| **SMA 20 / 50 / 200** | Script | MA stack, dynamic S/R, extension % from 200 |
| **EMA 20** | Script | Short-term trend, intraday support/resistance |
| **Golden / Death Cross** | Script | 50 vs 200 SMA cross status — **state timeframe** |
| **MACD (12,26,9)** | Script | Momentum direction, cross forming vs confirmed |
| **Bollinger Bands (20,2)** | Script | Band position: upper_band / lower_band / squeeze (width_pct) |
| **Volume trend** | Script | increasing / declining / stable vs 20-bar avg |
| **Price–volume divergence** | Script | Rally on declining volume = weak (Wyckoff effort vs result) |
| **RSI divergence** | Script | Bearish: price HH + RSI LH. Bullish: price LL + RSI HL |
| **Candlestick patterns** | Script | Last-bar: doji, engulfing, hammer, shooting star — **always add location context** |
| **Wyckoff hint** | Script | distribution_warning / accumulation_possible / markup_confirmed / markdown |
| **Per-TF bias** | Script | bullish / bearish / neutral + score + reasons |

See also: [moving-averages.md](moving-averages.md), [patterns.md](patterns.md), [wyckoff.md](wyckoff.md).

---

## Required output structure (every analysis)

Copy this block into every analysis response:

```markdown
## Multi-Timeframe Matrix

| TF | Bias | RSI | MA Stack | Cross | MACD | Volume | Wyckoff | Key note |
|----|------|-----|----------|-------|------|--------|---------|----------|
| Monthly | | | | | | | | |
| Weekly | | | | | | | | |
| Daily | | | | | | | | |
| 3mo | | | | | | | | |
| 4H | | | | | | | | |
| 2H | | | | | | | | |
| 1H | | | | | | | | |

## MTF Conflicts (if any)
- [severity] flag — message

## MTF Synthesis
- **HTF bias:** [monthly/weekly verdict]
- **LTF setup:** [4H/1H/daily entry quality]
- **Alignment:** aligned / conflicted
- **Trade implication:** [e.g. "4H looks buyable but weekly overbought + declining volume = risky long — wait or half size"]
```

---

## Conflict rules (automatic flags from script)

The script detects these conflicts. **Always surface them in the analysis.**

| Flag | Severity | Meaning | Trade implication |
|------|----------|---------|-------------------|
| `ltf_entry_vs_htf_overbought` | **High** | 4H/daily looks buyable; weekly/monthly RSI overbought | **Risky long** — bull trap / fade zone |
| `bullish_ltf_on_exhausted_htf` | **High** | LTF bullish + HTF overbought + declining volume | Classic distribution — do not chase |
| `weekly_distribution` | **High** | Wyckoff distribution warning on weekly | Institutions selling into strength |
| `daily_weekly_cross_conflict` | Medium | Daily golden cross inside weekly death cross | Pullback, not reversal — reduce long conviction |
| `monthly_extended` / `weekly_extended` | Medium | >25% above 200 SMA | Mean-reversion risk — smaller size, tighter stops |
| `weak_rally_[tf]` | Medium | Price up, volume down on that TF | Weak rally — wait for volume confirmation |
| `oversold_ltf_in_bearish_htf` | Medium | 1H oversold in daily bear trend | Bounce trade only — not a trend long |

Apply **−10% direction probability** per high-severity conflict ([reference.md](reference.md)).

---

## Decision logic — HTF vs LTF

### When LTF says BUY but HTF says WAIT (conflicted)

```text
4H/1H: bullish (support hold, MACD cross)
Weekly: overbought OR declining volume OR distribution_warning

→ Verdict: RISKY BUY at best
→ Action: Wait for HTF RSI to cool (<65 weekly) OR entry only with half size + tight stop
→ Do NOT cite LTF alone as justification
```

### When HTF and LTF align bullish

```text
Weekly: neutral/bullish, not overbought, volume confirming
Daily: above 50 SMA, RSI 40–65, MACD bullish
4H: pullback to support holding

→ Verdict: Favorable long setup
→ Action: Full size per execution card (1% risk default)
```

### When HTF bearish, LTF oversold

```text
Weekly/Daily: death cross, below 200 SMA
1H/4H: RSI oversold bounce

→ Verdict: Counter-trend bounce only
→ Action: Scalp with tight stop — not a swing long
```

### When all TFs overbought

```text
Monthly/Weekly/Daily RSI >70, extension >25% from 200 SMA

→ Verdict: Tactical SHORT or WAIT — not a long entry
→ Action: Fade into resistance per short framework
```

---

## RSI thresholds by timeframe

| TF | Oversold | Caution | Overbought | Extreme |
|----|----------|---------|------------|---------|
| Monthly | <30 | 70–80 | >80 | >90 (exhaustion) |
| Weekly | <30 | 60–70 | >70 | >80 |
| Daily | <30 | 60–70 | >70 | >80 |
| 4H / 1H | <30 | 55–65 | >65–70 | >75 |

---

## Wyckoff per timeframe

| Hint | Read |
|------|------|
| `distribution_warning` | HTF: institutions distributing — favor shorts/fades at resistance |
| `accumulation_possible` | HTF: selling exhausting on low volume — watch for spring |
| `markup_confirmed` | Trend leg up with volume — trend-following longs OK |
| `markdown` | Active sell phase — avoid longs |
| `range/consolidation` | Wait for boundary break |

Phase mapping (weekly/monthly only for swing trades): see [wyckoff.md](wyckoff.md).

---

## Candlestick context (all TFs)

Patterns from the script are **hints only**. Apply [patterns.md](patterns.md) context rules:

- Hammer **at support** after decline = bullish
- Same shape **at resistance** after rally = hanging man (bearish)
- Engulfing at resistance after extended move = Tier 1 short signal
- Doji alone = indecision — wait for next candle

Always state: **pattern + timeframe + location + trend**.

---

## Synthesis verdict labels (from script)

| `synthesis.verdict` | Meaning |
|---------------------|---------|
| `bullish_aligned` | HTF and LTF agree bullish, no high-severity conflicts |
| `bullish_but_conflicted` | Net bullish but HTF exhaustion flags — reduce size / wait |
| `bearish_aligned` | HTF and LTF agree bearish |
| `bearish_but_conflicted` | Net bearish with conflicting bounces |
| `mixed_neutral` | No clear edge — **default to WAIT** |

| `synthesis.trade_bias` | Action |
|------------------------|--------|
| `long` | Proceed with long framework if user horizon matches |
| `short_or_avoid` | Short or stand aside |
| `wait_or_reduce_size` | Conflicted — no full-size entry |
| `wait` | No trade until alignment improves |

---

## Example — SOFI-style conflict (illustrative)

| TF | Bias | Note |
|----|------|------|
| Weekly | Neutral | Golden cross but +45% above 200 SMA, declining volume |
| Daily | Neutral | Death cross, below 200 SMA, MACD bullish |
| 4H | Neutral | Rally on low volume |
| 2H | **Bullish** | MA stack bullish — looks like entry |
| 1H | **Bullish** | Support hold |

**Conflicts:** weekly distribution warning, weak rally on multiple TFs, monthly extended.

**Synthesis:** 2H/1H say buy; weekly says exhaustion. → **Risky buy — wait for $17–17.25 hold with weekly RSI cooling, or half size only.**

This is the standard of reasoning required on **every** future analysis regardless of the user's requested horizon.

---

## Workflow checklist

```
MTF Analysis Progress:
- [ ] 1. Run fetch_mtf_analysis.py TICKER --pretty
- [ ] 2. Fill Multi-Timeframe Matrix in response
- [ ] 3. List all conflicts (especially high severity)
- [ ] 4. Write MTF Synthesis (HTF leads, LTF times)
- [ ] 5. Apply conflict penalty to scenario probabilities
- [ ] 6. State trade implication BEFORE execution card
- [ ] 7. Web search for fundamentals (after MTF)
```

---

## Script output fields

| JSON path | Use |
|-----------|-----|
| `timeframes.{monthly,weekly,daily,...}` | Per-TF indicator block |
| `timeframes.*.bias` | bullish/bearish/neutral + reasons |
| `conflicts[]` | Must appear in analysis verbatim |
| `synthesis.verdict` | Overall MTF alignment |
| `synthesis.trade_bias` | long / wait / short_or_avoid |
| `synthesis.weighted_score` | Numeric confluence (-3 to +3 scale approx) |

Single-TF fetch still available via [fetch_chart.py](scripts/fetch_chart.py) for deep dives on one timeframe.
