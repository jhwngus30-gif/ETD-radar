"""ETD 레이더 — Streamlit 화면 (PRD v3: F1~F6). 계산은 logic.py, 파일은 storage.py에서 한다."""

from datetime import date

import config
import logic
import messages as M
import storage

# 브라우저 탭 제목에 확인할 건수 (F5-2) — set_page_config 전에 데이터를 읽는다
try:
    orders = storage.load_orders()
    changes = storage.load_changes()
    change_log = storage.load_change_log()
    load_error = None
except Exception:
    orders, changes, change_log, load_error = [], [], [], M.ERR_FILE.format(path=config.ORDERS_FILE)

import streamlit as st

alerts = logic.alerts(orders)
st.set_page_config(page_title=(f"({len(alerts)}) " if alerts else "") + "ETD 레이더", page_icon="📡", layout="wide")
if load_error:
    st.error(load_error)
    st.stop()

ss = st.session_state
for k, v in {"pending_delete": None, "pending_unship": None, "flash": None, "open_order": None,
             "show_guide": True, "import_plan": None, "sim_order": None, "cal_ym": None}.items():
    ss.setdefault(k, v)

today = logic.today_korea()
fd = lambda iso: logic.fmt_date(iso, today)
LEVEL_COLOR = {"late": "red", "red": "red", "yellow": "orange", "green": "blue", "ok": "violet", "na": "gray"}


def badge(label, level):
    """색 배지 (이모지 없이 색으로 뜻 표시 — F6-6)."""
    return f":{LEVEL_COLOR.get(level, 'gray')}-background[{label.split(' ', 1)[1] if ' ' in label else label}]"


def date_text(key, label, value="", help=None):
    """달력 입력 (F1-14). 저장 형식은 YYYY-MM-DD."""
    v = date.fromisoformat(value) if value else None
    d = st.date_input(label, value=v, key=key, format="YYYY-MM-DD", help=help)
    return d.isoformat() if d else ""


def v32_inputs(prefix, o=None, edit=False):
    """인코텀즈 · L/C 원본 칸 (F1-16 · 17). L/C 칸에는 MT700 칸 번호를 붙여 원본을 보며 옮겨 적게 한다."""
    o = o or {}
    opts = [""] + config.INCOTERMS
    i1, i2, i3 = st.columns(3)
    out = {"incoterms": i1.selectbox("인코텀즈", opts, index=opts.index((o.get("incoterms") or "").upper())
                                     if (o.get("incoterms") or "").upper() in opts else 0, key=f"{prefix}_inco",
                                     help="EXW · FCA · FAS · FOB = 바이어 측 포워더가 부킹 / C · D 조건 = 우리가 부킹"),
           "incoterms_place": i2.text_input("인코텀즈 지정 장소", o.get("incoterms_place", ""), key=f"{prefix}_place",
                                            placeholder="FOB → 선적항(Busan) · CIF → 도착항"),
           "port_of_discharge": i3.text_input("도착항", o.get("port_of_discharge", ""), key=f"{prefix}_pod",
                                              placeholder="예: Hamburg")}
    st.caption("L/C일 때만 — L/C 원본(MT700)의 칸 번호를 보며 그대로 옮겨 적어 주세요.")
    l1, l2, l3 = st.columns(3)
    with l1:
        out["lc_ship_by_confirm"] = date_text(f"{prefix}_lcc", "44C 선적 기한 한 번 더 *" if not edit
                                              else "44C 선적 기한 한 번 더 (기한을 바꿀 때)")
    with l2:
        out["lc_expiry"] = date_text(f"{prefix}_exp", "31D L/C 유효기한", o.get("lc_expiry", ""))
    out["lc_presentation_days"] = l3.text_input("48 서류 제시 기간(일)", o.get("lc_presentation_days", ""),
                                                key=f"{prefix}_pd", placeholder="비우면 21일 (UCP 600)")
    out["lc_port_loading"] = l1.text_input("44E 선적항", o.get("lc_port_loading", ""), key=f"{prefix}_44e",
                                           placeholder="예: Busan, Korea / Any Korean port")
    out["lc_port_discharge"] = l2.text_input("44F 도착항", o.get("lc_port_discharge", ""), key=f"{prefix}_44f")
    return out


