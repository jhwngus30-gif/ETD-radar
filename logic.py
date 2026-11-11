"""계산 · 입력 검사 (화면 코드 없음 — CLAUDE.md 규칙 3)
날짜 계산 함수는 now/today를 직접 받을 수 있다 (규칙 4)."""

import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

import config
import messages as M

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_FIELDS = ["order_no", "buyer", "item", "etd", "lc_ship_by"]


# ---------- 날짜 ----------
def now_korea(now=None):
    """한국 현재 시각. now(시간대 있는 datetime)를 주면 그것을 한국 시각으로 바꿔 쓴다."""
    tz = ZoneInfo(config.KOREA_TZ)
    if now is None:
        return datetime.now(tz)
    return now.astimezone(tz)


def today_korea(now=None):
    return now_korea(now).date()


def local_today(country, now=None):
    """바이어 국가의 오늘 날짜. 목록에 없는 국가면 None."""
    tz_name = config.BUYER_COUNTRIES.get(country or "")
    if not tz_name:
        return None
    base = now_korea(now)
    return base.astimezone(ZoneInfo(tz_name)).date()


def check_date(value, field):
    """날짜 글자를 검사한다. (date, None) 또는 (None, 에러문구)."""
    name = M.FIELD_NAMES.get(field, field)
    text = (value or "").strip()
    if not _DATE_RE.match(text):
        return None, M.ERR_DATE_FORMAT.format(field=name)
    try:
        return date.fromisoformat(text), None
    except ValueError:
        return None, M.ERR_DATE_INVALID.format(field=name, value=text)


# ---------- F1 등록 검사 ----------
def validate_new_order(fields, existing_order_nos):
    """새 오더 입력을 검사한다. 문제가 없으면 None, 있으면 한국어 에러 한 줄."""
    for f in REQUIRED_FIELDS:
        if not str(fields.get(f, "") or "").strip():
            return M.ERR_REQUIRED.format(field=M.FIELD_NAMES[f])
    order_no = fields["order_no"].strip()
    if order_no in {o.strip() for o in existing_order_nos}:
        return M.ERR_DUPLICATE.format(order_no=order_no)
    country = (fields.get("buyer_country") or "").strip()
    if country and country not in config.BUYER_COUNTRIES:
        return M.ERR_COUNTRY
    for f in ["etd", "lc_ship_by"]:
        _, err = check_date(fields[f], f)
        if err:
            return err
    if str(fields.get("eta", "") or "").strip():
        _, err = check_date(fields["eta"], "eta")
        if err:
            return err
    return None


def build_order(fields, now=None):
    """검사를 통과한 입력으로 저장할 오더 한 줄을 만든다."""
    return {
        "order_no": fields["order_no"].strip(),
        "buyer": fields["buyer"].strip(),
        "buyer_country": (fields.get("buyer_country") or "").strip(),
        "item": fields["item"].strip(),
        "etd": fields["etd"].strip(),
        "eta": (fields.get("eta") or "").strip(),
        "lc_ship_by": fields["lc_ship_by"].strip(),
        "status": config.STATUS_WAITING,
        "shipped_on": "",
        "created_at": now_korea(now).strftime("%Y-%m-%d %H:%M"),
        "deleted": "False",
    }


# ---------- F1 목록 ----------
def is_deleted(order):
    return str(order.get("deleted", "")).strip().lower() == "true"


def sort_orders(orders):
    """ETD가 빠른 순, ETD가 같으면 오더번호 순."""
    return sorted(orders, key=lambda o: (o.get("etd", ""), o.get("order_no", "")))


def active_orders(orders):
    return sort_orders([o for o in orders if not is_deleted(o)])


def deleted_orders(orders):
    return sort_orders([o for o in orders if is_deleted(o)])


# ---------- F1 선적 완료 ----------
def validate_shipped_on(value, now=None):
    """실제 선적일 검사. 비었음 · 형식 · 없는 날짜 · 미래 날짜면 에러 한 줄."""
    if not str(value or "").strip():
        return M.ERR_REQUIRED.format(field=M.FIELD_NAMES["shipped_on"])
    d, err = check_date(value, "shipped_on")
    if err:
        return err
    today = today_korea(now)
    if d > today:
        return M.ERR_SHIPPED_FUTURE.format(today=today.isoformat())
    return None


