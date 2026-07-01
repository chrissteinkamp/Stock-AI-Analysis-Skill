# Candlestick Patterns — Context, Reliability, and Stats

Patterns are **not standalone signals**. Reliability rises sharply with: correct trend context, volume confirmation, RSI/MFI filter, and higher-timeframe alignment. Academic studies are mixed ([Marshall, Young & Rose 2006](https://www.scribd.com/document/232577907/Marshall-Young-Rose-2006) found no edge on DJIA; [QuantifiedStrategies SPY backtests](https://www.quantifiedstrategies.com/candlestick-patterns-ranked-by-backtest/) found conditional edge with defined holds).

**Always state:** pattern name + location (support/resistance) + timeframe + trend context.

---

## Reliability tiers (with trend + volume filter)

Use these tiers when assigning probability boosts in analysis. Raw stats below are mostly **SPY 1993–present** or cited studies — individual stocks deviate.

### Tier 1 — Highest conviction (when at correct location)

| Pattern | Direction | Context required | Historical edge (benchmark) |
|---------|-----------|------------------|----------------------------|
| **Bearish Engulfing** | Bearish at resistance | After extended rally; volume on engulf candle | Win rate **55% → 70%+** over 5–17 days ([QS](https://www.quantifiedstrategies.com/candlestick-patterns-ranked-by-backtest/)); stronger as **bullish mean-reversion** on index without trend filter |
| **Dark Cloud Cover** | Bearish | Uptrend, at resistance; 2nd candle closes below midpoint of 1st | Win rate up to **~71.5%** at 19-day hold (QS SPY backtest) |
| **Three Inside Up** | Bullish | Downtrend exhaustion at support | Profit factor **~2.5**; ~2× market return over 20-day hold (QS) |
| **Three Outside Down** | Bearish | After extended rally | High-conviction 3-candle reversal (QS top-10) |
| **Hammer** | Bullish | After decline, at support | Forex study: hammer + hanging man with RSI showed significant edge ([academia.edu forex study](https://www.academia.edu/66112659)) |
| **Hanging Man / Shooting Star** | Bearish | After rally, at resistance | Same family as hammer; context flips meaning |

### Tier 2 — Strong with confirmation

| Pattern | Direction | Notes |
|---------|-----------|-------|
| **Bullish Engulfing** | Bullish at support | Mirror of bearish engulfing; confirm with close above prior high |
| **Morning Star** | Bullish | 3-candle bottom reversal; gap preferred but not required on stocks |
| **Evening Star** | Bearish | 3-candle top reversal |
| **Piercing Line** | Bullish | 2nd candle closes >50% into prior bearish body; weak short-term, better 15–20 days (QS) |
| **Bullish Harami** | Bullish | Frequent signal; slight short-term edge only (QS) |
| **Bearish Harami** | Bearish | Inside bar after rally; needs resistance context |
| **Tweezer Top / Bottom** | Reversal | Equal highs/lows at S/R; stronger with volume divergence |

### Tier 3 — Continuation / indecision (need trend context)

| Pattern | Use |
|---------|-----|
| **Bullish Marubozu** | Strong momentum continuation **in existing uptrend** |
| **Bearish Marubozu** | Strong momentum continuation **in existing downtrend** |
| **Doji / Long-legged Doji** | Indecision; reversal only at extremes with volume climax |
| **Spinning Top** | Weak indecision; wait for next candle |

---

## Single-candle quick reference

| Candle | Body | Wick | At support | At resistance |
|--------|------|------|------------|---------------|
| **Hammer** | Small, top | Long lower | Bullish reversal | N/A (would be hanging man) |
| **Hanging Man** | Small, top | Long lower | — | Bearish warning |
| **Inverted Hammer** | Small, bottom | Long upper | Bullish (needs confirm) | — |
| **Shooting Star** | Small, bottom | Long upper | — | Bearish rejection |
| **Dragonfly Doji** | Open ≈ close at high | Long lower | Bullish at support | Hanging man variant at top |
| **Gravestone Doji** | Open ≈ close at low | Long upper | — | Bearish at resistance |

---

## Multi-candle reversal checklist

**Bullish reversal (long):**
1. Prior downtrend or pullback in uptrend
2. Pattern at support (horizontal, channel, 50 SMA)
3. Volume higher on reversal candle(s)
4. RSI oversold or bullish divergence
5. Next candle confirms (close above pattern high)

**Bearish reversal (short):**
1. Prior extended rally
2. Pattern at resistance (channel top, prior high)
3. Volume on rejection candle
4. RSI overbought or bearish divergence
5. Next candle confirms (close below pattern low)

---

## Probability adjustment from candlesticks

When assigning scenario probabilities in output, adjust base rates:

| Confluence | Adjustment to pattern success estimate |
|------------|----------------------------------------|
| Pattern at correct S/R + HTF agrees | **+10–15%** vs base |
| Volume confirms (climax or expansion) | **+5–10%** |
| RSI divergence aligned | **+5–10%** |
| Pattern against HTF trend | **−15–25%** |
| No volume confirmation | **−10%** |
| Choppy range (no clear trend) | **−10–15%** |

**Base rate guidance (tactical 2–8 week holds, filtered):**
- Tier 1 pattern, full confluence: pattern "works" **~60–70%** (direction correct)
- Tier 2, partial confluence: **~50–60%**
- Tier 3 or mislocated pattern: **~40–50%** (near coin flip — prefer wait)

*These are estimates for analysis output, not guaranteed odds.*
