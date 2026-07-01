"""Chart pattern detection: cup & handle, ascending triangle, falling/rising wedges."""

from __future__ import annotations

from typing import Any


def _avg_volume(bars: list[dict[str, Any]], start: int, end: int) -> float | None:
    vols = [float(b["volume"] or 0) for b in bars[start:end] if b.get("volume")]
    return sum(vols) / len(vols) if vols else None


def _chunk_extremes(
    highs: list[float], lows: list[float], chunks: int = 10
) -> tuple[list[tuple[int, float]], list[tuple[int, float]]]:
    """Rolling chunk max/min — works on smooth trends where bar-by-bar swings fail."""
    n = len(highs)
    if n < chunks * 3:
        return [], []
    size = n // chunks
    chunk_highs: list[tuple[int, float]] = []
    chunk_lows: list[tuple[int, float]] = []
    for c in range(chunks):
        start = c * size
        end = n if c == chunks - 1 else start + size
        seg_h = highs[start:end]
        seg_l = lows[start:end]
        idx = end - 1
        chunk_highs.append((idx, max(seg_h)))
        chunk_lows.append((idx, min(seg_l)))
    return chunk_highs, chunk_lows


def _swing_points(
    highs: list[float], lows: list[float], radius: int = 2
) -> tuple[list[tuple[int, float]], list[tuple[int, float]]]:
    swing_highs: list[tuple[int, float]] = []
    swing_lows: list[tuple[int, float]] = []
    for i in range(radius, len(highs) - radius):
        h_seg = highs[i - radius : i + radius + 1]
        l_seg = lows[i - radius : i + radius + 1]
        if highs[i] == max(h_seg):
            swing_highs.append((i, highs[i]))
        if lows[i] == min(l_seg):
            swing_lows.append((i, lows[i]))
    return swing_highs, swing_lows


def _line_slope(points: list[tuple[int, float]]) -> float | None:
    if len(points) < 2:
        return None
    x0, y0 = points[0]
    x1, y1 = points[-1]
    if x1 == x0:
        return None
    return (y1 - y0) / (x1 - x0)


def _project_line(points: list[tuple[int, float]], at_index: int) -> float | None:
    if len(points) < 2:
        return None
    x0, y0 = points[0]
    x1, y1 = points[-1]
    if x1 == x0:
        return y1
    slope = (y1 - y0) / (x1 - x0)
    return y0 + slope * (at_index - x0)


