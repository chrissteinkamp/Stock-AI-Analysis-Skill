# Learning Loop — Analysis Journal & Calibration

Every analysis is **logged**, **reviewed against outcomes**, and used to **calibrate** future probability estimates. This is how the skill improves over time — not via model memory, but via **persistent tracked data** in this repo.

**Honest expectation:** No system guarantees hedge-fund win rates. Top funds often run **50–58%** win rates with **asymmetric risk/reward** (small losses, large wins). This journal tracks **verdict accuracy**, **direction**, and **setup tags** to sharpen *your stated probabilities* and *wait/long/short decisions* — the path to professional-grade discipline.

---

## How learning works

```text
BEFORE analysis          DURING analysis           AFTER analysis
─────────────────        ─────────────────         ────────────────
1. update-outcomes       1. fetch_mtf_analysis     1. log entry via
2. calibrate               2. apply calibration        trading_journal.py
   (read adjustments)        adjustments to probs    2. include setup_tags
3. read lessons          3. prefer aligned MTF     3. user can ask
                                                      "review outcomes"
```

The agent has **no cross-session memory** unless it reads `journal/calibration.json`. The journal **is** the memory.

---

## Commands

```bash
# BEFORE every analysis
python ".cursor/skills/stock-trading-analysis/scripts/trading_journal.py" update-outcomes
python ".cursor/skills/stock-trading-analysis/scripts/trading_journal.py" calibrate

# AFTER every analysis (required)
python ".cursor/skills/stock-trading-analysis/scripts/trading_journal.py" log --file entry.json

# Human-readable report
python ".cursor/skills/stock-trading-analysis/scripts/trading_journal.py" report

# List analyses awaiting horizon maturity
python ".cursor/skills/stock-trading-analysis/scripts/trading_journal.py" pending
```

---

## What gets logged (required fields)

| Field | Example | Purpose |
|-------|---------|---------|
| `symbol` | `SOFI` | Ticker |
| `asset_type` | `stock` / `crypto` / `etf` | Bucket stats |
| `horizon` | `30 days` | When to review outcome |
| `direction` | `long` / `short` / `neutral` | Score direction |
| `verdict` | `cautious long` | One-line call |
| `trade_bias` | `wait_or_reduce_size` | From MTF synthesis |
| `mtf_verdict` | `mixed_neutral` | From script |
| `mtf_alignment` | `aligned` / `conflicted` | Critical for learning |
| `mtf_conflicts_high` | `1` | HTF/LTF conflict count |
| `price_at_analysis` | `17.93` | Entry reference |
| `targets` | `[{"price": 19.25, "prob": 0.52}]` | **Peak-in-span** levels (≤3mo): highest/lowest expected **touched** during horizon — not terminal close |
| `stop` | `16.45` | Stop-hit tracking |
| `confidence` | `medium` | vs actual |
| `confluence_score` | `6` | 1–10 |
| `setup_tags` | see below | Pattern learning |

### Standard setup_tags (use 3–8 per analysis)

**Trend / MA:** `golden_cross_weekly`, `death_cross_daily`, `below_200sma`, `extended_200sma`, `bullish_ma_stack`, `bearish_ma_stack`

**Momentum:** `overbought_rsi`, `oversold_rsi`, `rsi_divergence_bearish`, `rsi_divergence_bullish`

**Volume / Wyckoff:** `distribution_warning`, `accumulation_possible`, `rally_low_volume`, `volume_confirmation`

**MTF:** `htf_ltf_conflict`, `mtf_aligned_bullish`, `mtf_aligned_bearish`

**Context:** `earnings_catalyst`, `ath_test`, `support_test`, `resistance_fade`, `parabolic_move`

**Chart patterns:** `cup_and_handle_forming`, `cup_and_handle_ready`, `cup_and_handle_breakout`, `cup_and_handle_failed`, `ascending_triangle_forming`, `ascending_triangle_apex`, `ascending_triangle_breakout`, `ascending_triangle_failed`, `falling_wedge_forming`, `falling_wedge_apex`, `falling_wedge_breakout`, `falling_wedge_failed`, `rising_wedge_forming`, `rising_wedge_apex`, `rising_wedge_breakdown`, `rising_wedge_failed`

**Fundamental:** `above_analyst_targets`, `below_analyst_targets`, `insider_buying`

