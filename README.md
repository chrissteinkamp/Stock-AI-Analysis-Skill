# Stock AI Analysis Skill

A Cursor Agent Skill for tactical stock, crypto, and ETF analysis — multi-timeframe technicals, Wyckoff, probability-weighted scenarios, and a persistent learning journal.

## What's included

- **SKILL.md** — Analysis workflow (long / short / wait)
- **Multi-timeframe** — Monthly → 1H with conflict detection
- **Live data** — Yahoo Finance + CoinGecko (no API key required)
- **Learning journal** — Log predictions, review outcomes, calibrate win rates

## Quick start

Copy `.cursor/skills/stock-trading-analysis/` into your project's `.cursor/skills/` folder, or clone this repo into a Cursor workspace.

```bash
# Multi-timeframe analysis
python ".cursor/skills/stock-trading-analysis/scripts/fetch_mtf_analysis.py" SOFI --pretty

# Log + calibrate
python ".cursor/skills/stock-trading-analysis/scripts/trading_journal.py" calibrate
```

## Requirements

- Python 3.10+
- Cursor IDE (for Agent Skills)

Optional: `FINNHUB_API_KEY` for real-time quote cross-check.

## Disclaimer

Not financial advice. For educational and research purposes only.
