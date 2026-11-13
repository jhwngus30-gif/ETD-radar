"""계산 · 입력 검사 (화면 코드 없음 — CLAUDE.md 규칙 3)
날짜 계산 함수는 now/today를 직접 받을 수 있다 (규칙 4)."""

import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

import config
import messages as M

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_FIELDS = ["order_no", "buyer", "item", "etd"]


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


def terms_of(order):
    """결제 조건 (예전 데이터처럼 비어 있으면 L/C)."""
    return (order.get("payment_terms") or config.DEFAULT_PAYMENT).strip()


def is_lc(order):
    return terms_of(order) == "L/C"


def port_of(order):
    return (order.get("port_of_loading") or config.DEFAULT_PORT).strip()


def is_third_country(order):
    """선적항이 한국이 아니면 삼국 간 거래."""
    info = config.PORTS.get(port_of(order))
    return bool(info) and info[0] != config.HOME_COUNTRY


def port_today(port, now=None):
    """선적항 현지 오늘 날짜. 목록에 없는 항구면 한국 오늘."""
    info = config.PORTS.get(port or config.DEFAULT_PORT)
    tz = info[1] if info else config.KOREA_TZ
    return now_korea(now).astimezone(ZoneInfo(tz)).date()


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
    terms = (fields.get("payment_terms") or "").strip()
    if terms not in config.PAYMENT_TERMS:
        return M.ERR_PAYMENT
    if (fields.get("port_of_loading") or "").strip() not in config.PORTS:
        return M.ERR_PORT
    if terms == "L/C" and not str(fields.get("lc_ship_by", "") or "").strip():
        return M.ERR_REQUIRED.format(field=M.FIELD_NAMES["lc_ship_by"])
    country = (fields.get("buyer_country") or "").strip()
    if country and country not in config.BUYER_COUNTRIES:
        return M.ERR_COUNTRY
    date_fields = ["etd", "lc_ship_by"] if terms == "L/C" else ["etd"]
    for f in date_fields:
        _, err = check_date(fields[f], f)
        if err:
            return err
    opt = ["eta", "cutoff"] + (["lc_expiry"] if terms == "L/C" else [])
    for f in opt:
        if str(fields.get(f, "") or "").strip():
            _, err = check_date(fields[f], f)
            if err:
                return err
    inco = str(fields.get("incoterms", "") or "").strip().upper()
    if inco and inco not in config.INCOTERMS:
        return M.ERR_INCOTERMS
    pdays = str(fields.get("lc_presentation_days", "") or "").strip()
    if terms == "L/C" and pdays and not (pdays.isdigit() and 1 <= int(pdays) <= 90):
        return M.ERR_PRESENT_DAYS
    for c in cross_check(fields):
        if c["level"] == "error":
            return c["msg"]
    return None


def build_order(fields, now=None):
    """검사를 통과한 입력으로 저장할 오더 한 줄을 만든다."""
    fields = {**fields,
              "payment_terms": (fields.get("payment_terms") or config.DEFAULT_PAYMENT),
              "port_of_loading": (fields.get("port_of_loading") or config.DEFAULT_PORT)}
    return {
        "order_no": fields["order_no"].strip(),
        "buyer": fields["buyer"].strip(),
        "buyer_country": (fields.get("buyer_country") or "").strip(),
        "item": fields["item"].strip(),
        "payment_terms": fields["payment_terms"].strip(),
        "port_of_loading": fields["port_of_loading"].strip(),
        "etd": fields["etd"].strip(),
        "eta": (fields.get("eta") or "").strip(),
        # T/T · D/P 는 L/C 기한을 저장하지 않는다 (F1-8)
        "lc_ship_by": (fields.get("lc_ship_by") or "").strip() if fields["payment_terms"].strip() == "L/C" else "",
        "status": config.STATUS_WAITING,
        "shipped_on": "",
        "created_at": now_korea(now).strftime("%Y-%m-%d %H:%M"),
        "deleted": "False",
        **_v32_fields(fields),
    }


