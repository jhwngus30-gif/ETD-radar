"""v3.2 — 인코텀즈(F1-16 · 17) · 입력 크로스체크(F7)."""
from datetime import datetime
from zoneinfo import ZoneInfo

import logic
import storage

NOW = datetime(2026, 11, 11, 15, 0, tzinfo=ZoneInfo("Asia/Seoul"))


def base(**kw):
    f = {"order_no": "PO-T-1", "buyer": "Test Buyer", "buyer_country": "", "item": "김", "payment_terms": "L/C",
         "port_of_loading": "부산", "etd": "2026-11-20", "eta": "2026-12-10", "lc_ship_by": "2026-11-30",
         "lc_expiry": "2026-12-21", "incoterms": "FOB", "incoterms_place": "Busan", "port_of_discharge": "New York"}
    f.update(kw)
    return f


def levels(order, others=None):
    return [(c["level"], c["field"]) for c in logic.cross_check(order, others, NOW)]


def test_clean_order_has_no_checks():
    assert levels(base()) == []
    assert logic.validate_new_order(base(), []) is None


# ---- F7-1 날짜 순서 ----
def test_eta_before_etd_blocks():
    assert ("error", "eta") in levels(base(eta="2026-11-19"))
    assert "ETA" in logic.validate_new_order(base(eta="2026-11-19"), [])


def test_eta_same_day_and_long_transit_warn():
    assert levels(base(eta="2026-11-20")) == [("warn", "eta")]
    assert levels(base(eta="2027-01-20")) == [("warn", "eta")]          # 61일
    assert levels(base(eta="2027-01-19")) == []                           # 60일 경계


def test_cutoff_after_etd_blocks_and_too_early_warns():
    assert logic.validate_new_order(base(cutoff="2026-11-21"), []) is not None
    assert levels(base(cutoff="2026-11-20")) == []                        # 같은 날은 허용
    assert levels(base(cutoff="2026-11-05")) == [("warn", "cutoff")]     # 15일 앞
    assert levels(base(cutoff="2026-11-06")) == []                        # 14일 앞 경계


def test_etd_far_future_warns():
    assert ("warn", "etd") in levels(base(etd="2027-11-12", eta="2027-12-01", lc_ship_by="2027-12-01",
                                          lc_expiry="2027-12-30"))


# ---- F7-2 L/C 원본 대조 ----
def test_expiry_before_ship_by_blocks():
    assert ("error", "lc_expiry") in levels(base(lc_expiry="2026-11-29"))
    assert logic.validate_new_order(base(lc_expiry="2026-11-29"), []) is not None


def test_expiry_missing_warns_only_for_lc():
    assert levels(base(lc_expiry="")) == [("warn", "lc_expiry")]
    assert levels(base(payment_terms="T/T", lc_ship_by="", lc_expiry="")) == []


def test_presentation_window():
    assert levels(base(lc_expiry="2026-12-21")) == []                     # 21일 = 기본값 경계
    w = logic.cross_check(base(lc_expiry="2026-12-20"), None, NOW)
    assert [c["field"] for c in w] == ["lc_expiry"] and "20일뿐" in w[0]["msg"]
    assert levels(base(lc_expiry="2026-12-10", lc_presentation_days="10")) == []   # 48칸 10일이면 통과
    shipped = base(status="선적 완료", shipped_on="2026-11-18", lc_expiry="2026-12-08")
    assert "실제 선적일" in logic.cross_check(shipped, None, NOW)[0]["msg"]


def test_44e_44f_port_matching():
    assert levels(base(lc_port_loading="Busan, Korea")) == []
    assert levels(base(lc_port_loading="KRPUS")) == []
    assert levels(base(lc_port_loading="Any Korean port")) == []
    assert levels(base(lc_port_loading="Incheon")) == [("warn", "lc_port_loading")]
    assert levels(base(lc_port_discharge="New York, USA")) == []
    assert levels(base(lc_port_discharge="Long Beach")) == [("warn", "lc_port_discharge")]


def test_presentation_days_must_be_number():
    assert logic.validate_new_order(base(lc_presentation_days="삼주"), []) is not None
    assert logic.validate_new_order(base(lc_presentation_days="15"), []) is None


