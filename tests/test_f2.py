import pytest
import logic, storage

def mk(etd, lc, **kw):
    o = {"order_no": "T", "etd": etd, "lc_ship_by": lc, "status": "선적 대기", "shipped_on": "", "deleted": "False"}
    o.update(kw); return o

@pytest.mark.parametrize("etd,level,text", [
    ("2026-11-26", "red", "L/C 기한 1일 초과"),      # -1일
    ("2026-11-25", "yellow", "L/C 기한 당일 출항"),   # 0일
    ("2026-11-18", "yellow", "L/C 기한까지 7일 남음"),  # 7일
    ("2026-11-17", "green", "L/C 기한까지 8일 남음"),   # 8일
])
def test_boundaries(etd, level, text):
    s = logic.lc_status(mk(etd, "2026-11-25"))
    assert s["level"] == level and text in s["label"]

def test_shipped_final_judgement():
    ok = logic.lc_status(mk("2026-11-05", "2026-11-10", status="선적 완료", shipped_on="2026-11-10"))
    late = logic.lc_status(mk("2026-11-03", "2026-11-08", status="선적 완료", shipped_on="2026-11-09"))
    assert ok["level"] == "ok" and "기한 내 선적" in ok["label"]
    assert late["level"] == "red" and "1일 넘겨 선적" in late["label"]

def test_report_sentence_has_order_dates_days():
    s = logic.lc_status(mk("2026-11-20", "2026-11-19", order_no="PO-2611-001"))["sentence"]
    for part in ["PO-2611-001", "2026-11-20", "2026-11-19", "1일"]:
        assert part in s

def test_summary_on_sample(tmpdata):
    assert logic.lc_summary(storage.load_orders(tmpdata / "orders.csv")) == {"red": 1, "yellow": 2, "late_shipped": 1}

def test_summary_zero():
    assert logic.lc_summary([]) == {"red": 0, "yellow": 0, "late_shipped": 0}