def show_checks(checks):
    """입력 확인 필요 목록 (F7)."""
    if checks:
        st.warning(f"**{M.CHECK_TITLE} {len(checks)}건**  \n" + "  \n".join(f"· [{c['kind']}] {c['msg']}" for c in checks))


def import_preview(text, key):
    """CSV · 엑셀 붙여넣기 공통: 미리보기 → 확인해야 반영 (F1-15 · F4-4)."""
    added, skipped, errors = logic.parse_import(text, [o["order_no"] for o in orders])
    st.write(M.IMPORT_RESULT.format(added=len(added), skipped=len(skipped), errors=len(errors)) + " (미리보기)")
    for line, why in errors:
        st.error(M.IMPORT_ERR_LINE.format(line=line, reason=why))
    if added:
        pool = logic.active_orders(orders) + added
        st.dataframe([{"오더번호": a["order_no"], "바이어": a["buyer"], "결제 조건": a["payment_terms"],
                       "인코텀즈": a.get("incoterms", ""), "선적항": a["port_of_loading"], "ETD": a["etd"],
                       "입력 확인": " / ".join(c["msg"] for c in logic.check_warnings(a, pool)) or "—"}
                      for a in added], hide_index=True)
        if st.button(f"{len(added)}건 추가하기", type="primary", key=f"imp_yes_{key}"):
            storage.add_orders(added)
            ss.flash = M.IMPORT_RESULT.format(added=len(added), skipped=len(skipped), errors=len(errors))
            st.rerun()
    elif not errors:
        st.info(M.IMPORT_EMPTY)


st.title(M.APP_TITLE)
st.caption(M.APP_SUBTITLE + f" · 오늘(한국) {fd(today.isoformat())}")
if ss.flash:
    st.success(ss.flash)
    ss.flash = None

active = logic.active_orders(orders)
checks_by = {x["order_no"]: x["checks"] for x in logic.check_alerts(orders)}

# ---------- 처음 쓰는 사람 안내 (F6-8) ----------
if ss.show_guide:
    with st.container(border=True):
        g1, g2 = st.columns([10, 1])
        g1.markdown("**처음이신가요?** ① 새 오더 등록 → ② 선적 현황에서 캘린더 · 위험 확인 → ③ ETD가 바뀌면 변경 기록 → ④ 보고 내보내기로 상사에게 보고  \n"
                    "**여유 일수** = L/C 선적 기한 − ETD. **7일 이하면 임박** — 정기선은 주 1회 운항이 많아 롤오버 한 번에 약 1주가 밀리기 때문이에요.")
        if g2.button("닫기", key="guide_close"):
            ss.show_guide = False
            st.rerun()

tab_dash, tab_orders, tab_new, tab_mail, tab_log, tab_report = st.tabs(
    ["선적 현황", f"오더 목록 ({len(active)})", "새 오더 등록", "메일 가져오기", "변경 기록", "보고 내보내기"])

