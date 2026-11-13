from datetime import datetime
from zoneinfo import ZoneInfo
import logic, storage

NOW = datetime(2026, 11, 12, 9, 0, tzinfo=ZoneInfo("Asia/Seoul"))
BASE = {"order_no": "PO-NEW", "buyer": "가상", "item": "김", "etd": "2026-11-20", "lc_ship_by": "2026-11-25",
        "payment_terms": "L/C", "port_of_loading": "부산"}  # v2: 결제 조건 · 선적항 필수

def test_sort_by_etd_then_order_no(tmpdata):
    nos = [o["order_no"] for o in logic.active_orders(storage.load_orders(tmpdata / "orders.csv"))]
    assert nos.index("PO-2611-001") + 1 == nos.index("PO-2611-009")
    assert "PO-2611-008" not in nos

def test_required_duplicate_and_dates():
    assert "비어" in logic.validate_new_order({**BASE, "buyer": " "}, [])
    assert "이미 등록된" in logic.validate_new_order(BASE, ["PO-NEW"])
    assert "2026-11-20처럼" in logic.validate_new_order({**BASE, "etd": "2026/11/20"}, [])
    assert "없는 날짜" in logic.validate_new_order({**BASE, "etd": "2026-02-30"}, [])
    assert logic.validate_new_order(BASE, []) is None

def test_empty_file_opens(tmp_path):
    assert storage.load_orders(tmp_path / "none" / "orders.csv") == []

def test_soft_delete_and_restore_keep_rows(tmpdata):
    p, b = tmpdata / "orders.csv", tmpdata / "bk"
    storage.set_deleted("PO-2611-001", True, p, b)
    rows = storage.load_orders(p)
    assert len(rows) == 14 and "PO-2611-001" in [o["order_no"] for o in logic.deleted_orders(rows)]
    storage.set_deleted("PO-2611-001", False, p, b)
    assert "PO-2611-001" in [o["order_no"] for o in logic.active_orders(storage.load_orders(p))]

def test_cannot_shrink_orders(tmpdata):
    import pytest
    with pytest.raises(ValueError):
        storage._write_orders([], tmpdata / "orders.csv", tmpdata / "bk")

def test_korea_and_local_dates():
    assert logic.today_korea(NOW).isoformat() == "2026-11-12"
    assert logic.local_today("미국 동부", NOW).isoformat() == "2026-11-11"
    assert logic.local_today("", NOW) is None

def test_shipped_on_rules():
    assert "비어" in logic.validate_shipped_on("", NOW)
    assert "오늘" in logic.validate_shipped_on("2026-11-13", NOW)
    assert logic.validate_shipped_on("2026-11-12", NOW) is None
