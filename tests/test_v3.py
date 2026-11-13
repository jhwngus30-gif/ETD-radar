"""v3 — ETD 지남 · 서류 마감 · 수정/L-C 연장 · 되돌리기 · 검색 · 불러오기 · 알림 · 보고 조치 (PRD v3)"""
import csv, io
from datetime import datetime
from zoneinfo import ZoneInfo
import pytest
import logic, storage

KST = ZoneInfo("Asia/Seoul")
NOW = datetime(2026, 11, 11, 15, 0, tzinfo=KST)        # 가상 데이터 기준일

def load(d):
    return storage.load_orders(d / "orders.csv"), storage.load_changes(d / "etd_changes.csv")

def by(orders, no):
    return next(o for o in orders if o["order_no"] == no)

def mk(**kw):
    o = {"order_no": "T", "buyer": "가상", "item": "김", "payment_terms": "L/C", "port_of_loading": "부산",
         "etd": "2026-11-20", "lc_ship_by": "2026-12-20", "status": "선적 대기", "shipped_on": "", "deleted": "False"}
    o.update(kw); return o

# ---- F2-1 ETD 지남 미선적 ----
@pytest.mark.parametrize("etd,days", [("2026-11-10", 1), ("2026-11-04", 7)])
def test_etd_overdue_is_late_and_first(etd, days):
    s = logic.lc_status(mk(etd=etd, lc_ship_by="2026-11-09"), NOW)     # L/C도 초과지만 ETD 지남이 먼저
    assert s["level"] == "late" and s["label"] == f"🚨 ETD {days}일 지남 · 선적 미확인"

def test_etd_today_is_not_late():
    assert logic.lc_status(mk(etd="2026-11-11"), NOW)["level"] != "late"

def test_late_applies_to_tt_and_not_to_shipped():
    assert logic.lc_status(mk(etd="2026-11-01", payment_terms="T/T", lc_ship_by=""), NOW)["level"] == "late"
    shipped = mk(etd="2026-11-01", status="선적 완료", shipped_on="2026-11-01")
    assert logic.lc_status(shipped, NOW)["level"] != "late"

def test_late_uses_port_local_today():
    early = datetime(2026, 11, 12, 1, 0, tzinfo=KST)                     # 호찌민은 아직 11/11
    assert logic.lc_status(mk(etd="2026-11-11", port_of_loading="부산"), early)["level"] == "late"
    assert logic.lc_status(mk(etd="2026-11-11", port_of_loading="호찌민"), early)["level"] != "late"

def test_sample_summary_has_one_late(tmpdata):
    o, _ = load(tmpdata)
    assert logic.lc_summary(o, NOW) == {"late": 1, "red": 1, "yellow": 2, "late_shipped": 1}
    assert logic.lc_status(by(o, "PO-2611-014"), NOW)["label"] == "🚨 ETD 2일 지남 · 선적 미확인"

def test_green_uses_blue_emoji():
    assert logic.lc_status(mk(etd="2026-11-20", lc_ship_by="2026-12-20"), NOW)["label"].startswith("🔵 ")

# ---- F2-5 서류 마감 ----
@pytest.mark.parametrize("cutoff,level,text", [("2026-11-10", "red", "서류 마감 1일 지남"), ("2026-11-11", "yellow", "서류 마감 D-Day"),
                                              ("2026-11-13", "yellow", "서류 마감 D-2"), ("2026-11-14", None, None)])
def test_cutoff(cutoff, level, text):
    c = logic.cutoff_status(mk(cutoff=cutoff), NOW)
    assert (c and c["level"]) == level and (not text or text in c["label"])

def test_cutoff_none_when_shipped_or_empty():
    assert logic.cutoff_status(mk(cutoff="2026-11-01", status="선적 완료", shipped_on="2026-11-01"), NOW) is None
    assert logic.cutoff_status(mk(), NOW) is None

# ---- F5 알림 ----
def test_alerts_order(tmpdata):
    o, _ = load(tmpdata)
    a = logic.alerts(o, NOW)
    assert [x["level"] for x in a][:2] == ["late", "red"]
    assert a[0]["order_no"] == "PO-2611-014"
    assert any("서류 마감" in x["label"] and x["order_no"] == "PO-2611-014" for x in a)   # 014 마감도 지남
    assert all(x["order_no"] != "PO-2611-008" for x in a)                                # 삭제된 오더 제외

def test_alerts_none():
    assert logic.alerts([], NOW) == []

# ---- F4 보고 조치 ----
def test_report_has_late_first_and_action(tmpdata):
    o, _ = load(tmpdata)
    t = logic.report_text(o, NOW).split("\n")
    assert t[0] == "[ETD 레이더] 2026-11-11 선적 위험 보고 — 🚨 1건 · 🔴 1건 · 🟡 2건"
    assert t[1].startswith("1. 🚨 PO-2611-014") and t[1].endswith("· 조치: (미정)")
    assert t[2].startswith("2. 🔴 PO-2611-001") and t[2].endswith("· 조치: L/C 연장 요청 — 바이어 회신 대기")

# ---- F1-10 수정 · L/C 연장 ----
def test_edit_lc_needs_reason_and_logs():
    o = mk(order_no="PO-E", lc_ship_by="2026-11-19", etd="2026-11-20")
    _, _, _, err = logic.plan_edit(o, {"lc_ship_by": "2026-11-30"}, "", NOW)
    assert "L/C 기한" in err and "사유" in err
    diff, etd_ch, lc_ch, err = logic.plan_edit(o, {"lc_ship_by": "2026-11-30"}, "L/C 연장(Amendment)", NOW)
    assert err is None and diff == {"lc_ship_by": "2026-11-30"} and etd_ch is None
    assert lc_ch["old"] == "2026-11-19" and lc_ch["new"] == "2026-11-30" and lc_ch["field"] == "L/C 기한"
    assert logic.lc_status({**o, **diff}, NOW)["label"] == "🔵 L/C 기한까지 10일 남음"