# ======================= 선적 현황 (홈) =======================
with tab_dash:
    summ = logic.lc_summary(orders)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ETD 지남 · 선적 미확인", summ["late"])
    c2.metric("L/C 기한 초과", summ["red"])
    c3.metric("L/C 임박 (7일 이내)", summ["yellow"])
    c4.metric("기한 넘겨 선적", summ["late_shipped"])
    # v3.3: 캘린더를 넓게, 오늘 확인할 것은 오른쪽 (F6-9)
    cal_col, side_col = st.columns([3, 1])
    with cal_col:
        # 일정 캘린더 (F5-3)
        with st.container(border=True):
            ym = ss.get("cal_ym") or (today.year, today.month)
            h1, h2, h3, h4 = st.columns([3, 1, 1, 1])
            h1.markdown(f"**일정 캘린더 — {ym[0]}년 {ym[1]}월**")
            if h2.button("◀ 이전 달", key="cal_prev"):
                ss.cal_ym = (ym[0] - 1, 12) if ym[1] == 1 else (ym[0], ym[1] - 1); st.rerun()
            if h3.button("오늘", key="cal_today"):
                ss.cal_ym = (today.year, today.month); st.rerun()
            if h4.button("다음 달 ▶", key="cal_next"):
                ss.cal_ym = (ym[0] + 1, 1) if ym[1] == 12 else (ym[0], ym[1] + 1); st.rerun()
            kinds = st.multiselect("보이는 일정", logic.CAL_KINDS, default=logic.CAL_KINDS, key="cal_kinds")
            events = [e for e in logic.calendar_events(orders) if e["kind"] in kinds]
            by_day = {}
            for e in events:
                by_day.setdefault(e["date"], []).append(e)
            if st.toggle("목록으로 보기 (다가오는 일정)", key="cal_list"):
                upcoming = [e for e in events if e["date"] >= today.isoformat()][:30]
                if not upcoming:
                    st.write("다가오는 일정이 없어요.")
                for e in upcoming:
                    st.markdown(f"**{fd(e['date'])}** · {badge('x ' + e['title'], e['level'])}")
            else:
                head = st.columns(7)
                for c, w in zip(head, "일월화수목금토"):
                    c.markdown(f"**{w}**")
                for week in logic.month_grid(*ym):
                    cols = st.columns(7)
                    for c, d in zip(cols, week):
                        day = d.isoformat()
                        num = f"{d.day}" if d.month == ym[1] else f":gray[{d.month}/{d.day}]"
                        lines = [f":violet-background[**{num} 오늘**]" if d == today else f"**{num}**"]
                        evs = by_day.get(day, [])
                        lines += [badge("x " + e["title"], e["level"]) for e in evs[:3]]
                        if len(evs) > 3:
                            lines.append(f":gray[+{len(evs) - 3}]")
                        c.markdown("  \n".join(lines))
    with side_col:
        # 오늘 확인할 것 — 결정 카드 (F5-1, v3.4)
        cards = logic.decision_cards(orders)
        st.markdown(f"**{M.ALERTS_TITLE}** · 오더 {len(cards)}건")
        if not cards:
            st.write(M.ALERTS_NONE)
        for c in cards:
            o, no = c["order"], c["order_no"]
            with st.container(border=True):
                st.markdown(" ".join(badge(i["label"], i["level"]) for i in c["issues"]))
                st.markdown(f"**{o['buyer']}** · {o['item']}  \n:gray[{no} · {logic.terms_of(o)} · ETD {fd(o['etd'])}"
                            + (f" · L/C {fd(o.get('lc_ship_by'))}" if logic.is_lc(o) else "") + "]")
                st.markdown("**할 일** " + "  \n".join(c["steps"]) + f"  \n**연락** {' · '.join(c['contacts'])}"
                            + f"  \n**계획** {c['plan'] or ':red[(미정)]'}")
                with st.popover("대응 계획 " + ("고치기" if c["plan"] else "적기")):
                    plan = st.text_input("대응 계획", c["plan"], key=f"plan_{no}", placeholder="예: 바이어에 L/C 연장 요청 메일 발송")
                    if st.button("저장", key=f"plansave_{no}"):
                        storage.update_order(no, {"action": plan.strip()})
                        ss.flash, ss.open_order = f"{no} 대응 계획을 저장했어요.", no
                        st.rerun()
        if checks_by:  # F7-6
            with st.container(border=True):
                st.markdown(f":gray-background[{M.CHECK_ALERT.format(n=len(checks_by))}]")
                for n, cs in checks_by.items():
                    o = next(x for x in active if x["order_no"] == n)
                    st.markdown(f"**{o['buyer']}** :gray[{o['item'].split(' ')[0]}] — {cs[0]['short']}"
                                + (f" 외 {len(cs) - 1}" if len(cs) > 1 else ""))

    # 여유 일수 상위 8건 (F6-3)
    rows = []
    for o in active:
        s = logic.lc_status(o)
        if logic.is_waiting(o) and logic.is_lc(o) and s["level"] != "late":
            rows.append((s["days"], o, s))
    rows.sort(key=lambda x: x[0])
    st.markdown("**L/C 선적 기한까지 여유** (위험한 순)")
    show = rows if st.toggle(f"전부 보기 ({len(rows)}건)", key="all_margin") else rows[:8]
    for m, o, s in show:
        st.markdown(f"{badge(s['label'], s['level'])} **{o['order_no']}** · ETD {fd(o['etd'])} → L/C {fd(o['lc_ship_by'])}")
    if len(rows) > 8 and len(show) == 8:
        st.caption(f"나머지 {len(rows) - 8}건은 '전부 보기'로 펼쳐요.")

