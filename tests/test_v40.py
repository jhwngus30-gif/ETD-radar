"""v4.0 — 메일에서 가져오기 (F8)."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

import logic
import messages as M
import storage

NOW = datetime(2026, 11, 13, 15, 0, tzinfo=ZoneInfo("Asia/Seoul"))
TODAY = date(2026, 11, 13)


def test_date_formats():
    t = "2026-11-28 / 28-Nov-2026 / Nov 28, 2026 / 28 Nov / Nov 28th / 11/28 / 28/11"
    assert set(logic.mail_dates(t, TODAY)) == {date(2026, 11, 28)}
    assert logic.mail_dates("Oct 20", TODAY) == [date(2026, 10, 20)]        # 연도 없고 반년 안 → 올해
    assert logic.mail_dates("ETA: Jan 2", TODAY) == [date(2027, 1, 2)]      # 반년 넘게 지난 날 → 내년
    assert logic.mail_dates("2026-02-30", TODAY) == []                       # 없는 날짜


def test_rollover_mail():
    p = logic.parse_mail(M.DEMO_MAILS[0][1], NOW)
    assert (p["order_no"], p["booking_no"], p["etd_old"], p["etd"], p["eta"]) == \
        ("PO-2611-004", "SKBK4410", "2026-11-17", "2026-11-24", "2026-11-26")
    assert p["status"] == "ETD 변경(롤오버)" and p["vessel"] == "SINOKOR TOKYO 212N" and p["bl_no"] == ""


def test_old_new_lines_and_missing_values():
    p = logic.parse_mail("PO-2611-001\nOriginal ETD: 20 Nov\nNew ETD: 27 Nov", NOW)
    assert (p["etd_old"], p["etd"], p["eta"], p["bl_no"], p["vessel"]) == ("2026-11-20", "2026-11-27", "", "", "")
    p2 = logic.parse_mail("Please find the B/L issued for your shipment.", NOW)   # 번호 없는 B/L 문구
    assert p2["bl_no"] == "" and p2["order_no"] == ""


def test_plan_updates_existing_order(tmpdata):
    o = storage.load_orders(tmpdata / "orders.csv")
    pl = logic.plan_mail_update(logic.parse_mail(M.DEMO_MAILS[0][1], NOW), o, NOW)
    assert pl["error"] is None and pl["by"] == "order_no"
    assert pl["diff"] == {"etd": "2026-11-24", "eta": "2026-11-26", "vessel": "SINOKOR TOKYO 212N"}
    assert pl["etd_change"]["old_etd"] == "2026-11-17" and pl["etd_change"]["reason"] == "메일: ETD 변경(롤오버)"


def test_match_by_booking_and_bl(tmpdata):
    o = storage.load_orders(tmpdata / "orders.csv")
    pl = logic.plan_mail_update(logic.parse_mail("Booking No: HLBK55021\nETA: 30 Dec 2026", NOW), o, NOW)
    assert pl["match"]["order_no"] == "PO-2611-002" and pl["by"] == "booking_no" and pl["diff"] == {"eta": "2026-12-30"}


def test_no_match_new_order_and_nothing(tmpdata):
    o = storage.load_orders(tmpdata / "orders.csv")
    p = logic.parse_mail(M.DEMO_MAILS[2][1], NOW)
    pl = logic.plan_mail_update(p, o, NOW)
    assert pl["match"] is None and pl["error"] == M.MAIL_NO_MATCH
    f = logic.mail_new_order_fields(p)
    assert f["port_of_loading"] == "부산" and f["port_of_discharge"] == "Rotterdam" and f["etd"] == "2026-12-03"
    assert logic.plan_mail_update(logic.parse_mail("안녕하세요", NOW), o, NOW)["error"] == M.MAIL_NOTHING


def test_cross_check_blocks_bad_mail(tmpdata):
    o = storage.load_orders(tmpdata / "orders.csv")
    pl = logic.plan_mail_update(logic.parse_mail("PO-2611-004\nETD: 2026-11-30\nETA: 2026-11-20", NOW), o, NOW)
    assert pl["error"] and "ETA" in pl["error"]                    # F7: ETA < ETD 는 반영 막음


def test_pol_mismatch_note(tmpdata):
    o = storage.load_orders(tmpdata / "orders.csv")
    pl = logic.plan_mail_update(logic.parse_mail("PO-2611-004\nPOL: Incheon\nETA: 2026-11-27", NOW), o, NOW)
    assert pl["notes"] and "Incheon" in pl["notes"][0] and "port_of_loading" not in pl["diff"]
