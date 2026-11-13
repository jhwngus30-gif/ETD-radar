"""F1~F3 날짜 계산 보강 테스트 (today/now 고정)."""
from datetime import datetime
from zoneinfo import ZoneInfo
import pytest
import logic, storage, config

KST = ZoneInfo("Asia/Seoul")
NOW = datetime(2026, 11, 12, 9, 0, tzinfo=KST)
BASE = {"order_no": "PO-X", "buyer": "가상", "item": "김", "etd": "2026-11-20", "lc_ship_by": "2026-11-25",
        "payment_terms": "L/C", "port_of_loading": "부산"}  # v2: 결제 조건 · 선적항 필수

def mk(etd="2026-11-20", lc="2026-11-25", **kw):
    o = {"order_no": "T", "etd": etd, "lc_ship_by": lc, "status": "선적 대기", "shipped_on": "", "deleted": "False"}
    o.update(kw); return o

def test_same_etd_sorted_by_order_no():
    rows = [mk(order_no="B", etd="2026-11-20"), mk(order_no="A", etd="2026-11-20"), mk(order_no="C", etd="2026-11-19")]
    assert [o["order_no"] for o in logic.active_orders(rows)] == ["C", "A", "B"]

def test_zero_orders():
    assert logic.active_orders([]) == [] and logic.deleted_orders([]) == []

@pytest.mark.parametrize("bad", ["", "2026/11/20", "2026-2-3", "20261120", "2026-02-30", "2026-13-01", "2025-02-29"])
def test_bad_dates_rejected_for_etd_lc_shipped(bad):
    assert logic.validate_new_order({**BASE, "etd": bad}, []) is not None
    assert logic.validate_new_order({**BASE, "lc_ship_by": bad}, []) is not None
    assert logic.validate_shipped_on(bad, NOW) is not None

def test_leap_day_ok():
    assert logic.validate_new_order({**BASE, "etd": "2028-02-29"}, []) is None

def test_invalid_country_rejected():
    assert logic.validate_new_order({**BASE, "buyer_country": "프랑스"}, []) is not None

def test_all_countries_listed():
    assert list(config.BUYER_COUNTRIES) == ["미국 동부", "미국 서부", "독일", "영국", "베트남", "일본", "UAE", "호주"]

def test_timezone_gap_us_east_and_kst_evening():
    assert logic.local_today("미국 동부", NOW).isoformat() == "2026-11-11"
    # 한국 11/12 23:00 -> 미국 동부(EST, UTC-5) 11/12 09:00 : 같은 날
    late = datetime(2026, 11, 12, 23, 0, tzinfo=KST)
    assert logic.local_today("미국 동부", late).isoformat() == "2026-11-12"
    assert logic.local_today("호주", NOW).isoformat() == "2026-11-12"
    assert logic.local_today("미국 서부", NOW).isoformat() == "2026-11-11"

def test_now_from_other_timezone_converted_to_kst():
    utc = datetime(2026, 11, 11, 20, 0, tzinfo=ZoneInfo("UTC"))  # KST 11/12 05:00
    assert logic.today_korea(utc).isoformat() == "2026-11-12"

def test_shipped_on_today_ok_tomorrow_rejected_and_midnight_kst():
    just_after = datetime(2026, 11, 12, 0, 0, tzinfo=KST)
    assert logic.validate_shipped_on("2026-11-12", just_after) is None
    assert logic.validate_shipped_on("2026-11-13", just_after) is not None
    before = datetime(2026, 11, 11, 23, 59, tzinfo=KST)
    assert logic.validate_shipped_on("2026-11-12", before) is not None

@pytest.mark.parametrize("etd,level,text", [
    ("2026-11-26", "red", "L/C 기한 1일 초과"), ("2026-11-25", "yellow", "L/C 기한 당일 출항"),
    ("2026-11-18", "yellow", "L/C 기한까지 7일 남음"), ("2026-11-17", "green", "L/C 기한까지 8일 남음"),
    ("2026-12-02", "red", "L/C 기한 7일 초과"), ("2026-11-24", "yellow", "L/C 기한까지 1일 남음"),
])
def test_margin_boundaries(etd, level, text):
    s = logic.lc_status(mk(etd, "2026-11-25"))
    assert s["level"] == level and text in s["label"]

def test_margin_across_month_year_and_leap():
    assert logic.lc_status(mk("2026-12-28", "2027-01-04"))["days"] == 7
    assert logic.lc_status(mk("2028-02-28", "2028-03-01"))["days"] == 2

def test_margin_independent_of_today():
    assert logic.lc_status(mk("2026-11-18", "2026-11-25")) == logic.lc_status(mk("2026-11-18", "2026-11-25"))