def detect_falling_wedge(bars: list[dict[str, Any]], timeframe: str) -> dict[str, Any] | None:
    """Falling wedge — bullish bias; breaks upward ([StockCharts](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/falling-wedge))."""
    min_bars = 25 if timeframe == "weekly" else 30
    if len(bars) < min_bars:
        return None

    window = bars[-min(len(bars), 70 if timeframe == "daily" else 45) :]
    wn = len(window)
    if wn < min_bars:
        return None

    highs = [b["high"] for b in window]
    lows = [b["low"] for b in window]
    closes = [b["close"] for b in window]
    swing_highs, swing_lows = _chunk_extremes(highs, lows, chunks=10)
    if len(swing_highs) < 3 or len(swing_lows) < 3:
        return None

    # Lower highs and lower lows (both trendlines slope down)
    hh_declining = swing_highs[0][1] > swing_highs[-1][1] * 1.01
    ll_declining = swing_lows[0][1] > swing_lows[-1][1] * 1.01
    if not (hh_declining and ll_declining):
        return None

    upper_slope = _line_slope(swing_highs)
    lower_slope = _line_slope(swing_lows)
    if upper_slope is None or lower_slope is None:
        return None
    # Upper falls faster (more negative) than lower — converging down-sloping wedge
    if upper_slope >= lower_slope or upper_slope >= 0 or lower_slope >= 0:
        return None

    first_range = swing_highs[0][1] - swing_lows[0][1]
    last_range = swing_highs[-1][1] - swing_lows[-1][1]
    if first_range <= 0 or last_range >= first_range * 0.85:
        return None

    resistance = _project_line(swing_highs, wn - 1)
    support = _project_line(swing_lows, wn - 1)
    if resistance is None or support is None:
        return None

    half = wn // 2
    vol_first = _avg_volume(window, 0, half)
    vol_second = _avg_volume(window, half, wn)
    vol_contracting = bool(vol_first and vol_second and vol_second < vol_first * 0.95)

    price = closes[-1]
    resistance_level = round(resistance, 4)
    support_level = round(support, 4)
    wedge_height = swing_highs[0][1] - swing_lows[0][1]
    measured_target = round(resistance_level + wedge_height, 4) if wedge_height > 0 else None

    vol_recent = _avg_volume(bars, len(bars) - 6, len(bars) - 1)
    vol_today = float(bars[-1].get("volume") or 0)
    vol_ratio = (vol_today / vol_recent) if vol_recent else None
    vol_confirmed = vol_ratio is not None and vol_ratio >= 1.4

    breakout = price > resistance_level * 1.002
    failed = price < support_level * 0.998
    near_apex = price >= resistance_level * 0.97 and not breakout

    if failed:
        state = "failed"
    elif breakout and vol_confirmed:
        state = "breakout_confirmed"
    elif breakout:
        state = "breakout_weak"
    elif near_apex and vol_contracting:
        state = "apex_approaching"
    else:
        state = "wedge_forming"

    return {
        "pattern": "falling_wedge",
        "direction": "bullish",
        "state": state,
        "resistance": resistance_level,
        "support": support_level,
        "swing_highs": len(swing_highs),
        "swing_lows": len(swing_lows),
        "volume_contracting": vol_contracting,
        "breakout_volume_ratio": round(vol_ratio, 2) if vol_ratio else None,
        "measured_target": measured_target,
        "play_type": (
            "confirmed_long" if state == "breakout_confirmed"
            else "early_stalk" if state in ("wedge_forming", "apex_approaching")
            else "wait_or_avoid"
        ),
    }


def detect_rising_wedge(bars: list[dict[str, Any]], timeframe: str) -> dict[str, Any] | None:
    """Rising wedge — bearish bias; breaks downward ([StockCharts](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/rising-wedge))."""
    min_bars = 25 if timeframe == "weekly" else 30
    if len(bars) < min_bars:
        return None

    window = bars[-min(len(bars), 70 if timeframe == "daily" else 45) :]
    wn = len(window)
    if wn < min_bars:
        return None

    highs = [b["high"] for b in window]
    lows = [b["low"] for b in window]
    closes = [b["close"] for b in window]
    swing_highs, swing_lows = _chunk_extremes(highs, lows, chunks=10)
    if len(swing_highs) < 3 or len(swing_lows) < 3:
        return None

    hh_rising = swing_highs[0][1] < swing_highs[-1][1] * 0.99
    ll_rising = swing_lows[0][1] < swing_lows[-1][1] * 0.99
    if not (hh_rising and ll_rising):
        return None

    upper_slope = _line_slope(swing_highs)
    lower_slope = _line_slope(swing_lows)
    if upper_slope is None or lower_slope is None:
        return None
    # Lower support rises faster than upper resistance — converging up-sloping wedge
    if lower_slope <= upper_slope or upper_slope <= 0 or lower_slope <= 0:
        return None

    first_range = swing_highs[0][1] - swing_lows[0][1]
    last_range = swing_highs[-1][1] - swing_lows[-1][1]
    if first_range <= 0 or last_range >= first_range * 0.85:
        return None

    resistance = _project_line(swing_highs, wn - 1)
    support = _project_line(swing_lows, wn - 1)
    if resistance is None or support is None:
        return None

    half = wn // 2
    vol_first = _avg_volume(window, 0, half)
    vol_second = _avg_volume(window, half, wn)
    vol_contracting = bool(vol_first and vol_second and vol_second < vol_first * 0.95)

    price = closes[-1]
    resistance_level = round(resistance, 4)
    support_level = round(support, 4)
    wedge_height = swing_highs[0][1] - swing_lows[0][1]
    measured_target = round(support_level - wedge_height, 4) if wedge_height > 0 else None

    vol_recent = _avg_volume(bars, len(bars) - 6, len(bars) - 1)
    vol_today = float(bars[-1].get("volume") or 0)
    vol_ratio = (vol_today / vol_recent) if vol_recent else None
    vol_confirmed = vol_ratio is not None and vol_ratio >= 1.4

    breakdown = price < support_level * 0.998
    failed = price > resistance_level * 1.002
    near_apex = price <= support_level * 1.03 and not breakdown

    if failed:
        state = "failed"
    elif breakdown and vol_confirmed:
        state = "breakdown_confirmed"
    elif breakdown:
        state = "breakdown_weak"
    elif near_apex and vol_contracting:
        state = "apex_approaching"
    else:
        state = "wedge_forming"

    return {
        "pattern": "rising_wedge",
        "direction": "bearish",
        "state": state,
        "resistance": resistance_level,
        "support": support_level,
        "swing_highs": len(swing_highs),
        "swing_lows": len(swing_lows),
        "volume_contracting": vol_contracting,
        "breakdown_volume_ratio": round(vol_ratio, 2) if vol_ratio else None,
        "measured_target": measured_target,
        "play_type": (
            "confirmed_short" if state == "breakdown_confirmed"
            else "early_stalk" if state in ("wedge_forming", "apex_approaching")
            else "wait_or_avoid"
        ),
    }