# ---------- F2 L/C 선적 기한 경고 ----------
def lc_status(order):
    """오더 하나의 L/C 기한 상태. {'level': red/yellow/green/ok, 'label', 'sentence', 'days'}"""
    lc = date.fromisoformat(order["lc_ship_by"])
    if order.get("status") == config.STATUS_SHIPPED and order.get("shipped_on"):
        shipped = date.fromisoformat(order["shipped_on"])
        late = (shipped - lc).days
        if late > 0:
            level, label = "red", "🔴 " + M.LC_SHIPPED_LATE.format(days=late)
        else:
            level, label = "ok", "✅ " + M.LC_SHIPPED_OK
        sentence = M.REPORT_SHIPPED.format(order_no=order["order_no"], shipped=order["shipped_on"],
                                           lc=order["lc_ship_by"], label=label[2:])
        return {"level": level, "label": label, "sentence": sentence, "days": late, "shipped": True}
    etd = date.fromisoformat(order["etd"])
    margin = (lc - etd).days  # 여유 일수 = L/C 기한 − ETD
    if margin < 0:
        level, label = "red", "🔴 " + M.LC_OVER.format(days=-margin)
    elif margin == 0:
        level, label = "yellow", "🟡 " + M.LC_SAME_DAY
    elif margin <= config.WARNING_DAYS:
        level, label = "yellow", "🟡 " + M.LC_LEFT.format(days=margin)
    else:
        level, label = "green", "🟢 " + M.LC_LEFT.format(days=margin)
    sentence = M.REPORT_WAITING.format(order_no=order["order_no"], etd=order["etd"],
                                       lc=order["lc_ship_by"], label=label[2:])
    return {"level": level, "label": label, "sentence": sentence, "days": margin, "shipped": False}


def lc_summary(orders):
    """삭제되지 않은 오더 기준 건수. 🔴·🟡는 선적 대기만, 기한 넘긴 선적은 따로."""
    red = yellow = late_shipped = 0
    for o in orders:
        if is_deleted(o):
            continue
        s = lc_status(o)
        if s["shipped"]:
            late_shipped += s["level"] == "red"
        elif s["level"] == "red":
            red += 1
        elif s["level"] == "yellow":
            yellow += 1
    return {"red": red, "yellow": yellow, "late_shipped": late_shipped}


# ---------- F3 ETD 변경 기록 ----------
def validate_etd_change(order, new_etd, reason):
    if order is None:
        return M.ERR_NO_ORDER
    if not str(reason or "").strip():
        return M.ERR_REASON
    d, err = check_date(new_etd, "etd")
    if err:
        return err
    if d.isoformat() == order["etd"]:
        return M.ERR_SAME_ETD.format(etd=order["etd"])
    return None


def build_change(order_no, old_etd, new_etd, reason, now=None):
    return {"order_no": order_no, "old_etd": old_etd, "new_etd": new_etd.strip(),
            "reason": reason.strip(), "changed_at": now_korea(now).strftime("%Y-%m-%d %H:%M")}


def etd_history(order, changes):
    """처음 ETD 대비 현재 ETD를 말로. 기록 0건이면 '변경 없음'."""
    mine = sorted([c for c in changes if c["order_no"] == order["order_no"]],
                  key=lambda c: c["changed_at"])
    n = len(mine)
    if n == 0:
        return M.HIST_NONE
    first = date.fromisoformat(mine[0]["old_etd"])
    diff = (date.fromisoformat(order["etd"]) - first).days
    if diff > 0:
        return M.HIST_LATER.format(days=diff, n=n)
    if diff < 0:
        return M.HIST_EARLIER.format(days=-diff, n=n)
    return M.HIST_SAME.format(n=n)


def plan_demo_updates(orders, demo_updates, now=None):
    """가상 선사 응답에서 바꿀 변경 목록과 건너뛴 건수를 계산한다 (파일은 안 건드림)."""
    by_no = {o["order_no"]: o for o in orders}
    changes, skipped = [], 0
    for u in demo_updates:
        o = by_no.get(u.get("order_no"))
        if o is None or is_deleted(o) or o.get("status") == config.STATUS_SHIPPED:
            skipped += 1
            continue
        _, err = check_date(u.get("new_etd"), "etd")
        if err:
            skipped += 1
            continue
        if u["new_etd"] == o["etd"]:
            continue
        changes.append(build_change(o["order_no"], o["etd"], u["new_etd"], M.DEMO_REASON, now))
    return changes, skipped