# ---- F7-3 인코텀즈 ----
def test_incoterms_place_rules():
    assert levels(base(incoterms_place="부산")) == []
    assert levels(base(incoterms_place="New York")) == [("warn", "incoterms_place")]      # FOB인데 도착항
    assert levels(base(incoterms="CIF", incoterms_place="New York")) == []
    assert levels(base(incoterms="CIF", incoterms_place="Busan")) == [("warn", "incoterms_place")]
    assert levels(base(incoterms="DAP", incoterms_place="Buyer warehouse NJ")) == []        # D조건은 검사 안 함
    assert levels(base(incoterms="")) == [("warn", "incoterms")]
    assert logic.validate_new_order(base(incoterms="FOT"), []) is not None


def test_booker():
    assert "바이어 측" in logic.booker({"incoterms": "fob"})
    assert "우리가" in logic.booker({"incoterms": "CIF"})
    assert "미입력" in logic.booker({})


# ---- F7-4 L/C 선적 기한 두 번 입력 ----
def test_ship_by_confirm():
    assert logic.validate_new_order(base(lc_ship_by_confirm="2026-11-30"), []) is None
    assert "두 번" in logic.validate_new_order(base(lc_ship_by_confirm="2026-11-03"), [])
    assert "두 번" in logic.validate_new_order(base(lc_ship_by_confirm=""), [])
    assert logic.validate_new_order(base(), []) is None                  # 일괄 등록 등 확인칸이 없으면 검사 안 함


def test_edit_confirm_only_when_ship_by_changes(tmpdata):
    o = next(x for x in storage.load_orders(tmpdata / "orders.csv") if x["order_no"] == "PO-2611-001")
    _, _, _, err = logic.plan_edit(o, {"lc_ship_by": "2026-11-28", "lc_ship_by_confirm": "2026-11-26"}, "연장", NOW)
    assert err and "두 번" in err
    diff, _, lc, err = logic.plan_edit(o, {"lc_ship_by": "2026-11-28", "lc_ship_by_confirm": "2026-11-28"}, "연장", NOW)
    assert err is None and lc["new"] == "2026-11-28"
    diff, _, _, err = logic.plan_edit(o, {"action": "x", "lc_ship_by_confirm": ""}, "", NOW)
    assert err is None and diff == {"action": "x"}


# ---- F7-5 중복 ----
def test_duplicate_booking_and_bl():
    others = [{"order_no": "A", "booking_no": "BK1", "bl_no": "BL9", "deleted": "False"},
              {"order_no": "B", "booking_no": "bk2", "bl_no": "", "deleted": "True"}]
    assert levels(base(booking_no="bk1"), others) == [("warn", "booking_no")]
    assert levels(base(booking_no="BK2"), others) == []                  # 삭제된 오더는 제외
    assert levels(base(bl_no="BL9"), others) == [("warn", "bl_no")]


# ---- 저장 · 불러오기 · 내보내기 ----
def test_non_lc_drops_lc_fields():
    o = logic.build_order(base(payment_terms="T/T", lc_port_loading="Busan", incoterms="fob"), NOW)
    assert o["lc_expiry"] == "" and o["lc_port_loading"] == "" and o["incoterms"] == "FOB"


def test_sample_data_checks(tmpdata):
    a = logic.check_alerts(storage.load_orders(tmpdata / "orders.csv"), NOW)
    got = {x["order_no"]: [c["field"] for c in x["checks"]] for x in a}
    assert got == {"PO-2611-001": ["booking_no"], "PO-2611-009": ["booking_no"], "PO-2611-002": ["lc_expiry"],
                   "PO-2611-005": ["lc_port_discharge"], "PO-2611-010": ["lc_port_loading"]}


def test_import_applies_cross_check():
    text = ("오더번호,바이어,품목,결제 조건,선적항,ETD,ETA,L/C 선적 기한,인코텀즈,L/C 유효기한\n"
            "PO-N-1,A,김,L/C,부산,2026-11-20,2026-12-01,2026-11-30,CIF,2026-12-30\n"
            "PO-N-2,B,김,L/C,부산,2026-11-20,2026-11-10,2026-11-30,CIF,2026-12-30\n")
    added, skipped, errors = logic.parse_import(text, [], NOW)
    assert [o["order_no"] for o in added] == ["PO-N-1"] and added[0]["incoterms"] == "CIF"
    assert errors and errors[0][0] == 3 and "ETA" in errors[0][1]


def test_export_has_new_columns(tmpdata):
    o = storage.load_orders(tmpdata / "orders.csv")
    rows = logic.export_rows(o, [], NOW)
    r = next(x for x in rows if x["오더번호"] == "PO-2611-002")
    assert r["인코텀즈"] == "CIF" and "10일뿐" in r["입력 확인"]
    assert next(x for x in rows if x["오더번호"] == "PO-2611-003")["입력 확인"] == ""