---

## Log entry template

Save as temp file or pipe JSON:

```json
{
  "symbol": "SOFI",
  "asset_type": "stock",
  "horizon": "30 days",
  "direction": "long",
  "verdict": "cautious long",
  "trade_bias": "wait_or_reduce_size",
  "mtf_verdict": "mixed_neutral",
  "mtf_alignment": "conflicted",
  "mtf_conflicts_high": 1,
  "price_at_analysis": 17.93,
  "targets": [
    {"price": 19.25, "prob": 0.52, "label": "T1", "type": "peak_in_span"},
    {"price": 21.50, "prob": 0.32, "label": "T2", "type": "peak_in_span"}
  ],
  "stop": 16.45,
  "confidence": "medium",
  "confluence_score": 6,
  "setup_tags": ["death_cross_daily", "accumulation_weekly", "htf_ltf_conflict", "earnings_catalyst"],
  "notes": "Half size due to Jul 28 earnings. Peak $21 possible; terminal close est. $18–19."
}
```

```bash
python ".cursor/skills/stock-trading-analysis/scripts/trading_journal.py" log --file entry.json
```

---

## Applying calibration to new analyses

After `calibrate`, read `journal/calibration.json`:

1. **`probability_adjustments`** — apply to scenario probabilities when conditions match (e.g. −10% when `mtf_alignment=conflicted` if historical win rate < 45%).

2. **`lessons`** — cite in analysis when relevant (*"Historical journal: conflicted MTF setups won 38% vs aligned 62% — reducing long conviction"*).

3. **`by_setup_tag`** — if a tag has n≥3 and win rate < 40%, **downgrade** that setup; if > 65%, **upgrade cautiously**.

4. **Immature calibration (n < 20 reviewed)** — use adjustments lightly; rely on framework defaults from [reference.md](reference.md).

### Calibration maturity levels

| Reviewed outcomes | Action |
|-------------------|--------|
| 0–9 | Log only; use default confluence table |
| 10–19 | Apply adjustments ±5% max |
| 20–49 | Apply full adjustments; start tag-level learning |
| 50+ | Tag-level required; report win rate by setup in every analysis |

---

## Outcome scoring

When horizon matures, `update-outcomes` fetches live price and scores:

| Metric | Meaning |
|--------|---------|
| `verdict_correct` | Did the call (long/short/wait) play out? |
| `direction_correct` | Did price move toward primary target direction? |
| `hit_stop` | Stop level breached? |
| `hit_targets` | Which targets reached? |
| `return_pct` | Return from `price_at_analysis` |

**Wait calls** scored correct if |return| < 5% (chop/small move — standing aside was right).

---

## What "hedge fund level" means here

| Myth | Reality |
|------|---------|
| 90% win rate | Unrealistic; 55% with 2:1 R:R is excellent |
| AI remembers past chats | Only this journal persists — must log every time |
| More indicators = higher wins | **Alignment + discipline + calibrated probabilities** |
| Always be in a trade | **Wait** is often the highest-expectancy call |

**Target for this system:** Improve **calibration** (when you say 60%, it happens ~60% of the time) and **filter bad trades** (conflicted MTF, low-volume rallies) — not predict every move.

---

## Workflow checklist (added to every analysis)

```
Learning Loop:
- [ ] Run update-outcomes + calibrate BEFORE analysis
- [ ] Read calibration.json adjustments and lessons
- [ ] Apply adjustments to scenario probabilities
- [ ] After delivering analysis, log entry with setup_tags
- [ ] Mention journal maturity (n reviewed) when citing historical win rates
```

---

## Files

| Path | Purpose |
|------|---------|
| `journal/analyses.jsonl` | Append-only log (one JSON per line) |
| `journal/calibration.json` | Computed stats (regenerated by calibrate) |
| `scripts/trading_journal.py` | Log, review, calibrate CLI |

**Do not delete** `analyses.jsonl` — it is the learning dataset. Commit to git if you want history across machines.

---

## Example learning narrative (future analyses)

> *"MTF synthesis: 2H bullish but weekly overbought + declining volume. Journal shows `htf_ltf_conflict` setups (n=12) won 42% vs aligned 61%. Applying −10% to long scenario. **Verdict: wait** — not a risky buy despite 4H entry."*

This is the standard going forward.
