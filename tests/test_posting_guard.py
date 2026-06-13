"""C2 (quiet hours) + C4 (kill switch) + C1 (warm-up ramp) — posting_guard tests.

Pure stdlib, no Flask/DB needed:
    .venv-local/bin/python tests/test_posting_guard.py
Exits non-zero on any failure. The kill-switch flag is isolated to a temp dir via
RA_DATA_DIR so the real data/ volume is never touched.
"""
import os
import sys
import tempfile
from datetime import datetime

os.environ["RA_DATA_DIR"] = tempfile.mkdtemp(prefix="posting_guard_test_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from zoneinfo import ZoneInfo
    IL = ZoneInfo("Asia/Jerusalem")
except Exception:  # pragma: no cover
    IL = None

from common import posting_guard as pg

FAILS = []


def check(name, cond):
    print(("  PASS " if cond else "  FAIL ") + name)
    if not cond:
        FAILS.append(name)


def at(hour):
    """A tz-aware Israel datetime at the given hour, for injection."""
    base = datetime(2026, 6, 15, hour, 30)
    return base.replace(tzinfo=IL) if IL else base


def main():
    pg.resume()  # ensure a clean (un-paused) starting state

    print("C2 — quiet hours 23:00-07:00 (Asia/Jerusalem):")
    check("02:00 is night", pg.is_night_hours(at(2)) is True)
    check("03:00 is night", pg.is_night_hours(at(3)) is True)
    check("23:00 is night", pg.is_night_hours(at(23)) is True)
    check("06:00 is night", pg.is_night_hours(at(6)) is True)
    check("09:00 is NOT night", pg.is_night_hours(at(9)) is False)
    check("12:00 is NOT night", pg.is_night_hours(at(12)) is False)
    check("19:00 is NOT night", pg.is_night_hours(at(19)) is False)
    check("block_reason@02:00 -> NIGHT_MODE", "NIGHT_MODE" in (pg.block_reason(at(2)) or ""))
    check("block_reason@09:00 -> None (may post)", pg.block_reason(at(9)) is None)

    print("C4 — global kill switch:")
    check("not paused initially", pg.is_paused() is False)
    pg.pause(reason="audit-test")
    check("is_paused() after pause()", pg.is_paused() is True)
    check("KILL_SWITCH blocks even at 09:00 (overrides allowed hours)",
          "KILL_SWITCH" in (pg.block_reason(at(9)) or ""))
    check("can_post()==False while paused", pg.can_post(at(9))[0] is False)
    check("resume() reports it was engaged", pg.resume() is True)
    check("not paused after resume()", pg.is_paused() is False)
    check("block_reason@09:00 None again after resume", pg.block_reason(at(9)) is None)

    print("C1 — warm-up ramp (effective_daily_cap), RAMP_DAYS=7, DAY1_CAP=3:")
    os.environ["WARMUP_RAMP_DAYS"] = "7"
    os.environ["WARMUP_DAY1_CAP"] = "3"
    day0 = pg.effective_daily_cap(50, 0)
    check(f"day 0 cap ({day0}) < configured 50", day0 < 50)
    check(f"day 0 cap ({day0}) >= floor 3", day0 >= 3)
    check("day 3 ramps above day 0", pg.effective_daily_cap(50, 3) > day0)
    check("day 7 == configured 50", pg.effective_daily_cap(50, 7) == 50)
    check("day 30 == configured 50", pg.effective_daily_cap(50, 30) == 50)
    check("unknown age == configured (no ramp)", pg.effective_daily_cap(50, None) == 50)

    print("")
    if FAILS:
        print(f"RESULT: {len(FAILS)} FAILED -> {FAILS}")
        return 1
    print("RESULT: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
