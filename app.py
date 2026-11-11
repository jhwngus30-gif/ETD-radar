"""ETD 레이더 — 화면 (F1 · F2 · F3). 계산은 logic.py, 파일은 storage.py에서 한다."""

import streamlit as st

import config
import logic
import messages as M
import storage

st.set_page_config(page_title="ETD 레이더", page_icon="📡", layout="wide")
st.title(M.APP_TITLE)
st.caption(M.APP_SUBTITLE)

ss = st.session_state
ss.setdefault("pending_delete", None)
ss.setdefault("pending_ship", None)
ss.setdefault("flash", None)

try:
    orders = storage.load_orders()
    changes = storage.load_changes()
except Exception:
    st.error(M.ERR_FILE.format(path=config.ORDERS_FILE))
    st.stop()

if ss.flash:
    st.success(ss.flash)
    ss.flash = None

# ---------- 오늘 날짜: 한국 + 바이어 현지 (F1-5) ----------
active = logic.active_orders(orders)
date_parts = [M.TODAY_KOREA.format(date=logic.today_korea().isoformat())]
for country in sorted({o["buyer_country"] for o in active if o["buyer_country"] in config.BUYER_COUNTRIES}):
    date_parts.append(M.TODAY_LOCAL.format(country=country, date=logic.local_today(country).isoformat()))
st.info(" · ".join(date_parts))

# ---------- F2 경고 요약 ----------
summ = logic.lc_summary(orders)
if summ["red"] == 0 and summ["yellow"] == 0:
    st.success(M.NO_RISK)
else:
    st.error(M.SUMMARY.format(red=summ["red"], yellow=summ["yellow"]))
if summ["late_shipped"]:
    st.warning(M.SUMMARY_LATE_SHIPPED.format(n=summ["late_shipped"]))
risky = [logic.lc_status(o) for o in active]
risky = [r for r in risky if r["level"] in ("red", "yellow")]
if risky:
    with st.expander(M.RISK_TITLE, expanded=True):
        for r in sorted(risky, key=lambda r: (r["level"] != "red", r["days"])):
            st.write(r["label"][:2] + " " + r["sentence"])