def _v32_fields(fields):
    """v3.2 칸 정리: 인코텀즈는 대문자, L/C 원본 칸은 L/C일 때만 저장."""
    is_lc_terms = (fields.get("payment_terms") or "").strip() == "L/C"
    out = {}
    for k in config.V32_FIELDS:
        v = str(fields.get(k, "") or "").strip()
        if k == "incoterms":
            v = v.upper()
        if k in config.LC_ONLY_FIELDS and not is_lc_terms:
            v = ""
        out[k] = v
    return out


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
def validate_shipped_on(value, now=None, port=None):
    """실제 선적일 검사. 비었음 · 형식 · 없는 날짜 · (선적항 현지 오늘보다) 미래 날짜면 에러 한 줄."""
    if not str(value or "").strip():
        return M.ERR_REQUIRED.format(field=M.FIELD_NAMES["shipped_on"])
    d, err = check_date(value, "shipped_on")
    if err:
        return err
    today = port_today(port, now)
    if d > today:
        return M.ERR_SHIPPED_FUTURE.format(today=today.isoformat())
    return None


# ---------- v3.2 인코텀즈 · 입력 크로스체크 (F1-16, F7) ----------
def _norm(text):
    return re.sub(r"[^0-9a-z가-힣]", "", (text or "").lower())


def place_is_port(place, port):
    """'Busan, Korea' · '부산' · 'KRPUS' 를 모두 부산으로 본다."""
    n = _norm(place)
    if not n or port not in config.PORTS:
        return False
    return any(_norm(k) in n for k in (port, config.PORT_EN.get(port, ""), config.PORT_CODES.get(port, "")) if k)


def same_place(a, b):
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return True
    if na in nb or nb in na:
        return True
    for port in config.PORTS:                      # 한글 ↔ 영어 ↔ 코드
        if place_is_port(a, port) and place_is_port(b, port):
            return True
    return False


def booker(order):
    """누가 배를 잡는지 (F1-16)."""
    term = (order.get("incoterms") or "").strip().upper()
    if not term:
        return M.BOOKER_NONE
    return (M.BOOKER_BUYER if term in config.BUYER_BOOKS else M.BOOKER_SELLER).format(term=term)


def _d(value):
    try:
        return date.fromisoformat((value or "").strip())
    except ValueError:
        return None


