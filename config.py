"""설정값 — 기준을 바꿀 때는 이 파일만 고친다. (CLAUDE.md 규칙 B)"""

# 한국 시간대 (ETD · L/C 기한 · 선적일은 선적항(한국) 날짜 기준)
KOREA_TZ = "Asia/Seoul"

# F2 경고 기준: L/C 기한까지 이 일수 이하로 남으면 🟡 임박
# (정기선은 주 1회 운항이 많아 롤오버 한 번에 ETD가 약 1주 밀리기 때문)
WARNING_DAYS = 7

# 바이어 국가 목록 (화면에 보이는 이름 → 시간대)
BUYER_COUNTRIES = {
    "미국 동부": "America/New_York",
    "미국 서부": "America/Los_Angeles",
    "독일": "Europe/Berlin",
    "영국": "Europe/London",
    "베트남": "Asia/Ho_Chi_Minh",
    "일본": "Asia/Tokyo",
    "UAE": "Asia/Dubai",
    "호주": "Australia/Sydney",
}

# 오더 상태
STATUS_WAITING = "선적 대기"
STATUS_SHIPPED = "선적 완료"

# 데이터 파일
DATA_DIR = "data"
ORDERS_FILE = "data/orders.csv"
CHANGES_FILE = "data/etd_changes.csv"
CARRIER_DEMO_FILE = "data/carrier_demo.json"
BACKUP_DIR = "data/backup"

ORDER_COLUMNS = [
    "order_no", "buyer", "buyer_country", "item", "etd", "eta",
    "lc_ship_by", "status", "shipped_on", "created_at", "deleted",
]
CHANGE_COLUMNS = ["order_no", "old_etd", "new_etd", "reason", "changed_at"]