# ======================= 오더 목록 =======================
with tab_orders:
    f1, f2 = st.columns([2, 1])
    q = f1.text_input("검색 (오더번호 · 바이어 · 품목 · 부킹번호 · B/L 번호)", key="q")
    filt = f2.selectbox("상태", ["전체", "ETD 지남", "L/C 초과", "L/C 임박", "여유", "선적 완료", "L/C 외"], key="filt")
    want = {"ETD 지남": "late", "L/C 초과": "red", "L/C 임박": "yellow", "여유": "green", "L/C 외": "na"}
    shown = []
    for o in logic.search_orders(active, q):
        s = logic.lc_status(o)
        if filt == "선적 완료" and not s["shipped"]:
            continue
        if filt in want and (s["shipped"] or s["level"] != want[filt]):
            continue
        shown.append((o, s))
    if not active:
        st.info(M.EMPTY_ORDERS)
    elif not shown:
        st.info(M.SEARCH_EMPTY)
    for o, s in shown:
        no = o["order_no"]
        third = f" · {M.THIRD_COUNTRY}" if logic.is_third_country(o) else ""
        cut = logic.cutoff_status(o)
        title = (f"**{no}** · {o['buyer']}  |  {logic.terms_of(o)} · {logic.port_of(o)}{third}  |  "
                 f"ETD {fd(o['etd'])}  |  L/C {fd(o.get('lc_ship_by'))}  |  {badge(s['label'], s['level'])}"
                 + (f" {badge(cut['label'], cut['level'])}" if cut else "")
                 + (f" :gray-background[입력 확인 {len(checks_by[no])}]" if no in checks_by else ""))
        with st.expander(title, expanded=(ss.open_order == no)):
            d1, d2, d3 = st.columns(3)
            d1.markdown(f"**품목** {o['item']}  \n**바이어 국가** {o.get('buyer_country') or '—'}  \n**ETA** {fd(o.get('eta'))}")
            d2.markdown(f"**선사** {o.get('carrier') or '—'}  \n**선명/항차** {o.get('vessel') or '—'}  \n"
                        f"**부킹번호** {o.get('booking_no') or '—'}  \n**B/L 번호** {o.get('bl_no') or '—'}")
            d3.markdown(f"**서류 마감일** {fd(o.get('cutoff'))}  \n**상태** {o['status']}"
                        + (f" ({fd(o['shipped_on'])})" if o.get("shipped_on") else "")
                        + f"  \n**ETD 변경** {logic.etd_history(o, changes)}  \n**대응 계획** {o.get('action') or '(미정)'}")
            st.markdown(f"**인코텀즈** {((o.get('incoterms') or '—') + ' ' + (o.get('incoterms_place') or '')).strip()}"
                        f"  ·  **도착항** {o.get('port_of_discharge') or '—'}  \n**부킹 담당** {logic.booker(o)}")
            if logic.is_lc(o):
                st.markdown(f"**L/C 원본** 44C 선적 기한 {fd(o.get('lc_ship_by'))} · 31D 유효기한 {fd(o.get('lc_expiry'))}"
                            f" · 48 제시 기간 {o.get('lc_presentation_days') or '21(기본)'}일"
                            f" · 44E {o.get('lc_port_loading') or '—'} · 44F {o.get('lc_port_discharge') or '—'}")
            show_checks(checks_by.get(no))
            if logic.is_third_country(o):
                st.caption(M.TODAY_PORT.format(port=logic.port_of(o), date=fd(logic.port_today(logic.port_of(o)).isoformat())))
            if o.get("buyer_country") in config.BUYER_COUNTRIES:
                st.caption(M.TODAY_LOCAL.format(country=o["buyer_country"], date=fd(logic.local_today(o["buyer_country"]).isoformat())))

            act_edit, act_ship, act_del = st.tabs(["수정", "선적 완료 / 되돌리기", "삭제"])
            with act_edit:  # F1-10
                with st.form(f"edit_{no}"):
                    e1, e2, e3 = st.columns(3)
                    new = {
                        "buyer": e1.text_input("바이어 *", o["buyer"]),
                        "item": e2.text_input("품목 *", o["item"]),
                        "buyer_country": e3.selectbox("바이어 국가", [""] + list(config.BUYER_COUNTRIES),
                                                      index=([""] + list(config.BUYER_COUNTRIES)).index(o.get("buyer_country") or "")),
                        "payment_terms": e1.selectbox("결제 조건 *", config.PAYMENT_TERMS, index=config.PAYMENT_TERMS.index(logic.terms_of(o))),
                        "port_of_loading": e2.selectbox("선적항 *", list(config.PORTS), index=list(config.PORTS).index(logic.port_of(o))),
                    }
                    with e3:
                        new["etd"] = date_text(f"etd_{no}", "ETD *", o["etd"])
                    with e1:
                        new["lc_ship_by"] = date_text(f"lc_{no}", "L/C 선적 기한 (L/C일 때)", o.get("lc_ship_by", ""))
                    with e2:
                        new["eta"] = date_text(f"eta_{no}", "ETA", o.get("eta", ""))
                    with e3:
                        new["cutoff"] = date_text(f"cut_{no}", "서류 마감일", o.get("cutoff", ""))
                    new["carrier"] = e1.text_input("선사", o.get("carrier", ""))
                    new["vessel"] = e2.text_input("선명/항차", o.get("vessel", ""))
                    new["booking_no"] = e3.text_input("부킹번호", o.get("booking_no", ""))
                    new["bl_no"] = e1.text_input("B/L 번호", o.get("bl_no", ""))
                    new["action"] = e2.text_input("대응 계획", o.get("action", ""), placeholder="예: L/C 연장 요청")
                    new.update(v32_inputs(f"e_{no}", o, edit=True))
                    reason = st.text_input("ETD · L/C 기한을 바꾼 사유", placeholder="예: L/C 연장(Amendment)")
                    go = st.form_submit_button("수정 저장")
                if go:
                    diff, etd_ch, lc_ch, err = logic.plan_edit(o, new, reason)
                    if err:
                        st.error(err)
                    else:
                        storage.update_order(no, diff)
                        if etd_ch:
                            storage.append_change(etd_ch)
                        if lc_ch:
                            storage.append_change_log(lc_ch)
                        ss.flash, ss.open_order = M.EDITED.format(order_no=no), no
                        st.rerun()
            with act_ship:  # F1-7 · F1-11
                if logic.is_waiting(o):
                    with st.form(f"ship_{no}"):
                        sd = date_text(f"sd_{no}", M.SHIP_PROMPT.format(order_no=no))
                        ok = st.form_submit_button(M.SHIP_SAVE)
                    if ok:
                        err = logic.validate_shipped_on(sd, port=logic.port_of(o))
                        if err:
                            st.error(err)
                        else:
                            storage.mark_shipped(no, sd)
                            ss.flash, ss.open_order = M.SHIPPED.format(order_no=no, date=sd), no
                            st.rerun()
                elif ss.pending_unship == no:
                    st.warning(M.UNSHIP_CONFIRM.format(order_no=no, date=o.get("shipped_on", "")))
                    y, n_ = st.columns(2)
                    if y.button("네, 되돌릴게요", key=f"unyes_{no}"):
                        ch, log = logic.plan_unship(o)
                        storage.update_order(no, ch)
                        storage.append_change_log(log)
                        ss.pending_unship, ss.flash, ss.open_order = None, M.UNSHIPPED.format(order_no=no), no
                        st.rerun()
                    if n_.button("취소", key=f"unno_{no}"):
                        ss.pending_unship = None
                        st.rerun()
                elif st.button("선적 대기로 되돌리기", key=f"unship_{no}"):
                    ss.pending_unship = no
                    st.rerun()
            with act_del:  # F1-4
                if ss.pending_delete == no:
                    st.warning(M.DELETE_CONFIRM.format(order_no=no))
                    y, n_ = st.columns(2)
                    if y.button(M.DELETE_YES, key=f"yes_{no}"):
                        storage.set_deleted(no, True)
                        ss.pending_delete, ss.flash = None, M.DELETED.format(order_no=no)
                        st.rerun()
                    if n_.button(M.DELETE_NO, key=f"no_{no}"):
                        ss.pending_delete = None
                        st.rerun()
                elif st.button(M.DELETE_BUTTON, key=f"del_{no}"):
                    ss.pending_delete = no
                    st.rerun()

    with st.expander(M.DELETED_TITLE):  # F1-6
        gone = logic.deleted_orders(orders)
        if not gone:
            st.write(M.NO_DELETED)
        for o in gone:
            c = st.columns([2, 2, 2, 1])
            c[0].write(o["order_no"]); c[1].write(o["buyer"]); c[2].write(f"ETD {fd(o['etd'])}")
            if c[3].button(M.RESTORE_BUTTON, key=f"restore_{o['order_no']}"):
                storage.set_deleted(o["order_no"], False)
                ss.flash = M.RESTORED.format(order_no=o["order_no"])
                st.rerun()

