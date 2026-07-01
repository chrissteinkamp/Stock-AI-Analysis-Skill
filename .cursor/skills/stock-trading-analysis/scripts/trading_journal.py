#!/usr/bin/env python3
"""Persistent analysis journal — log predictions, review outcomes, calibrate.

Usage:
  python trading_journal.py calibrate          # read before every analysis
  python trading_journal.py log --file entry.json
  python trading_journal.py log --stdin        # pipe JSON
  python trading_journal.py update-outcomes    # score matured entries
  python trading_journal.py pending            # list entries awaiting review
  python trading_journal.py report             # human-readable calibration report
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
JOURNAL_DIR = SCRIPT_DIR.parent / "journal"
ANALYSES_FILE = JOURNAL_DIR / "analyses.jsonl"
CALIBRATION_FILE = JOURNAL_DIR / "calibration.json"

sys.path.insert(0, str(SCRIPT_DIR))
from fetch_chart import http_get, pct_change  # noqa: E402

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_journal() -> None:
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    if not ANALYSES_FILE.exists():
        ANALYSES_FILE.write_text("", encoding="utf-8")


def load_entries() -> list[dict[str, Any]]:
    ensure_journal()
    entries: list[dict[str, Any]] = []
    for line in ANALYSES_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.append(json.loads(line))
    return entries


def save_entries(entries: list[dict[str, Any]]) -> None:
    ensure_journal()
    ANALYSES_FILE.write_text(
        "\n".join(json.dumps(e, separators=(",", ":")) for e in entries) + ("\n" if entries else ""),
        encoding="utf-8",
    )


def append_entry(entry: dict[str, Any]) -> dict[str, Any]:
    entries = load_entries()
    if "id" not in entry:
        entry["id"] = str(uuid.uuid4())
    if "logged_at" not in entry:
        entry["logged_at"] = utc_now()
    entry.setdefault("outcome", None)
    entry.setdefault("status", "pending")
    entries.append(entry)
    save_entries(entries)
    return entry


def parse_horizon_days(horizon: str) -> int:
    h = horizon.lower()
    if "day" in h:
        for token in h.replace("-", " ").split():
            if token.isdigit():
                return int(token)
        return 7
    if "week" in h:
        for token in h.replace("-", " ").split():
            if token.isdigit():
                return int(token) * 7
        return 14
    if "month" in h:
        for token in h.replace("-", " ").split():
            if token.isdigit():
                return int(token) * 30
        return 30
    return 30


def fetch_price(symbol: str) -> float | None:
    import urllib.parse

    url = f"{YAHOO_CHART.format(symbol=urllib.parse.quote(symbol.upper()))}?interval=1d&range=5d"
    try:
        data = http_get(url)
        result = data["chart"]["result"][0]
        meta = result["meta"]
        return float(meta.get("regularMarketPrice") or result["indicators"]["quote"][0]["close"][-1])
    except Exception:
        return None


def score_outcome(entry: dict[str, Any], actual_price: float) -> dict[str, Any]:
    entry_price = entry.get("price_at_analysis")
    verdict = entry.get("verdict", "").lower()
    trade_bias = entry.get("trade_bias", "").lower()
    stop = entry.get("stop")
    targets = entry.get("targets") or []
    direction = entry.get("direction", "long")

    return_pct = pct_change(actual_price, entry_price) if entry_price else None

    hit_stop = False
    if stop is not None and entry_price is not None:
        if direction == "long" and actual_price <= stop:
            hit_stop = True
        elif direction == "short" and actual_price >= stop:
            hit_stop = True

    hit_targets: list[bool] = []
    for t in targets:
        tp = t.get("price") if isinstance(t, dict) else t
        if tp is None:
            hit_targets.append(False)
            continue
        if direction == "long":
            hit_targets.append(actual_price >= tp)
        else:
            hit_targets.append(actual_price <= tp)

    # Verdict correctness heuristic
    verdict_correct: bool | None = None
    if return_pct is not None:
        if "wait" in verdict or "wait" in trade_bias:
            # Wait call correct if move was small or choppy (<5% abs)
            verdict_correct = abs(return_pct) < 5.0
        elif direction == "long" or "long" in verdict:
            verdict_correct = return_pct > 0 and not hit_stop
        elif direction == "short" or "short" in verdict:
            verdict_correct = return_pct < 0 and not hit_stop
        elif "bearish" in verdict or "fade" in verdict:
            verdict_correct = return_pct < 2.0

    primary_target = targets[0].get("price") if targets and isinstance(targets[0], dict) else None
    direction_correct: bool | None = None
    if return_pct is not None and primary_target and entry_price:
        expected_up = primary_target > entry_price
        direction_correct = (return_pct > 0) == expected_up

    return {
        "reviewed_at": utc_now(),
        "actual_price": round(actual_price, 4),
        "return_pct": round(return_pct, 2) if return_pct is not None else None,
        "hit_stop": hit_stop,
        "hit_targets": hit_targets,
        "hit_primary_target": hit_targets[0] if hit_targets else None,
        "verdict_correct": verdict_correct,
        "direction_correct": direction_correct,
    }


def update_outcomes(force: bool = False) -> list[dict[str, Any]]:
    entries = load_entries()
    updated: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    for entry in entries:
        if entry.get("outcome") and not force:
            continue
        horizon_days = entry.get("horizon_days") or parse_horizon_days(entry.get("horizon", "30 days"))
        logged = datetime.fromisoformat(entry["logged_at"].replace("Z", "+00:00"))
        if now < logged + timedelta(days=horizon_days) and not force:
            entry["status"] = "pending"
            continue

        symbol = entry.get("symbol", "")
        price = fetch_price(symbol)
        if price is None:
            entry["status"] = "review_failed"
            continue

        entry["outcome"] = score_outcome(entry, price)
        entry["status"] = "reviewed"
        updated.append(entry)

    save_entries(entries)
    return updated


def bucket_stats(items: list[dict[str, Any]], key_fn) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        k = key_fn(item)
        buckets.setdefault(k, []).append(item)

    out: dict[str, Any] = {}
    for k, group in buckets.items():
        reviewed = [g for g in group if g.get("outcome")]
        if not reviewed:
            out[k] = {"n": len(group), "reviewed": 0}
            continue
        wins = sum(1 for g in reviewed if g["outcome"].get("verdict_correct"))
        dir_wins = sum(1 for g in reviewed if g["outcome"].get("direction_correct"))
        returns = [g["outcome"]["return_pct"] for g in reviewed if g["outcome"].get("return_pct") is not None]
        out[k] = {
            "n": len(group),
            "reviewed": len(reviewed),
            "verdict_win_rate": round(wins / len(reviewed) * 100, 1) if reviewed else None,
            "direction_win_rate": round(dir_wins / len(reviewed) * 100, 1) if reviewed else None,
            "avg_return_pct": round(sum(returns) / len(returns), 2) if returns else None,
        }
    return out


def compute_calibration() -> dict[str, Any]:
    entries = load_entries()
    reviewed = [e for e in entries if e.get("outcome")]
    pending = [e for e in entries if e.get("status") == "pending"]

    overall_wins = sum(1 for e in reviewed if e["outcome"].get("verdict_correct"))
    overall_n = len(reviewed)

    calibration: dict[str, Any] = {
        "generated_at": utc_now(),
        "total_logged": len(entries),
        "pending_review": len(pending),
        "reviewed": overall_n,
        "overall_verdict_win_rate": round(overall_wins / overall_n * 100, 1) if overall_n else None,
        "by_trade_bias": bucket_stats(entries, lambda e: e.get("trade_bias", "unknown")),
        "by_mtf_verdict": bucket_stats(entries, lambda e: e.get("mtf_verdict", "unknown")),
        "by_mtf_alignment": bucket_stats(entries, lambda e: e.get("mtf_alignment", "unknown")),
        "by_direction": bucket_stats(entries, lambda e: e.get("direction", "unknown")),
        "by_asset_type": bucket_stats(entries, lambda e: e.get("asset_type", "stock")),
        "by_setup_tag": {},
        "probability_adjustments": [],
        "lessons": [],
    }

    # Tag-level stats
    tag_groups: dict[str, list[dict[str, Any]]] = {}
    for e in entries:
        for tag in e.get("setup_tags") or []:
            tag_groups.setdefault(tag, []).append(e)
    for tag, group in tag_groups.items():
        calibration["by_setup_tag"][tag] = bucket_stats(group, lambda _: tag)[tag]

    # High-severity conflict stats
    conflict_entries = [e for e in entries if (e.get("mtf_conflicts_high") or 0) > 0]
    no_conflict = [e for e in entries if (e.get("mtf_conflicts_high") or 0) == 0]
    calibration["htf_ltf_conflict_present"] = bucket_stats(conflict_entries, lambda _: "yes")
    calibration["htf_ltf_conflict_absent"] = bucket_stats(no_conflict, lambda _: "no")

    # Generate probability adjustments for agent
    adj: list[dict[str, Any]] = []
    for label, stats in calibration["by_mtf_alignment"].items():
        if isinstance(stats, dict) and stats.get("reviewed", 0) >= 3 and stats.get("verdict_win_rate") is not None:
            wr = stats["verdict_win_rate"]
            if wr < 45:
                adj.append({"condition": f"mtf_alignment={label}", "adjustment_pct": -10, "reason": f"historical win rate {wr}%"})
            elif wr > 60:
                adj.append({"condition": f"mtf_alignment={label}", "adjustment_pct": +5, "reason": f"historical win rate {wr}%"})

    for tag, stats in calibration["by_setup_tag"].items():
        if isinstance(stats, dict) and stats.get("reviewed", 0) >= 3 and stats.get("verdict_win_rate") is not None:
            wr = stats["verdict_win_rate"]
            if wr < 40:
                adj.append({"condition": f"setup_tag={tag}", "adjustment_pct": -8, "reason": f"tag win rate {wr}% (n={stats['reviewed']})"})
            elif wr > 65:
                adj.append({"condition": f"setup_tag={tag}", "adjustment_pct": +5, "reason": f"tag win rate {wr}% (n={stats['reviewed']})"})

    calibration["probability_adjustments"] = adj

    # Lessons (auto-generated insights)
    lessons: list[str] = []
    if overall_n >= 5:
        wr = calibration["overall_verdict_win_rate"]
        lessons.append(f"Overall tracked verdict win rate: {wr}% over {overall_n} reviewed analyses.")
    conf_yes = calibration.get("htf_ltf_conflict_present", {}).get("yes", {})
    conf_no = calibration.get("htf_ltf_conflict_absent", {}).get("no", {})
    if conf_yes.get("reviewed", 0) >= 3 and conf_no.get("reviewed", 0) >= 3:
        lessons.append(
            f"MTF conflict trades: {conf_yes.get('verdict_win_rate')}% win rate vs "
            f"aligned: {conf_no.get('verdict_win_rate')}% — prefer aligned setups."
        )
    wait_stats = calibration["by_trade_bias"].get("wait", {}) or calibration["by_trade_bias"].get("wait_or_reduce_size", {})
    if wait_stats.get("reviewed", 0) >= 3:
        lessons.append(f"'Wait' calls validated {wait_stats.get('verdict_win_rate')}% of the time — honor conflict flags.")

    if overall_n < 10:
        lessons.append(
            f"Calibration immature (n={overall_n}). Need 20+ reviewed outcomes before adjusting base rates aggressively."
        )
    lessons.append(
        "Win rate != edge. Track expectancy: avg win x win% - avg loss x loss%. Hedge funds target asymmetric R:R, not 90% wins."
    )
    calibration["lessons"] = lessons

    CALIBRATION_FILE.write_text(json.dumps(calibration, indent=2), encoding="utf-8")
    return calibration


def cmd_log(args: argparse.Namespace) -> int:
    if args.stdin:
        payload = json.load(sys.stdin)
    elif args.file:
        payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
    else:
        print("Provide --file or --stdin", file=sys.stderr)
        return 1
    if isinstance(payload, list):
        for item in payload:
            append_entry(item)
    else:
        append_entry(payload)
    compute_calibration()
    print(json.dumps({"status": "logged", "journal": str(ANALYSES_FILE)}))
    return 0


def cmd_calibrate(_: argparse.Namespace) -> int:
    cal = compute_calibration()
    print(json.dumps(cal, indent=2))
    return 0


def cmd_report(_: argparse.Namespace) -> int:
    cal = compute_calibration() if not CALIBRATION_FILE.exists() else json.loads(CALIBRATION_FILE.read_text())
    print("# Trading Journal Calibration Report")
    print(f"Generated: {cal.get('generated_at', 'n/a')}")
    print(f"Total logged: {cal.get('total_logged', 0)} | Reviewed: {cal.get('reviewed', 0)} | Pending: {cal.get('pending_review', 0)}")
    print(f"Overall verdict win rate: {cal.get('overall_verdict_win_rate', 'n/a')}%")
    print("\n## Lessons")
    for lesson in cal.get("lessons", []):
        print(f"- {lesson}")
    print("\n## Probability adjustments (apply when conditions match)")
    for adj in cal.get("probability_adjustments", []):
        print(f"- {adj['condition']}: {adj['adjustment_pct']:+d}% ({adj['reason']})")
    return 0


def cmd_pending(_: argparse.Namespace) -> int:
    entries = load_entries()
    pending = [e for e in entries if e.get("status") == "pending"]
    print(json.dumps(pending, indent=2))
    return 0


def cmd_update(_: argparse.Namespace) -> int:
    updated = update_outcomes(force=_.force)
    cal = compute_calibration()
    print(json.dumps({"updated": len(updated), "calibration": cal.get("overall_verdict_win_rate")}, indent=2))
    return 0


def cmd_seed(_: argparse.Namespace) -> int:
    """Seed journal with analyses from initial session (run once)."""
    if ANALYSES_FILE.exists() and ANALYSES_FILE.read_text().strip():
        print("Journal already has entries; skip seed or delete journal/analyses.jsonl first.")
        return 0

    seeds = [
        {
            "symbol": "BTC-USD",
            "asset_type": "crypto",
            "horizon": "6 days",
            "horizon_days": 6,
            "direction": "long",
            "verdict": "mild relief bounce",
            "trade_bias": "wait",
            "mtf_verdict": "mixed_neutral",
            "mtf_alignment": "conflicted",
            "mtf_conflicts_high": 0,
            "price_at_analysis": 58550,
            "targets": [{"price": 60500, "prob": 0.55}, {"price": 61500, "prob": 0.32}],
            "stop": 57650,
            "confidence": "low-medium",
            "confluence_score": 5,
            "setup_tags": ["oversold_daily", "below_200sma", "death_cross_weekly"],
            "notes": "Base case $60-61 by July 6",
            "logged_at": "2026-06-30T23:50:00Z",
        },
        {
            "symbol": "IREN",
            "asset_type": "stock",
            "horizon": "14 days",
            "horizon_days": 14,
            "direction": "long",
            "verdict": "wait",
            "trade_bias": "wait_or_reduce_size",
            "mtf_verdict": "mixed_neutral",
            "mtf_alignment": "conflicted",
            "mtf_conflicts_high": 1,
            "price_at_analysis": 45.73,
            "targets": [{"price": 47.5, "prob": 0.45}, {"price": 51.0, "prob": 0.28}],
            "stop": 43.75,
            "confidence": "low-medium",
            "confluence_score": 4,
            "setup_tags": ["below_200sma", "death_cross_daily", "support_test"],
            "notes": "Base ~$47 by July 14",
            "logged_at": "2026-06-30T23:55:00Z",
        },
        {
            "symbol": "SOFI",
            "asset_type": "stock",
            "horizon": "30 days",
            "horizon_days": 30,
            "direction": "long",
            "verdict": "cautious long",
            "trade_bias": "wait_or_reduce_size",
            "mtf_verdict": "mixed_neutral",
            "mtf_alignment": "conflicted",
            "mtf_conflicts_high": 1,
            "price_at_analysis": 17.93,
            "targets": [{"price": 19.25, "prob": 0.52}, {"price": 21.5, "prob": 0.32}],
            "stop": 16.45,
            "confidence": "medium",
            "confluence_score": 6,
            "setup_tags": ["death_cross_daily", "accumulation_weekly", "earnings_catalyst"],
            "notes": "Earnings July 28; half size",
            "logged_at": "2026-07-01T00:35:00Z",
        },
        {
            "symbol": "DAVE",
            "asset_type": "stock",
            "horizon": "30 days",
            "horizon_days": 30,
            "direction": "long",
            "verdict": "wait",
            "trade_bias": "wait",
            "mtf_verdict": "bullish_but_conflicted",
            "mtf_alignment": "conflicted",
            "mtf_conflicts_high": 2,
            "price_at_analysis": 372.59,
            "targets": [{"price": 365, "prob": 0.40}, {"price": 340, "prob": 0.30}],
            "stop": 348,
            "confidence": "medium",
            "confluence_score": 4,
            "setup_tags": ["overbought_rsi", "extended_200sma", "ath_volume_divergence"],
            "notes": "Most likely end-July $365; do not chase",
            "logged_at": "2026-07-01T00:40:00Z",
        },
    ]
    for s in seeds:
        append_entry(s)
    compute_calibration()
    print(json.dumps({"seeded": len(seeds)}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Trading analysis journal")
    sub = parser.add_subparsers(dest="cmd")

    p_log = sub.add_parser("log", help="Append analysis entry")
    p_log.add_argument("--file", help="JSON file with entry or list")
    p_log.add_argument("--stdin", action="store_true")
    p_log.set_defaults(func=cmd_log)

    p_cal = sub.add_parser("calibrate", help="Compute calibration stats (run before analysis)")
    p_cal.set_defaults(func=cmd_calibrate)

    p_rep = sub.add_parser("report", help="Human-readable calibration report")
    p_rep.set_defaults(func=cmd_report)

    p_pen = sub.add_parser("pending", help="List pending outcomes")
    p_pen.set_defaults(func=cmd_pending)

    p_up = sub.add_parser("update-outcomes", help="Score matured entries")
    p_up.add_argument("--force", action="store_true")
    p_up.set_defaults(func=cmd_update)

    p_seed = sub.add_parser("seed", help="Seed initial session analyses")
    p_seed.set_defaults(func=cmd_seed)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