def detect_cup_and_handle(bars: list[dict[str, Any]], timeframe: str) -> dict[str, Any] | None:
    """Heuristic cup-and-handle (O'Neil rules). Best on daily/weekly."""
    min_bars = 50 if timeframe == "weekly" else 60
    if len(bars) < min_bars:
        return None

    closes = [b["close"] for b in bars]
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    n = len(closes)
    window = bars[-min(n, 130 if timeframe == "daily" else 65) :]

    wc = [b["close"] for b in window]
    wh = [b["high"] for b in window]
    wl = [b["low"] for b in window]
    wn = len(wc)
    if wn < min_bars:
        return None

    # Left rim: peak in first 35% of window
    left_end = max(10, int(wn * 0.35))
    left_rim_idx = max(range(left_end), key=lambda i: wh[i])
    left_rim = wh[left_rim_idx]

    # Cup bottom: lowest in middle 30-70%
    mid_start, mid_end = int(wn * 0.30), int(wn * 0.70)
    if mid_end <= mid_start + 5:
        return None
    bottom_idx = min(range(mid_start, mid_end), key=lambda i: wl[i])
    cup_low = wl[bottom_idx]

    if left_rim <= 0:
        return None
    depth_pct = (left_rim - cup_low) / left_rim * 100
    if depth_pct < 10 or depth_pct > 45:
        return None

    # V-cup check: bottom should not be too close to edges
    if bottom_idx < wn * 0.25 or bottom_idx > wn * 0.75:
        return None

    # Right rim area: peak in 55-85% of window (before handle)
    right_start, right_end = int(wn * 0.55), max(int(wn * 0.85), wn - 15)
    if right_end <= right_start:
        return None
    right_rim_idx = max(range(right_start, right_end), key=lambda i: wh[i])
    right_rim = wh[right_rim_idx]
    recovery = right_rim / left_rim if left_rim else 0
    if recovery < 0.85:
        return None

    # Handle: last 5-15 bars pullback
    handle_len = min(15, max(5, int(wn * 0.12)))
    handle_bars = window[-handle_len:]
    handle_high = max(b["high"] for b in handle_bars)
    handle_low = min(b["low"] for b in handle_bars)
    handle_depth_pct = (handle_high - handle_low) / handle_high * 100 if handle_high else 0

    cup_range = left_rim - cup_low
    handle_mid = (handle_high + handle_low) / 2
    in_upper_half = handle_mid >= cup_low + cup_range * 0.5 if cup_range else False

    # Volume: handle vs prior 50 bars
    vol_handle = _avg_volume(window, wn - handle_len, wn)
    vol_50 = _avg_volume(bars, max(0, n - 50), n)
    handle_vol_dry = bool(vol_handle and vol_50 and vol_handle < vol_50 * 0.95)

    pivot = round(handle_high, 4)
    price = closes[-1]
    breakout = price > pivot * 1.001
    latest_vol = float(bars[-1].get("volume") or 0)
    breakout_vol_pct = ((latest_vol / vol_50 - 1) * 100) if vol_50 and breakout else None
    vol_confirmed = breakout_vol_pct is not None and breakout_vol_pct >= 35

    # Wedging handle: handle lows rising sharply into resistance
    handle_closes = [b["close"] for b in handle_bars]
    wedging = len(handle_closes) >= 3 and handle_closes[-1] > handle_closes[0] * 1.04 and handle_depth_pct < 5

    if wedging or handle_depth_pct > 15:
        state = "failed"
    elif breakout and vol_confirmed:
        state = "breakout_confirmed"
    elif breakout:
        state = "breakout_weak"
    elif handle_depth_pct <= 12 and in_upper_half and right_rim_idx < wn - 3:
        state = "handle_ready" if handle_vol_dry else "handle_forming"
    elif bottom_idx < wn - handle_len - 5:
        state = "cup_forming"
    else:
        state = "handle_forming"

    return {
        "pattern": "cup_and_handle",
        "direction": "bullish",
        "state": state,
        "pivot": pivot,
        "cup_depth_pct": round(depth_pct, 1),
        "handle_depth_pct": round(handle_depth_pct, 1),
        "in_upper_half": in_upper_half,
        "handle_volume_dry": handle_vol_dry,
        "breakout_volume_vs_50d_pct": round(breakout_vol_pct, 1) if breakout_vol_pct is not None else None,
        "wedging_handle": wedging,
        "play_type": (
            "confirmed_long" if state == "breakout_confirmed"
            else "early_stalk" if state in ("handle_forming", "handle_ready", "cup_forming")
            else "wait_or_avoid"
        ),
    }