def cross_check(order, others=None, now=None):
    """값끼리 서로 맞는지 본다 (F7). [{level: error|warn, kind, field, msg}]
    error = 저장 막음, warn = 저장하되 '입력 확인 필요' 표시. 날짜 형식 검사는 validate 쪽에서 한다."""
    out = []
    add = lambda level, kind, field, msg: out.append({"level": level, "kind": kind, "field": field, "msg": msg})
    g = lambda k: str(order.get(k, "") or "").strip()
    etd, eta, cutoff = _d(g("etd")), _d(g("eta")), _d(g("cutoff"))
    # 1. 날짜 순서
    if etd and eta:
        if eta < etd:
            add("error", "날짜", "eta", M.X_ETA_BEFORE.format(eta=g("eta"), etd=g("etd")))
        elif eta == etd:
            add("warn", "날짜", "eta", M.X_ETA_SAME)
        elif (eta - etd).days > config.MAX_TRANSIT_DAYS:
            add("warn", "날짜", "eta", M.X_TRANSIT_LONG.format(days=(eta - etd).days))
    if etd and cutoff:
        if cutoff > etd:
            add("error", "날짜", "cutoff", M.X_CUTOFF_AFTER.format(cutoff=g("cutoff"), etd=g("etd")))
        elif (etd - cutoff).days > config.MAX_CUTOFF_GAP_DAYS:
            add("warn", "날짜", "cutoff", M.X_CUTOFF_EARLY.format(days=(etd - cutoff).days))
    if etd and is_waiting(order):
        ahead = (etd - today_korea(now)).days
        if ahead > config.MAX_ETD_AHEAD_DAYS:
            add("warn", "날짜", "etd", M.X_ETD_FAR.format(days=ahead))
    # 2. L/C 원본 대조 (L/C만)
    if g("payment_terms") == "L/C":
        ship_by = _d(g("lc_ship_by"))
        if "lc_ship_by_confirm" in order and order["lc_ship_by_confirm"] is not None \
                and g("lc_ship_by_confirm") != g("lc_ship_by"):
            add("error", "L/C", "lc_ship_by", M.X_LC_CONFIRM.format(a=g("lc_ship_by"), b=g("lc_ship_by_confirm") or "빈칸"))
        exp = _d(g("lc_expiry"))
        if not g("lc_expiry"):
            add("warn", "L/C", "lc_expiry", M.X_EXPIRY_MISSING)
        elif exp and ship_by and exp < ship_by:
            add("error", "L/C", "lc_expiry", M.X_EXPIRY_BEFORE.format(exp=g("lc_expiry"), ship=g("lc_ship_by")))
        elif exp and ship_by:
            shipped = _d(g("shipped_on")) if g("status") == config.STATUS_SHIPPED else None
            base = shipped or ship_by
            need = int(g("lc_presentation_days")) if g("lc_presentation_days").isdigit() else config.LC_PRESENTATION_DEFAULT
            left = (exp - base).days
            if 0 <= left < need:
                add("warn", "L/C", "lc_expiry", M.X_PRESENT_SHORT.format(
                    base=("실제 선적일 " if shipped else "선적 기한 ") + base.isoformat(), days=left, need=need))
        lp = g("lc_port_loading")
        if lp and "any" not in lp.lower() and not place_is_port(lp, g("port_of_loading")):
            add("warn", "L/C", "lc_port_loading", M.X_44E.format(lc=lp, port=g("port_of_loading")))
        lpd, pod = g("lc_port_discharge"), g("port_of_discharge")
        if lpd and pod and "any" not in lpd.lower() and not same_place(lpd, pod):
            add("warn", "L/C", "lc_port_discharge", M.X_44F.format(lc=lpd, pod=pod))
    # 3. 인코텀즈 대조
    term, place, pod = g("incoterms").upper(), g("incoterms_place"), g("port_of_discharge")
    if not term:
        add("warn", "인코텀즈", "incoterms", M.X_INCO_MISSING)
    elif term not in config.INCOTERMS:
        add("error", "인코텀즈", "incoterms", M.ERR_INCOTERMS)
    elif place and term in config.PLACE_IS_LOADING and not place_is_port(place, g("port_of_loading")):
        add("warn", "인코텀즈", "incoterms_place", M.X_INCO_LOADING.format(term=term, place=place, port=g("port_of_loading")))
    elif place and pod and term in config.PLACE_IS_DISCHARGE and not same_place(place, pod):
        add("warn", "인코텀즈", "incoterms_place", M.X_INCO_DISCHARGE.format(term=term, place=place, pod=pod))
    # 5. 중복 (부킹 · B/L)
    if others:
        me = g("order_no")
        for f in ("booking_no", "bl_no"):
            v = g(f)
            if not v:
                continue
            hits = [o["order_no"] for o in others if o.get("order_no") != me and not is_deleted(o)
                    and (o.get(f) or "").strip().upper() == v.upper()]
            if hits:
                add("warn", "중복", f, M.X_DUP.format(field=M.FIELD_NAMES[f], value=v, others=", ".join(hits)))
    return out


def check_warnings(order, orders, now=None):
    """저장된 오더의 '입력 확인 필요' 목록 (warn만; 예전 데이터의 error도 함께 보여 줌)."""
    return cross_check(order, orders, now)


def check_alerts(orders, now=None):
    """대시보드용: 입력 확인이 필요한 오더들 [(오더, [항목])] (F7-6)."""
    act = active_orders(orders)
    out = []
    for o in act:
        c = check_warnings(o, act, now)
        if c:
            out.append({"order_no": o["order_no"], "order": o, "checks": c})
    return out


