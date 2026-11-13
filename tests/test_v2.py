"""v2 — 결제 조건 · 선적항(삼국 간) · 보고 내보내기 (PRD F1-8·9, F2 ※, F4)"""
import csv, io
from datetime import datetime
from zoneinfo import ZoneInfo
import logic, storage

KST = ZoneInfo("Asia/Seoul")
NOW = datetime(2026, 11, 11, 15, 0, tzinfo=KST)
BASE = {"order_no": "PO-V2", "buyer": "가상", "item": "김", "etd": "2026-11-20", "lc_ship_by": "",
        "payment_terms": "T/T", "port_of_loading": "부산"}

def load(d):
    return storage.load_orders(d / "orders.csv"), storage.load_changes(d / "etd_changes.csv")

def by(orders, no):
    return next(o for o in orders if o["order_no"] == no)

# ---- F1-8 결제 조건 ----
def test_lc_deadline_required_only_for_lc():
    assert logic.validate_new_order(BASE, []) is None                          # T/T: 기한 없어도 OK
    assert logic.validate_new_order({**BASE, "payment_terms": "D/P"}, []) is None
    assert "L/C 선적 기한" in logic.validate_new_order({**BASE, "payment_terms": "L/C"}, [])
    assert "결제 조건" in logic.validate_new_order({**BASE, "payment_terms": ""}, [])
    assert "결제 조건" in logic.validate_new_order({**BASE, "payment_terms": "D/A"}, [])

def test_non_lc_does_not_store_lc_deadline():
    o = logic.build_order({**BASE, "lc_ship_by": "2026-11-25"}, NOW)
    assert o["payment_terms"] == "T/T" and o["lc_ship_by"] == ""

def test_non_lc_wrong_lc_text_is_ignored_not_error():
    assert logic.validate_new_order({**BASE, "lc_ship_by": "아무거나"}, []) is None

# ---- F2 L/C만 경고 ----
def test_non_lc_is_gray_and_not_counted(tmpdata):
    o, _ = load(tmpdata)
    tt, dp = logic.lc_status(by(o, "PO-2611-011")), logic.lc_status(by(o, "PO-2611-012"))
    assert tt["level"] == "na" and tt["label"] == "⚪ L/C 아님 (T/T)"
    assert dp["level"] == "na" and "D/P" in dp["label"]
    assert logic.lc_summary(o, NOW) == {"late": 1, "red": 1, "yellow": 2, "late_shipped": 1}   # 새 오더가 건수를 바꾸지 않음

def test_old_file_without_new_columns_reads_as_lc_busan(tmp_path):
    p = tmp_path / "orders.csv"
    p.write_text("order_no,buyer,buyer_country,item,etd,eta,lc_ship_by,status,shipped_on,created_at,deleted\n"
                 "A,b,,c,2026-11-20,,2026-11-25,선적 대기,,2026-11-01 09:00,False\n", encoding="utf-8")
    r = storage.load_orders(p)[0]
    assert r["payment_terms"] == "L/C" and r["port_of_loading"] == "부산"

# ---- F1-9 선적항 · 삼국 간 ----
def test_port_required_and_from_list():
    assert "선적항" in logic.validate_new_order({**BASE, "port_of_loading": ""}, [])
    assert "선적항" in logic.validate_new_order({**BASE, "port_of_loading": "평택"}, [])

def test_third_country_flag(tmpdata):
    o, _ = load(tmpdata)
    assert logic.is_third_country(by(o, "PO-2611-013")) is True
    assert logic.is_third_country(by(o, "PO-2611-012")) is False   # 인천 = 한국

def test_port_local_today():
    early = datetime(2026, 11, 12, 1, 0, tzinfo=KST)              # 한국 11/12 01시 → 로테르담 11/11 17시
    assert logic.port_today("부산", early).isoformat() == "2026-11-12"
    assert logic.port_today("로테르담", early).isoformat() == "2026-11-11"
    assert logic.port_today("호찌민", early).isoformat() == "2026-11-11"  # 한국보다 2시간 늦음

def test_shipped_on_future_uses_port_local_today():
    early = datetime(2026, 11, 12, 1, 0, tzinfo=KST)
    assert logic.validate_shipped_on("2026-11-12", early, "부산") is None
    assert "오늘" in logic.validate_shipped_on("2026-11-12", early, "호찌민")   # 호찌민은 아직 11/11

# ---- F4 보고 내보내기 ----
def test_report_text(tmpdata):
    o, _ = load(tmpdata)
    t = logic.report_text(o, NOW).split("\n")
    assert t[0] == "[ETD 레이더] 2026-11-11 선적 위험 보고 — 🚨 1건 · 🔴 1건 · 🟡 2건"   # v3: ETD 지남 포함
    assert t[2].startswith("2. 🔴 PO-2611-001") and "2026-11-19" in t[2]
    assert t[3].startswith("3. 🟡 PO-2611-002") and t[4].startswith("4. 🟡 PO-2611-003")
    assert len(t) == 5 and not any("PO-2611-011" in x for x in t)

def test_report_text_none():
    t = logic.report_text([], NOW).split("\n")
    assert t[1] == "위험 오더 없음" and "🚨 0건 · 🔴 0건 · 🟡 0건" in t[0]

def test_csv_export(tmpdata):
    o, c = load(tmpdata)
    b = logic.export_csv_bytes(o, c, NOW)
    assert b.startswith(b"\xef\xbb\xbf")                              # 엑셀 한글용 BOM
    rows = list(csv.DictReader(io.StringIO(b.decode("utf-8-sig"))))
    assert len(rows) == 13                                           # 14건 중 삭제 1건 제외
    assert rows[0]["오더번호"] == "PO-2611-007"                         # ETD 빠른 순
    r13 = next(r for r in rows if r["오더번호"] == "PO-2611-013")
    assert r13["삼국 간"] == "예" and r13["선적항"] == "호찌민" and r13["여유 일수"] == "12"
    r11 = next(r for r in rows if r["오더번호"] == "PO-2611-011")
    assert r11["경고"] == "L/C 아님 (T/T)" and r11["여유 일수"] == ""

def test_csv_export_empty():
    rows = list(csv.reader(io.StringIO(logic.export_csv_bytes([], []).decode("utf-8-sig"))))
    assert rows == [logic.EXPORT_COLUMNS]