def detect_ascending_triangle(bars: list[dict[str, Any]], timeframe: str) -> dict[str, Any] | None:
    """Heuristic ascending triangle — flat resistance + rising lows."""
    min_bars = 25 if timeframe == "weekly" else 30
    if len(bars) < min_bars:
        return None

    window = bars[-min(len(bars), 80 if timeframe == "daily" else 40) :]
    wn = len(window)
    if wn < min_bars:
        return None

    highs = [b["high"] for b in window]
    lows = [b["low"] for b in window]
    closes = [b["close"] for b in window]

    # Resistance: top 20% of highs cluster
    sorted_highs = sorted(highs)
    resistance_zone = sorted_highs[int(len(sorted_highs) * 0.85) :]
    if not resistance_zone:
        return None
    resistance = sum(resistance_zone) / len(resistance_zone)
    res_band = resistance * 0.018  # ~1.8% tolerance

    touch_count = sum(1 for h in highs if abs(h - resistance) <= res_band or h >= resistance - res_band)
    if touch_count < 2:
        return None

    # Swing lows (simplified): every 5 bars local minima
    swing_lows: list[float] = []
    for i in range(4, wn - 4, 3):
        segment = lows[i - 2 : i + 3]
        if lows[i] == min(segment):
            swing_lows.append(lows[i])

    if len(swing_lows) < 3:
        return None

    rising_lows = all(swing_lows[i] > swing_lows[i - 1] * 1.002 for i in range(1, len(swing_lows)))
    if not rising_lows:
        return None

    # Volume contraction: first half vs second half of pattern
    half = wn // 2
    vol_first = _avg_volume(window, 0, half)
    vol_second = _avg_volume(window, half, wn)
    vol_contracting = bool(vol_first and vol_second and vol_second < vol_first * 0.95)

    price = closes[-1]
    resistance_level = round(resistance, 4)
    breakout = price > resistance_level * 1.002
    vol_recent = _avg_volume(bars, len(bars) - 6, len(bars) - 1)
    vol_today = float(bars[-1].get("volume") or 0)
    vol_ratio = (vol_today / vol_recent) if vol_recent else None
    vol_confirmed = vol_ratio is not None and vol_ratio >= 1.4

    # Apex: price within 3% of resistance
    near_apex = price >= resistance * 0.97

    height = resistance - swing_lows[0]
    measured_target = round(resistance + height, 4) if height > 0 else None

    if lows[-1] < swing_lows[-2] * 0.98:
        state = "failed"
    elif breakout and vol_confirmed:
        state = "breakout_confirmed"
    elif breakout:
        state = "breakout_weak"
    elif near_apex and vol_contracting:
        state = "apex_approaching"
    else:
        state = "triangle_forming"

    return {
        "pattern": "ascending_triangle",
        "direction": "bullish",
        "state": state,
        "resistance": resistance_level,
        "higher_lows_count": len(swing_lows),
        "resistance_touches": touch_count,
        "volume_contracting": vol_contracting,
        "breakout_volume_ratio": round(vol_ratio, 2) if vol_ratio else None,
        "measured_target": measured_target,
        "play_type": (
            "confirmed_long" if state == "breakout_confirmed"
            else "early_stalk" if state in ("triangle_forming", "apex_approaching")
            else "wait_or_avoid"
        ),
    }


