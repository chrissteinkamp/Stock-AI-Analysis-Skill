# Stock Trading Analysis — Reference

## Level map template

```text
$[RESISTANCE_3]  ← channel top / 52-wk high / extension
$[RESISTANCE_2]  ← prior high / horizontal resistance
$[RESISTANCE_1]  ← entry fade zone (short) or breakout level (long)
$[CURRENT]       ← current price
$[SUPPORT_1]     ← first support / breakdown trigger
$[SUPPORT_2]     ← major horizontal / weekly low
$[SUPPORT_3]     ← 200 SMA / channel bottom
```

## Scenario probability template (required in every analysis)

**Horizon target default:** For spans **≤3 months**, all T1/T2/T3 and scenario price zones are **peak-in-span** — the high (long) or low (short) **touched at any point** during the window, **not** the expected close on the last day. Label columns accordingly.

```markdown
## Scenario probabilities (estimates)
*Based on pattern context, Wyckoff phase, MA structure, RSI, and historical studies — not guarantees.*
*Targets ≤3mo = **peak potential during span**, not terminal close unless noted.*

### Direction (within [X]-week horizon)
| Scenario | Probability | Peak zone (in span) | Key drivers |
|----------|-------------|---------------------|-------------|
| [Primary thesis plays out] | XX–XX% | $X–$Y peak | [e.g. Wyckoff Phase D + weekly reversal] |
| [Chop / no resolution] | XX–XX% | $X–$Y peak | [e.g. range hold, conflicting daily/weekly] |
| [Invalidation] | XX–XX% | $X trough | [e.g. reclaim $X on volume] |

### Peak target reach (if primary thesis active)
| Target | Peak price (in span) | Est. touch prob. | Horizon | Terminal close note |
|--------|----------------------|------------------|---------|---------------------|
| T1 | $X | XX–XX% | X weeks | [optional: "may fade to $Y by day 30"] |
| T2 | $X | XX–XX% | X weeks | |
| T3 | $X | XX–XX% | X weeks | |

**Peak gain from entry:** +X% to +Y% possible during span
**Confidence:** High / Medium / Low
**Confluence score:** X/10 — [list factors]
```

## Confluence scoring (for probability calibration)

Start at **50%** for primary direction, then adjust:

| Factor | Long | Short |
|--------|------|-------|
| Weekly trend aligned | +8 | +8 |
| Wyckoff phase C/D/E (distrib) or C/D/E (accum) | −10 | +10 |
| Tier 1 candlestick at correct S/R | +8 | +8 |
| Cup & handle breakout confirmed (volume) | +10 | — |
| Ascending triangle breakout confirmed | +8 | — |
| Falling wedge breakout confirmed | +8 | — |
| Rising wedge breakdown confirmed | — | +8 |
| Chart pattern early stalk only (no volume) | +3 | +3 |
| Chart pattern failed / weak breakout | −10 | — |
| Chart pattern failed / weak breakdown | — | −10 |
| RSI divergence aligned | +7 | +7 |
| Golden cross (weekly) | +10 | −10 |
| Death cross (weekly) | −10 | +10 |
| Volume confirms | +5 | +5 |
| Price >25% above 200 SMA | −8 | +8 |
| Stock above analyst consensus | −5 | +5 |
| Monthly RSI >90 | −8 | +8 |
| HTF vs LTF conflict | −10 | −10 |
| MTF high-severity conflict (each) | −10 | −10 |

Cap direction probability **35–75%** unless exceptional confluence (state why if outside).

**Target reach:** T1 closer = higher prob; each subsequent target −10–15%. Wyckoff cause–effect target: use phase resolution rates from [wyckoff.md](wyckoff.md). For horizons **≤3 months**, "reach" = **price touched at any point in span** (peak high / trough low), not close at horizon end.

## Execution card template

```markdown
# [TICKER] — [LONG / SHORT] Execution Card
**Horizon:** [X weeks] | **Type:** [Tactical fade / pullback buy / breakout / breakdown]

## Thesis
[One sentence: price vs fundamentals]

## Wyckoff phase
[Distribution Phase X / Accumulation Phase X / N/A]

## MA structure
[Weekly: golden/death/none | Daily: ... | Price vs 50/200 SMA | Extension % from 200]

## Friday / daily close rule (if applicable)
| Close | Action |
|-------|--------|
| [condition] | [trade / wait / invalidate] |

## Entry
| Style | Zone | Trigger |
|-------|------|---------|
| Preferred | $X – $Y | [rejection / hold / breakdown] |
| Aggressive | $X – $Y | [earlier trigger] |

## Stop
**$X** — [why: above high / below support]

## Targets (scale out)
| Target | Price | Size off | Reach prob. | After hit |
|--------|-------|----------|-------------|-----------|
| T1 | $X | 40% | XX–XX% | Stop → breakeven |
| T2 | $X | 35% | XX–XX% | Trail below prior swing |
| T3 | $X | 25% | XX–XX% | Full exit or trail |

## Position size
Risk: 1% of account
Shares = (Account × 0.01) ÷ (Entry − Stop)

## Invalidation
- [Level / condition] → exit all

## Do not
- [Chase, widen stop, etc.]
```

