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

# 결제 조건 — F2 L/C 기한 경고는 L/C만 대상
PAYMENT_TERMS = ["L/C", "T/T", "D/P"]
DEFAULT_PAYMENT = "L/C"

# 선적항 목록 (화면 이름 → (나라, 시간대)). 한국이 아니면 "삼국 간"
HOME_COUNTRY = "한국"
PORTS = {
    "부산": ("한국", "Asia/Seoul"),
    "인천": ("한국", "Asia/Seoul"),
    "광양": ("한국", "Asia/Seoul"),
    "상하이": ("중국", "Asia/Shanghai"),
    "칭다오": ("중국", "Asia/Shanghai"),
    "호찌민": ("베트남", "Asia/Ho_Chi_Minh"),
    "하이퐁": ("베트남", "Asia/Ho_Chi_Minh"),
    "싱가포르": ("싱가포르", "Asia/Singapore"),
    "램차방": ("태국", "Asia/Bangkok"),
    "로테르담": ("네덜란드", "Europe/Amsterdam"),
}
DEFAULT_PORT = "부산"

# 선적항 UN/LOCODE (선사 조회 시뮬레이션의 가상 응답에 사용)
PORT_CODES = {"부산": "KRPUS", "인천": "KRINC", "광양": "KRKAN", "상하이": "CNSHA", "칭다오": "CNTAO",
              "호찌민": "VNSGN", "하이퐁": "VNHPH", "싱가포르": "SGSIN", "램차방": "THLCH", "로테르담": "NLRTM"}
# 선적항 영어 이름 (L/C · 인코텀즈 지정 장소는 영어로 적는 경우가 많음 → 같은 항구로 인식)
PORT_EN = {"부산": "Busan", "인천": "Incheon", "광양": "Gwangyang", "상하이": "Shanghai", "칭다오": "Qingdao",
           "호찌민": "Ho Chi Minh", "하이퐁": "Haiphong", "싱가포르": "Singapore", "램차방": "Laem Chabang",
           "로테르담": "Rotterdam"}

# 인코텀즈 2020 (F1-16) — 주 운송(배)을 누가 잡는지
INCOTERMS = ["EXW", "FCA", "FAS", "FOB", "CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"]
BUYER_BOOKS = {"EXW", "FCA", "FAS", "FOB"}          # 바이어 측 포워더가 부킹
PLACE_IS_LOADING = {"FAS", "FOB"}                   # 지정 장소 = 선적항
PLACE_IS_DISCHARGE = {"CFR", "CIF"}                 # 지정 장소 = 도착항

# L/C 서류 제시 기간 기본값 (UCP 600 제14조 c항: 선적 후 21일, 유효기한 이내)
LC_PRESENTATION_DEFAULT = 21

# 입력 크로스체크 (F7) — 날짜 오타 의심 기준
MAX_TRANSIT_DAYS = 60
MAX_CUTOFF_GAP_DAYS = 14
MAX_ETD_AHEAD_DAYS = 365

# 선사 연동 시뮬레이션의 가상 API 주소 (example.com = 예시 전용 도메인, 실제 선사 아님)
DEMO_API = "https://carrier-api.example.com/v2/events"

# 일괄 등록 빈 양식 칸 (한국어 이름 — 내보내기 · 불러오기와 같음)
TEMPLATE_COLUMNS = ["오더번호", "바이어", "바이어 국가", "품목", "결제 조건", "선적항", "ETD", "ETA", "L/C 선적 기한",
                    "선사", "선명/항차", "부킹번호", "B/L 번호", "서류 마감일", "대응 계획",
                    "인코텀즈", "인코텀즈 장소", "도착항", "L/C 유효기한", "서류 제시 기간",
                    "L/C 선적항(44E)", "L/C 도착항(44F)"]

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
    "order_no", "buyer", "buyer_country", "item", "payment_terms", "port_of_loading",
    "etd", "eta", "lc_ship_by", "status", "shipped_on", "created_at", "deleted",
    # v3 선적 정보 (모두 선택)
    "carrier", "vessel", "booking_no", "bl_no", "cutoff", "action",
    # v3.2 인코텀즈 · L/C 원본 칸 (모두 선택)
    "incoterms", "incoterms_place", "port_of_discharge",
    "lc_expiry", "lc_presentation_days", "lc_port_loading", "lc_port_discharge",
]
V32_FIELDS = ["incoterms", "incoterms_place", "port_of_discharge",
              "lc_expiry", "lc_presentation_days", "lc_port_loading", "lc_port_discharge"]
LC_ONLY_FIELDS = ["lc_ship_by", "lc_expiry", "lc_presentation_days", "lc_port_loading", "lc_port_discharge"]
CHANGE_COLUMNS = ["order_no", "old_etd", "new_etd", "reason", "changed_at"]

# v3 L/C 기한 · 상태 변경 기록 (추가만)
CHANGE_LOG_FILE = "data/change_log.csv"
CHANGE_LOG_COLUMNS = ["order_no", "field", "old", "new", "reason", "changed_at"]

# 서류 마감(Cut-off) 임박 기준: 마감까지 이 일수 이하
CUTOFF_WARN_DAYS = 2

# 수정할 수 있는 칸 (오더번호 제외)
EDITABLE = ["buyer", "buyer_country", "item", "payment_terms", "port_of_loading", "etd", "eta",
            "lc_ship_by", "carrier", "vessel", "booking_no", "bl_no", "cutoff", "action",
            "incoterms", "incoterms_place", "port_of_discharge",
            "lc_expiry", "lc_presentation_days", "lc_port_loading", "lc_port_discharge"]
