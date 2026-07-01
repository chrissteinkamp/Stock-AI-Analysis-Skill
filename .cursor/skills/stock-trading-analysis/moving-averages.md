# Moving Averages — 50/200 SMA, Golden Cross, Death Cross

**Default SMAs:** 50-period and 200-period unless user specifies EMA.

**Critical:** Crosses are **lagging** — they confirm regimes already underway, not predict turns ([Investopedia](https://www.investopedia.com/terms/g/goldencross.asp)). Reliability varies by **timeframe** and **asset** (indices > individual volatile stocks).

---

## Definitions

| Signal | Condition | Interpretation |
|--------|-----------|----------------|
| **Golden Cross** | 50 SMA crosses **above** 200 SMA | Bullish regime shift |
| **Death Cross** | 50 SMA crosses **below** 200 SMA | Bearish regime shift |
| **Price > 50 > 200** | Bullish stack | Strong uptrend |
| **Price < 50 < 200** | Bearish stack | Strong downtrend |
| **Extension** | Price >20–30% above 200 SMA | Mean-reversion risk increases |

Confirm with **volume expansion** on cross when possible.

---

## Timeframe matrix (use in every analysis)

| Timeframe | 50/200 cross meaning | Whipsaw risk | Best use |
|-----------|---------------------|--------------|----------|
| **Daily** | Classic golden/death cross; swing to position trades | **High** on volatile stocks | Trend filter; 2–8 week tactical trades |
| **Weekly** | Major trend change; fewer signals | **Medium** | **Primary** bias for swing trades |
| **Monthly** | Macro regime (bull/bear years) | **Low** (very lagging) | Long-term context; extension gauge |
| **4H / 1H** | Short-term momentum shifts | **Very high** | Entry timing only — never sole signal |

**Rule:** Higher TF cross **overrides** lower TF for bias. Daily death cross inside weekly golden cross = pullback, not necessarily bear market.

---

## S&P 500 historical stats (1960–present)

Source: [QuantifiedStrategies golden/death cross backtests](https://www.quantifiedstrategies.com/do-moving-average-crossovers-really-predict-price-direction/)

| Signal | Finding |
|--------|---------|
| **Golden Cross → hold until Death Cross** | Average gain **~16%** per bull regime |
| **Golden Cross strategy CAGR** | **~7%** vs buy-and-hold; **~30% less** time in market, lower drawdowns |
| **Death Cross (short-term)** | Underperforms random for **<30 days** |
| **Death Cross (defensive exit)** | Reduces max drawdown; "plays defense" — **~0.4% CAGR** if shorting |
| **False signals** | Common in **sideways/choppy** markets |

**Individual stocks:** Expect **more whipsaws** and **lower hit rates** than SPY — especially high-beta (beta >2). Discount cross reliability **~10–15%** vs index for parabolic names.

---

## Trading rules by scenario

### Bull case (long)

| Setup | Action | Est. edge |
|-------|--------|-----------|
| Weekly golden cross + price above both SMAs | Bullish bias; buy pullbacks to **50 SMA** | Regime favorable **~60–65%** over 3–6 months |
| Daily golden cross, weekly still bullish | Tactical long on pullback | **~55–60%** |
| Price at **50 SMA** in golden-cross regime | "Buy the dip" zone | **~55–65%** if hold + volume |
| Price extended **>25% above 200 SMA** | Reduce size; wait for pullback | Mean-reversion risk **~50–60%** within 8 weeks |

### Bear case (short)

| Setup | Action | Est. edge |
|-------|--------|-----------|
| Weekly death cross | Bearish regime; favor shorts on rallies to **50 SMA** | **~55–60%** over 3–6 months |
| Price below 50 & 200; death cross recent | Rally-fade shorts | **~55–60%** |
| Daily death cross, weekly still golden | **Caution** — likely pullback not reversal | Short edge drops to **~45–50%** |
| Price rejects **50 SMA** from below (now resistance) | LPSY-style MA rejection short | **~55–65%** with volume |

### Extension + cross conflict

| State | Read |
|-------|------|
| Golden cross + monthly RSI >90 | Bullish regime but **exhaustion** — tactical short/fade possible despite MA bull stack |
| Death cross + RSI oversold | Bearish regime but **bounce risk** — don't chase short into climax |
| Golden cross just formed after parabolic move | **Late** — edge diminished; prior move may be priced in |

---

## SMA as dynamic S/R

| Level | Support (uptrend) | Resistance (downtrend) |
|-------|-------------------|------------------------|
| **50 SMA** | First pullback buy zone | First rally fade zone |
| **200 SMA** | Major trend line; last defense | Major overhead resistance |
| **Both** | Confluence strengthens level **+5–10%** hold probability |

---

## Probability adjustments for MA structure

Add to scenario output when MAs align with trade direction:

| MA confluence | Long thesis boost | Short thesis boost |
|---------------|-------------------|-------------------|
| Weekly golden cross + price > 50 SMA | **+10%** | **−15%** (fighting trend) |
| Weekly death cross + price < 50 SMA | **−15%** | **+10%** |
| Price extended >25% above 200 SMA | **−10%** long | **+10%** short (mean reversion) |
| 50 SMA flattening after golden cross | Neutral — trend maturing | Watch for distribution |
| Daily cross contradicts weekly | **−10%** on trade following daily only | Same |

---

## Output requirement

In every analysis, state:
1. **50 SMA** value and price relationship
2. **200 SMA** value and price relationship
3. **Stack order** (bullish / bearish / mixed)
4. **Recent cross** — golden or death, on which timeframe, how many bars ago
5. **Extension** — % distance from 200 SMA if parabolic