# ======================= 새 오더 등록 =======================
with tab_new:
    with st.form("new_order"):
        c1, c2, c3 = st.columns(3)
        fields = {
            "order_no": c1.text_input("오더번호 *", placeholder="PO-2611-015"),
            "buyer": c2.text_input("바이어 *", placeholder="가상 회사명"),
            "buyer_country": c3.selectbox("바이어 국가", [""] + list(config.BUYER_COUNTRIES)),
            "item": c1.text_input("품목 *"),
            "payment_terms": c2.selectbox("결제 조건 *", config.PAYMENT_TERMS),
            "port_of_loading": c3.selectbox("선적항 *", list(config.PORTS),
                                            format_func=lambda p: p + ("" if config.PORTS[p][0] == config.HOME_COUNTRY else f" ({config.PORTS[p][0]} · 삼국 간)")),
        }
        with c1:
            fields["etd"] = date_text("n_etd", "ETD *")
        with c2:
            fields["lc_ship_by"] = date_text("n_lc", "L/C 선적 기한 (L/C일 때 필수)")
        with c3:
            fields["eta"] = date_text("n_eta", "ETA")
        with st.expander("인코텀즈 · L/C 원본 칸 (L/C면 44C 기한을 한 번 더 입력)", expanded=True):
            fields.update(v32_inputs("n"))
        with st.expander("선적 정보 (선택)"):
            s1, s2, s3 = st.columns(3)
            extra = {"carrier": s1.text_input("선사"), "vessel": s2.text_input("선명/항차"),
                     "booking_no": s3.text_input("부킹번호"), "bl_no": s1.text_input("B/L 번호"),
                     "action": s3.text_input("대응 계획")}
            with s2:
                extra["cutoff"] = date_text("n_cut", "서류 마감일")
        submitted = st.form_submit_button(M.SAVE_BUTTON)
    st.caption("결제 조건이 T/T · D/P면 L/C 선적 기한은 저장하지 않아요. 선적항이 한국이 아니면 '삼국 간'으로 표시돼요.")
    st.divider()
    st.markdown(f"**{M.BULK_TITLE}** — 이미 있는 오더번호는 건너뛰고, 미리보기에서 확인해야 반영돼요.")
    st.download_button(M.TEMPLATE_BUTTON, data=logic.template_csv_bytes(), file_name=M.TEMPLATE_NAME, mime="text/csv")
    b1, b2 = st.tabs(["CSV 파일 올리기", "엑셀에서 붙여넣기"])
    with b1:
        up_new = st.file_uploader("양식에 채운 CSV 파일", type=["csv"], key="up_new")
        if up_new is not None:
            import_preview(up_new.getvalue().decode("utf-8-sig", errors="replace"), "new_file")
    with b2:
        pasted = st.text_area(M.PASTE_HELP, height=160, key="paste_new")
        if pasted.strip():
            import_preview(pasted, "new_paste")
    if submitted:
        fields.update({k: v for k, v in extra.items() if v})
        if fields["payment_terms"] != "L/C":
            fields.pop("lc_ship_by_confirm", None)
        err = logic.validate_new_order(fields, [o["order_no"] for o in orders])
        if err:
            st.error(err)
        else:
            new_order = logic.build_order(fields)
            new_order.update({k: v.strip() for k, v in extra.items() if v})
            warns = logic.check_warnings(new_order, logic.active_orders(orders))
            storage.add_order(new_order)
            ss.flash = M.SAVED.format(order_no=fields["order_no"].strip())
            if fields["payment_terms"] != "L/C" and fields["lc_ship_by"]:
                ss.flash += " " + M.NOTE_NO_LC.format(terms=fields["payment_terms"])
            if warns:
                ss.flash += f" — {M.CHECK_TITLE} {len(warns)}건: " + " / ".join(c["msg"] for c in warns)
            st.rerun()