# ---------- F2 경고 (ETD 지남 · L/C 기한 · 서류 마감) ----------
def is_waiting(order):
    return order.get("status") != config.STATUS_SHIPPED


def etd_overdue_days(order, now=None):
    """선적 대기인데 ETD가 선적항 현지 오늘보다 앞이면 지난 일수, 아니면 0."""
    if not is_waiting(order):
        return 0
    d = (port_today(port_of(order), now) - date.fromisoformat(order["etd"])).days
    return d if d > 0 else 0


def lc_status(order, now=None):
    """오더 하나의 경고 상태. level: late/red/yellow/green/ok/na
    late(🚨 ETD 지남 미선적)는 모든 결제 조건에서 L/C 판정보다 먼저 본다 (F2-1)."""
    over = etd_overdue_days(order, now)
    if over:
        label = "🚨 " + M.LATE.format(days=over)
        sentence = M.REPORT_LATE.format(order_no=order["order_no"], etd=order["etd"], label=label[2:])
        return {"level": "late", "label": label, "sentence": sentence, "days": -over, "shipped": False}
    if not is_lc(order):
        shipped = not is_waiting(order)
        label = ("✅ " + M.LC_NA_SHIPPED if shipped else "⚪ " + M.LC_NA).format(terms=terms_of(order))
        sentence = M.REPORT_NA.format(order_no=order["order_no"], etd=order["etd"], label=label[2:])
        return {"level": "na", "label": label, "sentence": sentence, "days": None, "shipped": shipped}
    lc = date.fromisoformat(order["lc_ship_by"])
    if not is_waiting(order) and order.get("shipped_on"):
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
        level, label = "green", "🔵 " + M.LC_LEFT.format(days=margin)
    sentence = M.REPORT_WAITING.format(order_no=order["order_no"], etd=order["etd"],
                                       lc=order["lc_ship_by"], label=label[2:])
    return {"level": level, "label": label, "sentence": sentence, "days": margin, "shipped": False}


def cutoff_status(order, now=None):
    """서류 마감(Cut-off) 경고. 선적 대기 + 마감일 있음일 때만. 없으면 None (F2-5)."""
    if not is_waiting(order) or not (order.get("cutoff") or "").strip():
        return None
    left = (date.fromisoformat(order["cutoff"]) - port_today(port_of(order), now)).days
    if left < 0:
        return {"level": "red", "label": "🔴 " + M.CUTOFF_OVER.format(days=-left), "days": left}
    if left <= config.CUTOFF_WARN_DAYS:
        txt = M.CUTOFF_TODAY if left == 0 else M.CUTOFF_SOON.format(days=left)
        return {"level": "yellow", "label": "🟡 " + txt, "days": left}
    return None


def lc_summary(orders, now=None):
    """삭제되지 않은 오더 기준 건수.
    late = ETD 지남 미선적(모든 결제 조건), red·yellow = 선적 대기 L/C, late_shipped = 기한 넘겨 선적."""
    late = red = yellow = late_shipped = 0
    for o in orders:
        if is_deleted(o):
            continue
        s = lc_status(o, now)
        if s["level"] == "late":
            late += 1
        elif not is_lc(o):
            continue
        elif s["shipped"]:
            late_shipped += s["level"] == "red"
        elif s["level"] == "red":
            red += 1
        elif s["level"] == "yellow":
            yellow += 1
    return {"late": late, "red": red, "yellow": yellow, "late_shipped": late_shipped}


_RANK = {"late": 0, "red": 1, "yellow": 2}


def alerts(orders, now=None):
    """오늘 확인할 것 (F5): ETD 지남 · L/C 초과/임박 · 서류 마감 지남/임박, 위험한 순."""
    out = []
    for o in active_orders(orders):
        s = lc_status(o, now)
        if not s["shipped"] and s["level"] in _RANK:
            out.append({"order_no": o["order_no"], "level": s["level"], "label": s["label"], "order": o,
                        "key": (_RANK[s["level"]], s["days"] if s["days"] is not None else 0)})
        c = cutoff_status(o, now)
        if c:
            out.append({"order_no": o["order_no"], "level": c["level"], "label": c["label"], "order": o,
                        "key": (_RANK[c["level"]], c["days"])})
    out.sort(key=lambda x: x["key"])
    return out


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