# ---------- 새 오더 등록 (F1-1, F1-2) ----------
with st.expander(M.FORM_TITLE, expanded=not active):
    with st.form("new_order", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        order_no = c1.text_input("오더번호 *", placeholder="PO-2611-011")
        buyer = c2.text_input("바이어 *", placeholder="가상 회사명")
        country = c3.selectbox("바이어 국가", ["(선택 안 함)"] + list(config.BUYER_COUNTRIES))
        c4, c5, c6, c7 = st.columns(4)
        item = c4.text_input("품목 *")
        etd = c5.text_input("ETD *", placeholder="2026-11-20")
        eta = c6.text_input("ETA (선택)", placeholder="2026-12-10")
        lc = c7.text_input("L/C 선적 기한 *", placeholder="2026-11-25")
        submitted = st.form_submit_button(M.SAVE_BUTTON)
    if submitted:
        fields = {
            "order_no": order_no, "buyer": buyer,
            "buyer_country": "" if country == "(선택 안 함)" else country,
            "item": item, "etd": etd, "eta": eta, "lc_ship_by": lc,
        }
        err = logic.validate_new_order(fields, [o["order_no"] for o in orders])
        if err:
            st.error(err)
        else:
            storage.add_order(logic.build_order(fields))
            ss.flash = M.SAVED.format(order_no=fields["order_no"].strip())
            st.rerun()

# ---------- 오더 목록 (F1-1, F1-3) ----------
st.subheader(M.LIST_TITLE)
if not active:
    st.info(M.EMPTY_ORDERS)
else:
    widths = [1.2, 1.5, 0.9, 1.5, 1, 1, 1.1, 1.5, 1.8, 1.7, 1.6]
    head = st.columns(widths)
    for h, t in zip(head, ["오더번호", "바이어", "국가", "품목", "ETD", "ETA", "L/C 선적 기한", "상태", "L/C 경고", "ETD 변경", ""]):
        h.markdown(f"**{t}**")
    for o in active:
        cols = st.columns(widths)
        cols[0].write(o["order_no"])
        cols[1].write(o["buyer"])
        cols[2].write(o["buyer_country"] or "—")
        cols[3].write(o["item"])
        cols[4].write(o["etd"])
        cols[5].write(o["eta"] or "—")
        cols[6].write(o["lc_ship_by"])
        if o["status"] == config.STATUS_SHIPPED:
            cols[7].write(f"{config.STATUS_SHIPPED} ({o['shipped_on']})")
        else:
            cols[7].write(config.STATUS_WAITING)
        cols[8].write(logic.lc_status(o)["label"])
        cols[9].write(logic.etd_history(o, changes))
        b1, b2 = cols[10].columns(2)
        if o["status"] != config.STATUS_SHIPPED and b1.button(M.SHIP_BUTTON, key=f"ship_{o['order_no']}"):
            ss.pending_ship, ss.pending_delete = o["order_no"], None
        if b2.button(M.DELETE_BUTTON, key=f"del_{o['order_no']}"):
            ss.pending_delete, ss.pending_ship = o["order_no"], None

        # 삭제 확인 (F1-4)
        if ss.pending_delete == o["order_no"]:
            st.warning(M.DELETE_CONFIRM.format(order_no=o["order_no"]))
            y, n, _ = st.columns([1, 1, 6])
            if y.button(M.DELETE_YES, key=f"yes_{o['order_no']}"):
                storage.set_deleted(o["order_no"], True)
                ss.pending_delete = None
                ss.flash = M.DELETED.format(order_no=o["order_no"])
                st.rerun()
            if n.button(M.DELETE_NO, key=f"no_{o['order_no']}"):
                ss.pending_delete = None
                st.rerun()

        # 선적 완료 입력 (F1-7)
        if ss.pending_ship == o["order_no"]:
            with st.form(f"shipform_{o['order_no']}"):
                shipped = st.text_input(M.SHIP_PROMPT.format(order_no=o["order_no"]), placeholder="2026-11-10")
                ok = st.form_submit_button(M.SHIP_SAVE)
            if ok:
                err = logic.validate_shipped_on(shipped)
                if err:
                    st.error(err)
                else:
                    storage.mark_shipped(o["order_no"], shipped.strip())
                    ss.pending_ship = None
                    ss.flash = M.SHIPPED.format(order_no=o["order_no"], date=shipped.strip())
                    st.rerun()

    if any(not o["buyer_country"] for o in active):
        st.caption(M.NO_COUNTRY)

# ---------- F3 ETD 변경 기록 ----------
st.subheader(M.HISTORY_TITLE)
st.caption("⚠️ " + M.DEMO_NOTICE)
waiting = [o for o in active if o["status"] != config.STATUS_SHIPPED]
with st.form("etd_change"):
    c1, c2, c3 = st.columns([2, 1.2, 2])
    pick = c1.selectbox(M.CHANGE_ORDER, ["(선택)"] + [f"{o['order_no']} · 현재 ETD {o['etd']}" for o in waiting])
    new_etd = c2.text_input(M.CHANGE_NEW_ETD, placeholder="2026-11-27")
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
    if not plan:
        ss.flash = M.DEMO_NONE + (f" · {skipped}건 건너뜀" if skipped else "")
    else:
        ss.flash = M.DEMO_RESULT.format(changed=len(plan), skipped=skipped)
    st.rerun()

if changes:
    with st.expander(f"변경 기록 전체 ({len(changes)}건)"):
        for c in sorted(changes, key=lambda c: c["changed_at"], reverse=True):
            st.write(f"{c['changed_at']} · {c['order_no']} · {c['old_etd']} → {c['new_etd']} · {c['reason']}")

# ---------- 삭제된 오더 보기 · 복구 (F1-6) ----------
with st.expander(M.DELETED_TITLE):
    gone = logic.deleted_orders(orders)
    if not gone:
        st.write(M.NO_DELETED)
    for o in gone:
        c = st.columns([2, 2, 2, 2, 1])
        c[0].write(o["order_no"])
        c[1].write(o["buyer"])
        c[2].write(o["item"])
        c[3].write(f"ETD {o['etd']}")
        if c[4].button(M.RESTORE_BUTTON, key=f"restore_{o['order_no']}"):
            storage.set_deleted(o["order_no"], False)
            ss.flash = M.RESTORED.format(order_no=o["order_no"])
            st.rerun()