## Decision tree — short

```text
Weekly reversal at resistance?
  NO  → Wait for setup or re-analyze
  YES → Plan A active

Price bouncing into resistance (daily/4H)?
  YES → Preferred short entry on failure below [LEVEL]
  NO  → Wait for bounce OR breakdown below [SUPPORT]

Close below key support on weekly?
  YES → Plan B (breakdown short) — higher conviction, lower entry
  NO  → Plan A (fade the bounce)

Reclaims resistance on volume?
  YES → INVALIDATE — no short
```

## Decision tree — long

```text
Weekly uptrend intact (higher lows, above 200 SMA)?
  NO  → Reversal long only with strong confirmation at support
  YES → Look for pullback entries

At support (channel / 50 SMA / horizontal)?
  YES → Watch hammer, engulfing, volume capitulation
  NO  → Wait for pullback or breakout retest

Breakout above resistance?
  Close above + volume → long on retest or continuation
  Long wick rejection → wait

Monthly RSI > 90?
  YES → Reduce size; prefer pullback entries over chase
```

## Technical checklist (copy per analysis)

Full MTF matrix template: [multi-timeframe.md](multi-timeframe.md)

```
Monthly:
- [ ] Bias / RSI zone / extension from 200 SMA
- [ ] MACD status / Wyckoff hint
- [ ] Major S/R

Weekly (PRIMARY BIAS):
- [ ] Bias / RSI (>70 = caution)
- [ ] MA stack / cross status
- [ ] Volume trend / price–volume divergence
- [ ] Candlestick + Wyckoff phase
- [ ] Channel position

Daily:
- [ ] Entry triggers / rejection candles
- [ ] 50/200 SMA / MACD / Bollinger
- [ ] Cross vs weekly (conflict?)

3mo / 4H / 2H / 1H:
- [ ] LTF bias vs HTF alignment
- [ ] Entry zone quality
- [ ] Conflicts flagged by script

MTF Synthesis:
- [ ] HTF leads verdict
- [ ] All high-severity conflicts stated
- [ ] Trade implication in plain English
```

## Fundamental + sentiment table

| Category | Bull signal | Bear signal |
|----------|-------------|-------------|
| Valuation | Below consensus, reasonable P/E vs growth | Above consensus, "prices perfection" |
| Analysts | Upgrades, raising targets | Stock above mean target |
| Insiders | Net buying | Net selling into rally |
| Short interest | Declining | Rising |
| Sector | Peer strength confirms | Peer weakness / divergence |
| Narrative | Structural demand shift | Cyclical peak / "this time is different" |

## Synthesis one-liner templates

**Tactical short:**
> [Catalyst] is real, but [METRIC] shows FOMO/overextension — tactical fade toward [TARGET_ZONE], not a bet against [LONG_TERM_THESIS].

**Tactical long:**
> Pullback to [SUPPORT] in intact [TIMEFRAME] uptrend — entry on [TRIGGER], targeting [RESISTANCE].

**Wait:**
> Conflicting signals between [HTF] and [LTF] — stand aside until [LEVEL] breaks or holds.

## Inverse / leveraged ETF notes

| ETF type | Use case | Warning |
|----------|----------|---------|
| 2x inverse daily | Tactical short expression | Daily decay; avoid multi-month hold |
| 2x long daily | Tactical long expression | Decay in sideways markets |
| Standard shares | Cleaner for multi-week holds | Full dollar risk |

SNDQ-style confirmation: inverse ETF at channel support + RSI ~30 + volume climax → underlying may be rolling over.

## Web search queries (adapt per ticker)

- `[TICKER] stock analyst price target consensus`
- `[TICKER] insider buying selling`
- `[TICKER] earnings revenue guidance`
- `[SECTOR] outlook shortage demand [YEAR]`
- `[TICKER] short interest`
- `[TICKER] RSI overbought sentiment`