# ---------- F4 보고 내보내기 · 불러오기 ----------
def _with_action(order, sentence):
    act = (order.get("action") or "").strip() or M.ACTION_NONE
    return sentence + M.ACTION_SUFFIX.format(action=act)


def report_text(orders, now=None):
    """보고 문장 전체: 머리말 + 🚨 → 🔴 → 🟡 문장, 끝에 대응 계획 (F4-1·2)."""
    summ = lc_summary(orders, now)
    head = M.REPORT_HEAD_V3.format(date=today_korea(now).isoformat(), late=summ["late"],
                                   red=summ["red"], yellow=summ["yellow"])
    risky = []
    for o in orders:
        if is_deleted(o):
            continue
        s = lc_status(o, now)
        if s["level"] == "late" or (is_lc(o) and not s["shipped"] and s["level"] in ("red", "yellow")):
            risky.append((o, s))
    risky.sort(key=lambda x: (_RANK[x[1]["level"]], x[1]["days"]))
    if not risky:
        return head + "\n" + M.REPORT_NONE
    return head + "\n" + "\n".join(
        f"{i}. {s['label'].split(' ', 1)[0]} {_with_action(o, s['sentence'])}" for i, (o, s) in enumerate(risky, 1))


EXPORT_COLUMNS = ["오더번호", "바이어", "바이어 국가", "품목", "결제 조건", "선적항", "삼국 간", "ETD", "ETA",
                  "L/C 선적 기한", "여유 일수", "경고", "상태", "실제 선적일", "선사", "선명/항차", "부킹번호",
                  "B/L 번호", "서류 마감일", "대응 계획", "인코텀즈", "인코텀즈 장소", "도착항", "L/C 유효기한",
                  "서류 제시 기간", "L/C 선적항(44E)", "L/C 도착항(44F)", "입력 확인", "ETD 변경", "보고 문장", "등록일"]
# 불러오기: CSV 칸 이름 → 저장 칸 (내보낸 한국어 이름과 orders.csv 영어 이름 모두 받음)
IMPORT_MAP = {"오더번호": "order_no", "바이어": "buyer", "바이어 국가": "buyer_country", "품목": "item",
              "결제 조건": "payment_terms", "선적항": "port_of_loading", "ETD": "etd", "ETA": "eta",
              "L/C 선적 기한": "lc_ship_by", "상태": "status", "실제 선적일": "shipped_on", "선사": "carrier",
              "선명/항차": "vessel", "부킹번호": "booking_no", "B/L 번호": "bl_no", "서류 마감일": "cutoff",
              "대응 계획": "action", "등록일": "created_at",
              "인코텀즈": "incoterms", "인코텀즈 장소": "incoterms_place", "도착항": "port_of_discharge",
              "L/C 유효기한": "lc_expiry", "서류 제시 기간": "lc_presentation_days",
              "L/C 선적항(44E)": "lc_port_loading", "L/C 도착항(44F)": "lc_port_discharge"}