def test_edit_etd_logs_to_etd_changes():
    diff, etd_ch, _, err = logic.plan_edit(mk(), {"etd": "2026-11-27"}, "롤오버", NOW)
    assert err is None and etd_ch["old_etd"] == "2026-11-20" and etd_ch["new_etd"] == "2026-11-27"

def test_edit_plain_fields_no_reason_needed():
    diff, etd_ch, lc_ch, err = logic.plan_edit(mk(), {"buyer": "새 바이어", "booking_no": "BK1"}, "", NOW)
    assert err is None and diff == {"buyer": "새 바이어", "booking_no": "BK1"} and not etd_ch and not lc_ch

def test_edit_validation_and_no_change():
    assert "없는 날짜" in logic.plan_edit(mk(), {"cutoff": "2026-02-30"}, "", NOW)[3]
    assert logic.plan_edit(mk(), {"buyer": "가상"}, "", NOW)[3] == "바뀐 내용이 없어요."
    assert "비어" in logic.plan_edit(mk(), {"buyer": ""}, "", NOW)[3]

def test_edit_to_tt_clears_lc():
    diff, *_ , err = logic.plan_edit(mk(), {"payment_terms": "T/T"}, "", NOW)
    assert err is None and diff["lc_ship_by"] == ""

def test_edit_persists_and_logs(tmpdata):
    o, _ = load(tmpdata)
    diff, etd_ch, lc_ch, _ = logic.plan_edit(by(o, "PO-2611-001"), {"lc_ship_by": "2026-11-28"}, "L/C 연장(Amendment)", NOW)
    storage.update_order("PO-2611-001", diff, tmpdata / "orders.csv", tmpdata / "bk")
    storage.append_change_log(lc_ch, tmpdata / "change_log.csv", tmpdata / "bk")
    o2, _ = load(tmpdata)
    assert by(o2, "PO-2611-001")["lc_ship_by"] == "2026-11-28" and len(o2) == len(o)
    assert storage.load_change_log(tmpdata / "change_log.csv")[-1]["reason"] == "L/C 연장(Amendment)"

# ---- F1-11 되돌리기 ----
def test_unship(tmpdata):
    o, _ = load(tmpdata)
    changes, log = logic.plan_unship(by(o, "PO-2611-006"), NOW)
    assert changes == {"status": "선적 대기", "shipped_on": ""} and log["old"] == "선적 완료 (2026-11-06)"

# ---- F1-12 검색 ----
def test_search(tmpdata):
    o, _ = load(tmpdata)
    nos = lambda q: sorted(x["order_no"] for x in logic.search_orders(o, q))
    assert nos("hudson") == ["PO-2611-001", "PO-2611-009"]
    assert nos("HMMBK") == ["PO-2611-001", "PO-2611-009"] and nos("maeu2611") == ["PO-2611-006"]
    assert nos("없는말") == [] and len(nos("")) == 14

# ---- F4-4 불러오기 ----
def test_import_roundtrip_skips_existing(tmpdata):
    o, c = load(tmpdata)
    text = logic.export_csv_bytes(o, c, NOW).decode("utf-8-sig")
    added, skipped, errors = logic.parse_import(text, [x["order_no"] for x in o], NOW)
    assert added == [] and len(skipped) == 13 and errors == []

def test_import_into_empty_keeps_fields(tmpdata):
    o, c = load(tmpdata)
    text = logic.export_csv_bytes(o, c, NOW).decode("utf-8-sig")
    added, skipped, errors = logic.parse_import(text, [], NOW)
    assert len(added) == 13 and not skipped and not errors
    a1 = next(x for x in added if x["order_no"] == "PO-2611-001")
    assert a1["booking_no"] == "HMMBK2611001" and a1["action"].startswith("L/C 연장")
    a6 = next(x for x in added if x["order_no"] == "PO-2611-006")
    assert a6["status"] == "선적 완료" and a6["shipped_on"] == "2026-11-06"

def test_import_errors_with_line_numbers():
    text = "오더번호,바이어,품목,결제 조건,선적항,ETD,L/C 선적 기한\n" \
           "N1,가상,김,L/C,부산,2026-12-01,2026-12-10\n" \
           "N2,가상,김,L/C,부산,2026-12-01,\n" \
           "N3,가상,김,T/T,평택,2026-12-01,\n" \
           "N1,가상,김,T/T,부산,2026-12-01,\n"
    added, skipped, errors = logic.parse_import(text, [], NOW)
    assert [a["order_no"] for a in added] == ["N1"] and skipped == ["N1"]
    assert [e[0] for e in errors] == [3, 4] and "L/C 선적 기한" in errors[0][1] and "선적항" in errors[1][1]

def test_import_bad_file():
    added, skipped, errors = logic.parse_import("a,b\n1,2\n", [], NOW)
    assert not added and errors and "오더번호" in errors[0][1]

# ---- F6-4 날짜 표기 ----
def test_fmt_date():
    from datetime import date
    assert logic.fmt_date("2026-11-20", date(2026, 11, 11)) == "11/20 (금)"
    assert logic.fmt_date("2027-01-05", date(2026, 11, 11)) == "2027-01-05"
    assert logic.fmt_date("", date(2026, 11, 11)) == "—"
