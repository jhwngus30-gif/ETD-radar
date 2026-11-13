"""F5-3 일정 캘린더"""
from datetime import datetime, date
from zoneinfo import ZoneInfo
import logic, storage

NOW = datetime(2026, 11, 11, 15, 0, tzinfo=ZoneInfo("Asia/Seoul"))

def test_events_kinds_and_order(tmpdata):
    ev = logic.calendar_events(storage.load_orders(tmpdata / "orders.csv"), NOW)
    assert ev == sorted(ev, key=lambda e: (e["date"], logic.CAL_KINDS.index(e["kind"]), e["order_no"]))
    e001 = [(e["kind"], e["date"]) for e in ev if e["order_no"] == "PO-2611-001"]
    assert ("ETD", "2026-11-20") in e001 and ("L/C", "2026-11-19") in e001 and ("마감", "2026-11-17") in e001 and ("ETA", "2026-12-12") in e001
    assert all(e["level"] == "red" for e in ev if e["order_no"] == "PO-2611-001")

def test_shipped_only_shipped_and_eta(tmpdata):
    ev = logic.calendar_events(storage.load_orders(tmpdata / "orders.csv"), NOW)
    kinds = {e["kind"] for e in ev if e["order_no"] == "PO-2611-006"}
    assert kinds == {"선적", "ETA"}

def test_deleted_and_tt_rules(tmpdata):
    ev = logic.calendar_events(storage.load_orders(tmpdata / "orders.csv"), NOW)
    assert not any(e["order_no"] == "PO-2611-008" for e in ev)                         # 삭제됨
    assert not any(e["order_no"] == "PO-2611-011" and e["kind"] == "L/C" for e in ev)  # T/T 는 L/C 없음
    assert any(e["order_no"] == "PO-2611-014" and e["level"] == "late" for e in ev)    # ETD 지남 색

def test_events_empty():
    assert logic.calendar_events([], NOW) == []

def test_month_grid_sunday_start():
    g = logic.month_grid(2026, 11)
    assert g[0][0] == date(2026, 11, 1) and g[0][0].weekday() == 6 and all(len(w) == 7 for w in g)
    assert date(2026, 11, 30) in g[-1]