def export_rows(orders, changes, now=None):
    """CSV로 내보낼 줄들 (삭제되지 않은 오더, ETD 빠른 순)."""
    rows = []
    act = active_orders(orders)
    for o in act:
        s = lc_status(o, now)
        margin = "" if s["days"] is None or s["shipped"] or s["level"] == "late" else s["days"]
        rows.append({
            "오더번호": o["order_no"], "바이어": o["buyer"], "바이어 국가": o.get("buyer_country", ""),
            "품목": o["item"], "결제 조건": terms_of(o), "선적항": port_of(o),
            "삼국 간": "예" if is_third_country(o) else "", "ETD": o["etd"], "ETA": o.get("eta", ""),
            "L/C 선적 기한": o.get("lc_ship_by", ""), "여유 일수": margin,
            "경고": s["label"][2:], "상태": o["status"], "실제 선적일": o.get("shipped_on", ""),
            "선사": o.get("carrier", ""), "선명/항차": o.get("vessel", ""), "부킹번호": o.get("booking_no", ""),
            "B/L 번호": o.get("bl_no", ""), "서류 마감일": o.get("cutoff", ""), "대응 계획": o.get("action", ""),
            "인코텀즈": o.get("incoterms", ""), "인코텀즈 장소": o.get("incoterms_place", ""),
            "도착항": o.get("port_of_discharge", ""), "L/C 유효기한": o.get("lc_expiry", ""),
            "서류 제시 기간": o.get("lc_presentation_days", ""), "L/C 선적항(44E)": o.get("lc_port_loading", ""),
            "L/C 도착항(44F)": o.get("lc_port_discharge", ""),
            "입력 확인": " / ".join(c["msg"] for c in check_warnings(o, act, now)),
            "ETD 변경": etd_history(o, changes), "보고 문장": s["sentence"], "등록일": o.get("created_at", ""),
        })
    return rows


def export_csv_bytes(orders, changes, now=None):
    """엑셀에서 한글이 깨지지 않게 UTF-8 BOM 을 붙인 CSV."""
    import csv, io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=EXPORT_COLUMNS)
    w.writeheader()
    w.writerows(export_rows(orders, changes, now))
    return buf.getvalue().encode("utf-8-sig")


def parse_import(text, existing_order_nos, now=None):
    """CSV 글자 → (추가할 오더들, 건너뛴 오더번호들, 오류[(줄, 이유)]). 파일은 안 건드림 (F4-4).
    이미 있는 오더번호는 덮어쓰지 않고 건너뛴다."""
    import csv, io
    text = text.lstrip("\ufeff")
    first = text.split("\n", 1)[0]
    delim = "\t" if "\t" in first else ","          # 엑셀에서 복사해 붙여 넣으면 탭으로 구분됨
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    if not reader.fieldnames or not ({"오더번호", "order_no"} & set(f.strip() for f in reader.fieldnames)):
        return [], [], [(1, M.IMPORT_NO_HEADER)]
    seen = {n.strip() for n in existing_order_nos}
    added, skipped, errors = [], [], []
    for line, row in enumerate(reader, start=2):
        f = {}
        for k, v in row.items():
            if k is None:
                continue
            key = IMPORT_MAP.get(k.strip(), k.strip())
            f[key] = (v or "").strip()
        if not any(f.values()):
            continue
        no = f.get("order_no", "")
        if no and no in seen:
            skipped.append(no)
            continue
        f.setdefault("payment_terms", config.DEFAULT_PAYMENT)
        f["payment_terms"] = f["payment_terms"] or config.DEFAULT_PAYMENT
        f["port_of_loading"] = f.get("port_of_loading") or config.DEFAULT_PORT
        err = validate_new_order(f, list(seen))
        if not err:
            for k in ("cutoff", "shipped_on"):
                if f.get(k):
                    _, err = check_date(f[k], k)
                    if err:
                        break
        if err:
            errors.append((line, err))
            continue
        o = build_order(f, now)
        for k in ("carrier", "vessel", "booking_no", "bl_no", "cutoff", "action", "created_at"):
            if f.get(k):
                o[k] = f[k]
        if f.get("status") == config.STATUS_SHIPPED and f.get("shipped_on"):
            o["status"], o["shipped_on"] = config.STATUS_SHIPPED, f["shipped_on"]
        added.append(o)
        seen.add(no)
    return added, skipped, errors