def detect_chart_patterns(bars: list[dict[str, Any]], timeframe: str) -> list[dict[str, Any]]:
    """Run all chart pattern detectors for a timeframe."""
    if timeframe not in ("daily", "weekly", "monthly", "3mo"):
        return []
    found: list[dict[str, Any]] = []
    cup = detect_cup_and_handle(bars, timeframe)
    if cup:
        cup["timeframe"] = timeframe
        found.append(cup)
    tri = detect_ascending_triangle(bars, timeframe)
    if tri:
        tri["timeframe"] = timeframe
        found.append(tri)
    fw = detect_falling_wedge(bars, timeframe)
    if fw:
        fw["timeframe"] = timeframe
        found.append(fw)
    rw = detect_rising_wedge(bars, timeframe)
    if rw:
        rw["timeframe"] = timeframe
        found.append(rw)
    return found


def summarize_patterns(all_patterns: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate patterns across timeframes for MTF output."""
    if not all_patterns:
        return {"detected": False, "patterns": []}

    bullish_states = ("breakout_confirmed", "handle_ready", "apex_approaching", "wedge_forming")
    bearish_states = ("breakdown_confirmed", "apex_approaching", "wedge_forming")

    bullish_primary = None
    bearish_primary = None
    for p in all_patterns:
        if p.get("direction") == "bearish" and p.get("state") in bearish_states:
            bearish_primary = p
            break
    for p in all_patterns:
        if p.get("direction") != "bearish" and p.get("state") in bullish_states:
            bullish_primary = p
            break

    primary = bullish_primary or bearish_primary or all_patterns[0]

    tags: list[str] = []
    for p in all_patterns:
        name = p.get("pattern", "")
        state = p.get("state", "")
        if name == "cup_and_handle":
            if "breakout" in state:
                tags.append("cup_and_handle_breakout")
            elif state in ("handle_ready", "handle_forming"):
                tags.append("cup_and_handle_ready" if state == "handle_ready" else "cup_and_handle_forming")
            elif state == "failed":
                tags.append("cup_and_handle_failed")
        elif name == "ascending_triangle":
            if "breakout" in state:
                tags.append("ascending_triangle_breakout")
            elif state == "apex_approaching":
                tags.append("ascending_triangle_apex")
            elif state == "triangle_forming":
                tags.append("ascending_triangle_forming")
            elif state == "failed":
                tags.append("ascending_triangle_failed")
        elif name == "falling_wedge":
            if "breakout" in state:
                tags.append("falling_wedge_breakout")
            elif state == "apex_approaching":
                tags.append("falling_wedge_apex")
            elif state == "wedge_forming":
                tags.append("falling_wedge_forming")
            elif state == "failed":
                tags.append("falling_wedge_failed")
        elif name == "rising_wedge":
            if "breakdown" in state:
                tags.append("rising_wedge_breakdown")
            elif state == "apex_approaching":
                tags.append("rising_wedge_apex")
            elif state == "wedge_forming":
                tags.append("rising_wedge_forming")
            elif state == "failed":
                tags.append("rising_wedge_failed")

    return {
        "detected": True,
        "primary": primary,
        "bullish_primary": bullish_primary,
        "bearish_primary": bearish_primary,
        "all": all_patterns,
        "setup_tags": list(dict.fromkeys(tags)),
    }