# ======================= 메일 가져오기 (F8) =======================
with tab_mail:
    st.markdown("**선사 · 포워더 메일 본문을 붙여 넣으면** 오더번호 · ETD · ETA · B/L · 선명을 찾아요. 확인을 눌러야 반영돼요.")
    st.caption("이 화면은 붙여넣기만 해요. 실제 Gmail에서 바로 가져오기는 Claude 공유 페이지에서만 돼요 (본인 메일 읽기만).")
    dm = st.columns(len(M.DEMO_MAILS))
    for c, (name, body) in zip(dm, M.DEMO_MAILS):
        if c.button(f"가상 메일: {name}", key=f"demo_mail_{name}"):
            ss.mail_text = body
            st.rerun()
    mail_text = st.text_area("메일 본문", value=ss.get("mail_text", ""), height=220, key="mail_box",
                             placeholder="메일 본문 전체를 붙여 넣으세요 (제목 줄 포함하면 더 정확해요)")
    if mail_text.strip():
        p = logic.parse_mail(mail_text)
        st.markdown("**메일에서 찾은 값**")
        shown = {"오더번호": p["order_no"], "부킹번호": p["booking_no"], "B/L 번호": p["bl_no"], "선명/항차": p["vessel"],
                 "선적항": p["pol"], "도착항": p["pod"], "ETD": (f"{p['etd_old']} → " if p["etd_old"] else "") + p["etd"],
                 "ETA": p["eta"], "상태": p["status"]}
        st.dataframe([{"칸": k, "값": v or "메일에서 못 찾음"} for k, v in shown.items()], hide_index=True)
        plan = logic.plan_mail_update(p, orders)
        for n in plan["notes"]:
            st.warning(n)
        if plan["error"] and not plan["match"]:
            st.info(plan["error"])
            if plan["error"] == M.MAIL_NO_MATCH:
                st.markdown("**새 오더 등록 탭에 아래 값을 넣어 주세요** (바이어 · 품목 · 결제 조건은 메일에 없어 직접 입력)")
                st.json({k: v for k, v in logic.mail_new_order_fields(p).items() if v})
        elif plan["error"]:
            st.error(plan["error"])
        else:
            o = plan["match"]
            st.markdown(f"**{o['buyer']}** · {o['item']} · {o['order_no']} — 바뀔 칸")
            st.dataframe([{"칸": M.FIELD_NAMES.get(k, k), "지금": o.get(k, "") or "—", "메일": v} for k, v in plan["diff"].items()],
                         hide_index=True)
            if st.button("반영하기", type="primary", key="mail_apply"):
                storage.update_order(o["order_no"], plan["diff"])
                if plan["etd_change"]:
                    storage.append_change(plan["etd_change"])
                ss.flash = M.MAIL_APPLIED.format(order_no=o["order_no"], what=", ".join(M.FIELD_NAMES.get(k, k) for k in plan["diff"]))
                ss.mail_text = ""
                st.rerun()