# ---------- 오더 수정 · 되돌리기 · 검색 (F1-10·11·12) ----------
def plan_edit(order, new_fields, reason, now=None):
    """수정 계획: (바뀐 칸 dict, ETD 변경 기록 or None, L/C 기한 기록 or None, 에러 or None). 파일은 안 건드림."""
    merged = {k: (order.get(k) or "") for k in config.EDITABLE}
    merged.update({k: v for k, v in order.items() if k not in merged})
    for k in config.EDITABLE:
        if k in new_fields:
            merged[k] = (new_fields[k] or "").strip()
    if merged["payment_terms"] != "L/C":
        for k in config.LC_ONLY_FIELDS:
            merged[k] = ""
    merged["incoterms"] = merged.get("incoterms", "").upper()
    check = {**merged, "order_no": "__edit__"}
    if "lc_ship_by_confirm" in new_fields and merged["lc_ship_by"] != (order.get("lc_ship_by") or ""):
        check["lc_ship_by_confirm"] = new_fields["lc_ship_by_confirm"] or ""
    err = validate_new_order(check, [])
    if not err:
        for k in ("cutoff",):
            if merged.get(k):
                _, err = check_date(merged[k], k)
                if err:
                    break
    if err:
        return {}, None, None, err
    diff = {k: merged[k] for k in config.EDITABLE if (order.get(k) or "") != merged[k]}
    if not diff:
        return {}, None, None, M.NO_CHANGE
    reason = (reason or "").strip()
    need = [M.FIELD_NAMES["etd"]] if "etd" in diff else []
    if "lc_ship_by" in diff and order.get("lc_ship_by") and merged["lc_ship_by"]:
        need.append(M.FIELD_LC)
    if need and not reason:
        return {}, None, None, M.ERR_EDIT_REASON.format(field=" · ".join(need))
    etd_ch = build_change(order["order_no"], order["etd"], merged["etd"], reason, now) if "etd" in diff else None
    lc_ch = None
    if "lc_ship_by" in diff:
        lc_ch = {"order_no": order["order_no"], "field": M.FIELD_LC, "old": order.get("lc_ship_by", ""),
                 "new": merged["lc_ship_by"], "reason": reason or "-",
                 "changed_at": now_korea(now).strftime("%Y-%m-%d %H:%M")}
    return diff, etd_ch, lc_ch, None


def plan_unship(order, now=None):
    """선적 완료 → 선적 대기 되돌리기: (바뀐 칸, 상태 기록)."""
    log = {"order_no": order["order_no"], "field": M.FIELD_STATUS,
           "old": f"{config.STATUS_SHIPPED} ({order.get('shipped_on', '')})", "new": config.STATUS_WAITING,
           "reason": M.UNSHIP_REASON, "changed_at": now_korea(now).strftime("%Y-%m-%d %H:%M")}
    return {"status": config.STATUS_WAITING, "shipped_on": ""}, log


def search_orders(orders, query):
    """오더번호 · 바이어 · 품목 · 부킹번호 · B/L 번호 부분 일치, 대소문자 무시."""
    q = (query or "").strip().lower()
    if not q:
        return list(orders)
    keys = ("order_no", "buyer", "item", "booking_no", "bl_no")
    return [o for o in orders if any(q in (o.get(k) or "").lower() for k in keys)]


# ---------- F6 화면 날짜 표기 ----------
_WD = "월화수목금토일"


def fmt_date(iso, today=None):
    """화면용 날짜: 올해면 '11/20 (금)', 아니면 '2027-01-05'. 빈칸이면 '—'."""
    if not iso:
        return "—"
    d = date.fromisoformat(iso)
    year = (today or today_korea()).year
    if d.year != year:
        return d.isoformat()
    return f"{d.month}/{d.day} ({_WD[d.weekday()]})"



# ---------- v3.1 일괄 등록 양식 · 선사 연동 시뮬레이션 ----------
def template_csv_bytes():
    """일괄 등록용 빈 양식 (칸 이름만, 엑셀용 BOM)."""
    return (",".join(config.TEMPLATE_COLUMNS) + "\r\n").encode("utf-8-sig")


