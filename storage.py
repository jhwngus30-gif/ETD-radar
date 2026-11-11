"""data/ 파일 읽고 쓰기 (CLAUDE.md 규칙 1 · 2 · 5 · A)
- 오더 줄은 절대 지우지 않는다. 삭제 = deleted=True
- 저장하기 전에 data/backup/ 에 사본을 남긴다
- 파일이 없으면 칸 이름만 있는 빈 파일을 만든다"""

import csv
import os
import shutil
from datetime import datetime

import config


def _ensure_file(path, columns):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(columns)


def _backup(path, backup_dir):
    if not os.path.exists(path):
        return
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    name = os.path.basename(path).replace(".csv", f"_{stamp}.csv")
    shutil.copy2(path, os.path.join(backup_dir, name))


def load_orders(path=config.ORDERS_FILE):
    _ensure_file(path, config.ORDER_COLUMNS)
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for c in config.ORDER_COLUMNS:
            r.setdefault(c, "")
            if r[c] is None:
                r[c] = ""
    return rows


def _write_orders(orders, path, backup_dir):
    """전체 다시 쓰기. 줄 수가 줄어드는 저장은 거부한다 (오더 기록 보호)."""
    before = load_orders(path)
    if len(orders) < len(before):
        raise ValueError("오더 줄 수가 줄어드는 저장은 할 수 없어요 (삭제는 숨기기만 가능).")
    _backup(path, backup_dir)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=config.ORDER_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(orders)


def add_order(order, path=config.ORDERS_FILE, backup_dir=config.BACKUP_DIR):
    orders = load_orders(path)
    orders.append(order)
    _write_orders(orders, path, backup_dir)


def _update(order_no, changes, path, backup_dir):
    orders = load_orders(path)
    found = False
    for o in orders:
        if o["order_no"] == order_no:
            o.update(changes)
            found = True
    if not found:
        raise KeyError(order_no)
    _write_orders(orders, path, backup_dir)


def set_deleted(order_no, deleted, path=config.ORDERS_FILE, backup_dir=config.BACKUP_DIR):
    _update(order_no, {"deleted": "True" if deleted else "False"}, path, backup_dir)


def mark_shipped(order_no, shipped_on, path=config.ORDERS_FILE, backup_dir=config.BACKUP_DIR):
    _update(order_no, {"status": config.STATUS_SHIPPED, "shipped_on": shipped_on}, path, backup_dir)


def load_changes(path=config.CHANGES_FILE):
    _ensure_file(path, config.CHANGE_COLUMNS)
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def append_change(change, path=config.CHANGES_FILE, backup_dir=config.BACKUP_DIR):
    """변경 기록은 덧붙이기만 한다 (규칙 2)."""
    _ensure_file(path, config.CHANGE_COLUMNS)
    _backup(path, backup_dir)
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=config.CHANGE_COLUMNS, extrasaction="ignore").writerow(change)


def apply_etd_change(change, orders_path=config.ORDERS_FILE, changes_path=config.CHANGES_FILE,
                     backup_dir=config.BACKUP_DIR):
    _update(change["order_no"], {"etd": change["new_etd"]}, orders_path, backup_dir)
    append_change(change, changes_path, backup_dir)


def load_carrier_demo(path=config.CARRIER_DEMO_FILE):
    import json
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("updates", [])
