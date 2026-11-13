"""v3.1 — 일괄 등록(엑셀 붙여넣기 · 빈 양식) · 선사 연동 시뮬레이션 (PRD F1-15, F3-6)"""
import csv, io, json
from datetime import datetime
from zoneinfo import ZoneInfo
import logic, storage, config

KST = ZoneInfo("Asia/Seoul")
NOW = datetime(2026, 11, 11, 15, 0, tzinfo=KST)

def load(d):
    return storage.load_orders(d / "orders.csv"), storage.load_carrier_demo(d / "carrier_demo.json")

def by(orders, no):
    return next(o for o in orders if o["order_no"] == no)

# ---- F1-15 일괄 등록 ----
def test_template_has_headers_only():
    rows = list(csv.reader(io.StringIO(logic.template_csv_bytes().decode("utf-8-sig"))))
    assert rows == [config.TEMPLATE_COLUMNS]

def test_template_roundtrip_through_import():
    text = logic.template_csv_bytes().decode("utf-8-sig") + "N1,가상,,김,T/T,부산,2026-12-01,,,,,BK1,,,\r\n"
    added, skipped, errors = logic.parse_import(text, [], NOW)
    assert [a["order_no"] for a in added] == ["N1"] and added[0]["booking_no"] == "BK1" and not errors

def test_excel_paste_tab_separated():
    paste = "오더번호\t바이어\t품목\t결제 조건\t선적항\tETD\tL/C 선적 기한\n" \
            "X1\tAcme, Inc.\t김\tL/C\t부산\t2026-12-01\t2026-12-10\n" \
            "X2\t가상\t김\tL/C\t부산\t2026-12-01\t\n"
    added, skipped, errors = logic.parse_import(paste, [], NOW)
    assert [a["order_no"] for a in added] == ["X1"] and added[0]["buyer"] == "Acme, Inc."   # 쉼표가 있어도 안 깨짐
    assert errors and errors[0][0] == 3

# ---- F3-6 선사 연동 시뮬레이션 ----
def test_sim_changed(tmpdata):
    o, demo = load(tmpdata)
    r = logic.simulate_carrier_query(by(o, "PO-2611-002"), demo, NOW)
    assert r["ok"] and len(r["steps"]) == 4
    assert "부킹번호 HLBK55021" in r["steps"][0] and "carrierBookingReference=HLBK55021" in r["request"]["url"]
    assert r["request"]["url"].startswith("https://carrier-api.example.com/")
    ev = r["response"]["events"][0]
    assert ev["transportEventTypeCode"] == "DEPA" and ev["eventClassifierCode"] == "EST"
    assert ev["eventDateTime"] == "2026-11-28T18:00:00+09:00" and ev["transportCall"]["UNLocationCode"] == "KRPUS"
    assert "3일 늦어짐" in r["steps"][3] and r["change"]["new_etd"] == "2026-11-28"
    assert logic.lc_status({**by(o, "PO-2611-002"), "etd": r["new_etd"]}, NOW)["label"] == "🔴 L/C 기한 3일 초과"
    json.dumps(r["response"])                                   # 화면에 JSON으로 그대로 보여 줄 수 있음

def test_sim_same(tmpdata):
    o, demo = load(tmpdata)
    r = logic.simulate_carrier_query(by(o, "PO-2611-001"), demo, NOW)
    assert r["ok"] and r["change"] is None and "같음" in r["steps"][3]

def test_sim_uses_bl_when_no_booking(tmpdata):
    o, demo = load(tmpdata)
    r = logic.simulate_carrier_query({**by(o, "PO-2611-001"), "booking_no": "", "bl_no": "BL9"}, demo, NOW)
    assert "B/L 번호 BL9" in r["steps"][0] and "transportDocumentReference=BL9" in r["request"]["url"]

def test_sim_no_key_stops_at_step1(tmpdata):
    o, demo = load(tmpdata)
    r = logic.simulate_carrier_query(by(o, "PO-2611-005"), demo, NOW)
    assert r["ok"] is False and "부킹번호나 B/L 번호" in r["error"] and r["steps"] == []

def test_sim_third_country_port_offset(tmpdata):
    o, demo = load(tmpdata)
    r = logic.simulate_carrier_query(by(o, "PO-2611-013"), demo, NOW)
    ev = r["response"]["events"][0]
    assert ev["transportCall"]["UNLocationCode"] == "VNSGN" and ev["eventDateTime"].endswith("+07:00")