def simulate_carrier_query(order, demo_updates, now=None):
    """실제 선사 연동이 움직이는 순서를 단계별로 재현한다 (파일은 안 건드림, PRD F3-6).
    반환: {ok, steps[], request, response, new_etd, change(or None), error}"""
    key, key_name, ref = (order.get("booking_no") or "").strip(), "부킹번호", "carrierBookingReference"
    if not key:
        key, key_name, ref = (order.get("bl_no") or "").strip(), "B/L 번호", "transportDocumentReference"
    if not key:
        return {"ok": False, "steps": [], "error": M.SIM_NO_KEY}
    carrier = (order.get("carrier") or "").strip() or "미지정"
    url = f"{config.DEMO_API}?{ref}={key}&eventType=TRANSPORT"
    upd = next((u for u in demo_updates if u.get("order_no") == order["order_no"]), None)
    new_etd = upd["new_etd"] if upd and check_date(upd.get("new_etd"), "etd")[1] is None else order["etd"]
    port = port_of(order)
    tz = ZoneInfo(config.PORTS.get(port, (None, config.KOREA_TZ))[1])
    dt = datetime.fromisoformat(new_etd + "T18:00:00").replace(tzinfo=tz).isoformat()
    vessel = (order.get("vessel") or "").strip() or "DEMO VESSEL 001E"
    response = {
        "_note": "가상 응답 (DCSA Track & Trace 형식 참고) — 실제 선사와 연결되지 않음",
        ref: key,
        "carrierCode": carrier,
        "events": [{
            "eventType": "TRANSPORT",
            "transportEventTypeCode": "DEPA",           # 출항
            "eventClassifierCode": "EST",                # 예정(Estimated)
            "eventDateTime": dt,
            "transportCall": {"UNLocationCode": config.PORT_CODES.get(port, ""), "vessel": {"vesselName": vessel}},
        }],
    }
    diff = (date.fromisoformat(new_etd) - date.fromisoformat(order["etd"])).days
    words = f"{diff}일 늦어짐" if diff > 0 else f"{-diff}일 앞당겨짐"
    steps = [M.SIM_STEP1.format(key_name=key_name, key=key, carrier=carrier),
             M.SIM_STEP2.format(url=url),
             M.SIM_STEP3.format(etd=new_etd, vessel=vessel),
             M.SIM_STEP4_CHANGED.format(old=order["etd"], new=new_etd, words=words) if diff else M.SIM_STEP4_SAME.format(old=order["etd"])]
    change = build_change(order["order_no"], order["etd"], new_etd, M.DEMO_REASON, now) if diff else None
    return {"ok": True, "steps": steps, "request": {"method": "GET", "url": url}, "response": response,
            "new_etd": new_etd, "change": change, "error": None}



# ---------- F5-3 일정 캘린더 ----------
CAL_KINDS = ["ETD", "L/C", "마감", "ETA", "선적"]


def calendar_events(orders, now=None):
    """달력에 올릴 일정: {date, kind, order_no, level, title}. 삭제된 오더 제외, 날짜순.
    선적 완료 오더는 실제 선적일 · ETA만, 색(level)은 그 오더의 경고 상태를 따른다."""
    out = []
    for o in active_orders(orders):
        level = lc_status(o, now)["level"]
        if is_waiting(o):
            pairs = [("ETD", o.get("etd")), ("L/C", o.get("lc_ship_by")), ("마감", o.get("cutoff")), ("ETA", o.get("eta"))]
        else:
            pairs = [("선적", o.get("shipped_on")), ("ETA", o.get("eta"))]
        for kind, d in pairs:
            if d:
                out.append({"date": d, "kind": kind, "order_no": o["order_no"], "level": level,
                            "title": f"{kind} {o['order_no']}"})
    out.sort(key=lambda e: (e["date"], CAL_KINDS.index(e["kind"]), e["order_no"]))
    return out


def month_grid(year, month):
    """월간 달력 칸: 주(월~일) 단위 날짜 목록. 앞뒤 달 날짜도 채운다."""
    import calendar
    return calendar.Calendar(firstweekday=6).monthdatescalendar(year, month)   # 일요일 시작