# ======================= 변경 기록 =======================
with tab_log:
    st.caption("⚠️ " + M.DEMO_NOTICE)
    waiting = [o for o in active if logic.is_waiting(o)]
    with st.form("etd_change"):
        c1, c2, c3 = st.columns([2, 1.2, 2])
        pick = c1.selectbox(M.CHANGE_ORDER, ["(선택)"] + [f"{o['order_no']} · 현재 ETD {o['etd']}" for o in waiting])
        with c2:
            new_etd = date_text("chg_etd", M.CHANGE_NEW_ETD)
        reason = c3.text_input(M.CHANGE_REASON, placeholder="롤오버")
        go = st.form_submit_button(M.CHANGE_SAVE)
    if go:
        target = None if pick == "(선택)" else next(o for o in waiting if pick.startswith(o["order_no"] + " "))
        err = logic.validate_etd_change(target, new_etd, reason)
        if err:
            st.error(err)
        else:
            ch = logic.build_change(target["order_no"], target["etd"], new_etd, reason)
            storage.apply_etd_change(ch)
            ss.flash = M.CHANGED.format(order_no=ch["order_no"], old=ch["old_etd"], new=ch["new_etd"], reason=ch["reason"])
            st.rerun()
    if st.button(M.DEMO_BUTTON):
        plan, skipped = logic.plan_demo_updates(orders, storage.load_carrier_demo())
        for ch in plan:
            storage.apply_etd_change(ch)
        ss.flash = M.DEMO_RESULT.format(changed=len(plan), skipped=skipped) if plan else M.DEMO_NONE + (f" · {skipped}건 건너뜀" if skipped else "")
        st.rerun()
    # 선사 연동 시뮬레이션 (F3-6)
    with st.container(border=True):
        st.markdown(f"**{M.SIM_TITLE}** — 실제 선사 연동이 움직이는 순서를 보여 줘요. ⚠️ {M.DEMO_NOTICE}")
        sim_pick = st.selectbox("조회할 오더", ["(선택)"] + [f"{o['order_no']} · {o.get('carrier') or '선사 미지정'} · "
                                f"{o.get('booking_no') or o.get('bl_no') or '조회 키 없음'}" for o in waiting], key="sim_pick")
        if st.button("조회 실행", key="sim_run") and sim_pick != "(선택)":
            ss.sim_order = sim_pick.split(" · ")[0]
        if ss.get("sim_order"):
            target = next((o for o in waiting if o["order_no"] == ss.sim_order), None)
            r = logic.simulate_carrier_query(target, storage.load_carrier_demo()) if target else None
            if r and not r["ok"]:
                st.error("① " + r["error"])
            elif r:
                with st.status("선사 조회 진행", expanded=True, state="complete"):
                    for i, step in enumerate(r["steps"], 1):
                        st.write(f"{'①②③④'[i-1]} {step}")
                    st.json(r["response"], expanded=False)
                if r["change"]:
                    if st.button(f"⑤ {M.SIM_APPLY} — ETD {r['change']['old_etd']} → {r['change']['new_etd']}", type="primary", key="sim_apply"):
                        storage.apply_etd_change(r["change"])
                        ss.sim_order = None
                        ss.flash = M.CHANGED.format(order_no=r["change"]["order_no"], old=r["change"]["old_etd"],
                                                    new=r["change"]["new_etd"], reason=r["change"]["reason"])
                        st.rerun()
                else:
                    st.info("⑤ " + M.SIM_SAME)

    # ETD · L/C 기한 · 상태 변경을 한 표로 (F3-5) — 증감은 회색 화살표
    log_rows = []
    for c in changes:
        d = (date.fromisoformat(c["new_etd"]) - date.fromisoformat(c["old_etd"])).days
        log_rows.append({"바꾼 시각": c["changed_at"], "오더번호": c["order_no"], "항목": "ETD", "이전": c["old_etd"],
                         "새 값": c["new_etd"], "변화": f"▲ {d}일 늦어짐" if d > 0 else f"▼ {-d}일 앞당겨짐", "사유": c["reason"]})
    for c in change_log:
        chg = ""
        if c["field"] == M.FIELD_LC and c["old"] and c["new"]:
            d = (date.fromisoformat(c["new"]) - date.fromisoformat(c["old"])).days
            chg = f"▲ {d}일 연장" if d > 0 else f"▼ {-d}일 단축"
        log_rows.append({"바꾼 시각": c["changed_at"], "오더번호": c["order_no"], "항목": c["field"], "이전": c["old"],
                         "새 값": c["new"], "변화": chg, "사유": c["reason"]})
    log_rows.sort(key=lambda r: r["바꾼 시각"], reverse=True)
    st.markdown(f"**변경 기록 전체** ({len(log_rows)}건 · 최근 순)")
    if log_rows:
        st.dataframe(log_rows, hide_index=True, use_container_width=True)
    else:
        st.write("아직 변경 기록이 없어요.")

# ======================= 보고 내보내기 · 불러오기 =======================
with tab_report:
    st.caption(M.COPY_HELP)
    st.code(logic.report_text(orders), language=None)
    st.download_button(M.CSV_BUTTON, data=logic.export_csv_bytes(orders, changes),
                       file_name=M.CSV_NAME.format(date=today.isoformat()), mime="text/csv")
    st.divider()
    st.markdown("**CSV 불러오기** — 이미 있는 오더번호는 덮어쓰지 않고 건너뛰어요.")
    up = st.file_uploader("이 앱에서 내보낸 CSV 파일", type=["csv"], key="up_report")
    if up is not None:
        import_preview(up.getvalue().decode("utf-8-sig", errors="replace"), "report")
