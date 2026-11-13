from datetime import datetime
from zoneinfo import ZoneInfo
import logic, storage

NOW = datetime(2026, 11, 11, 15, 0, tzinfo=ZoneInfo("Asia/Seoul"))

def orders_changes(d):
    return storage.load_orders(d / "orders.csv"), storage.load_changes(d / "etd_changes.csv")

def by(orders, no):
    return next(o for o in orders if o["order_no"] == no)

def test_history_words(tmpdata):
    o, c = orders_changes(tmpdata)
    assert logic.etd_history(by(o, "PO-2611-009"), c) == "처음 ETD보다 7일 늦어짐 (2회 변경)"
    assert logic.etd_history(by(o, "PO-2611-010"), c) == "처음 ETD보다 4일 앞당겨짐 (1회 변경)"
    assert logic.etd_history(by(o, "PO-2611-003"), c) == "처음 ETD와 같음 (2회 변경)"
    assert logic.etd_history(by(o, "PO-2611-002"), c) == "변경 없음"

def test_change_validation(tmpdata):
    o, _ = orders_changes(tmpdata)
    t = by(o, "PO-2611-002")
    assert "사유" in logic.validate_etd_change(t, "2026-11-27", " ")
    assert "같은 날짜" in logic.validate_etd_change(t, "2026-11-25", "롤오버")
    assert "2026-11-20처럼" in logic.validate_etd_change(t, "11/27", "롤오버")
    assert logic.validate_etd_change(t, "2026-11-27", "롤오버") is None

def test_change_is_logged_append_only(tmpdata):
    o, c = orders_changes(tmpdata)
    ch = logic.build_change("PO-2611-002", "2026-11-25", "2026-11-27", "롤오버", NOW)
    storage.apply_etd_change(ch, tmpdata / "orders.csv", tmpdata / "etd_changes.csv", tmpdata / "bk")
    o2, c2 = orders_changes(tmpdata)
    assert by(o2, "PO-2611-002")["etd"] == "2026-11-27"
    assert c2[:len(c)] == c and len(c2) == len(c) + 1 and c2[-1]["changed_at"] == "2026-11-11 15:00"

def test_demo_changes_and_skips(tmpdata):
    o, _ = orders_changes(tmpdata)
    plan, skipped = logic.plan_demo_updates(o, storage.load_carrier_demo(tmpdata / "carrier_demo.json"), NOW)
    assert [p["order_no"] for p in plan] == ["PO-2611-002", "PO-2611-004"] and skipped == 3   # v3.1: 002 응답 추가
    assert all(p["reason"] == "선사 조회(데모)" for p in plan)
    assert logic.lc_status({**by(o, "PO-2611-004"), "etd": "2026-11-24"})["label"] == "🟡 L/C 기한까지 1일 남음"

def test_demo_none():
    assert logic.plan_demo_updates([], []) == ([], 0)