def test_shipped_on_deadline_day_ok_and_after_late():
    ok = logic.lc_status(mk(status="선적 완료", shipped_on="2026-11-25"))
    early = logic.lc_status(mk(status="선적 완료", shipped_on="2026-11-01"))
    late = logic.lc_status(mk(status="선적 완료", shipped_on="2026-11-26"))
    assert ok["level"] == "ok" and "기한 내 선적" in ok["label"]
    assert early["level"] == "ok"
    assert late["level"] == "red" and "L/C 기한 1일 넘겨 선적" in late["label"]

def test_summary_excludes_shipped_and_deleted():
    rows = [mk(order_no="a", etd="2026-11-26"), mk(order_no="b", etd="2026-11-25"),
            mk(order_no="c", etd="2026-11-17"),
            mk(order_no="d", etd="2026-11-26", deleted="True"),
            mk(order_no="e", etd="2026-11-26", status="선적 완료", shipped_on="2026-11-26"),
            mk(order_no="f", status="선적 완료", shipped_on="2026-11-20"),
            mk(order_no="g", etd="2026-11-26", status="선적 완료", shipped_on="2026-11-26", deleted="True")]
    assert logic.lc_summary(rows, NOW) == {"late": 0, "red": 1, "yellow": 1, "late_shipped": 1}

def test_history_empty_and_same_etd_rejected():
    o = mk(order_no="Z")
    assert logic.etd_history(o, []) == "변경 없음"
    assert logic.validate_etd_change(o, "2026-11-20", "롤오버") is not None

def test_history_other_order_changes_ignored():
    o = mk(order_no="Z")
    ch = [{"order_no": "Y", "old_etd": "2026-11-01", "new_etd": "2026-11-20", "reason": "r", "changed_at": "2026-11-01 09:00"}]
    assert logic.etd_history(o, ch) == "변경 없음"

def test_history_uses_first_old_etd_across_month():
    o = mk(order_no="Z", etd="2026-12-02")
    ch = [{"order_no": "Z", "old_etd": "2026-11-25", "new_etd": "2026-11-28", "reason": "r", "changed_at": "2026-11-01 09:00"},
          {"order_no": "Z", "old_etd": "2026-11-28", "new_etd": "2026-12-02", "reason": "r", "changed_at": "2026-11-02 09:00"}]
    assert logic.etd_history(o, ch) == "처음 ETD보다 7일 늦어짐 (2회 변경)"

def test_change_time_is_kst_from_utc():
    utc = datetime(2026, 11, 11, 20, 30, tzinfo=ZoneInfo("UTC"))
    assert logic.build_change("Z", "2026-11-20", "2026-11-27", "롤오버", utc)["changed_at"] == "2026-11-12 05:30"
    assert logic.build_order({**BASE}, utc)["created_at"] == "2026-11-12 05:30"

def test_demo_skips_deleted_shipped_unknown_and_same(tmpdata):
    rows = [mk(order_no="A"), mk(order_no="D", deleted="True"), mk(order_no="S", status="선적 완료", shipped_on="2026-11-01")]
    ups = [{"order_no": "A", "new_etd": "2026-11-27"}, {"order_no": "D", "new_etd": "2026-11-27"},
           {"order_no": "S", "new_etd": "2026-11-27"}, {"order_no": "NOPE", "new_etd": "2026-11-27"},
           {"order_no": "A2", "new_etd": "2026-02-30"}]
    plan, skipped = logic.plan_demo_updates(rows, ups, NOW)
    assert [p["order_no"] for p in plan] == ["A"] and skipped == 4
    assert plan[0]["changed_at"] == "2026-11-12 09:00" and plan[0]["reason"] == "선사 조회(데모)"
    assert logic.plan_demo_updates(rows, [{"order_no": "A", "new_etd": "2026-11-20"}], NOW) == ([], 0)

def test_empty_files_created_with_headers(tmp_path):
    assert storage.load_orders(tmp_path / "n" / "o.csv") == []
    assert storage.load_changes(tmp_path / "n" / "c.csv") == []
    assert (tmp_path / "n" / "o.csv").read_text(encoding="utf-8").strip().split(",") == config.ORDER_COLUMNS

def test_shipped_saved_to_tmp_copy_only(tmpdata):
    storage.mark_shipped("PO-2611-002", "2026-11-10", tmpdata / "orders.csv", tmpdata / "bk")
    o = next(o for o in storage.load_orders(tmpdata / "orders.csv") if o["order_no"] == "PO-2611-002")
    assert o["status"] == "선적 완료" and o["shipped_on"] == "2026-11-10"
