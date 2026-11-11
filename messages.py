"""화면에 나오는 안내 · 에러 문구 모음 (CLAUDE.md 규칙 7 · C)
모든 에러는 '무엇이 문제인지 + 어떻게 고치는지' 한국어 한 줄."""

APP_TITLE = "📡 ETD 레이더"
APP_SUBTITLE = "밀린 ETD와 L/C 선적 기한 위험을 한눈에 잡아내는 선적 일정 레이더"

# F1 등록
FORM_TITLE = "새 오더 등록"
SAVE_BUTTON = "오더 저장하기"
SAVED = "오더 {order_no}을(를) 저장했어요."
ERR_REQUIRED = "{field} 칸이 비어 있어요. 채운 뒤 다시 저장해 주세요."
ERR_DUPLICATE = "이미 등록된 오더번호예요({order_no}). 다른 오더번호를 입력해 주세요."
ERR_DATE_FORMAT = "{field} 날짜는 2026-11-20처럼 입력해 주세요."
ERR_DATE_INVALID = "{field}에 없는 날짜예요({value}). 달력에 있는 날짜로 입력해 주세요."
ERR_COUNTRY = "바이어 국가는 목록에서 골라 주세요."

FIELD_NAMES = {
    "order_no": "오더번호",
    "buyer": "바이어",
    "buyer_country": "바이어 국가",
    "item": "품목",
    "etd": "ETD",
    "eta": "ETA",
    "lc_ship_by": "L/C 선적 기한",
    "shipped_on": "실제 선적일",
}

# F1 목록
LIST_TITLE = "오더 목록 (ETD 빠른 순)"
EMPTY_ORDERS = "아직 등록된 오더가 없어요. 위에서 첫 오더를 등록해 주세요."
NO_COUNTRY = "바이어 국가를 고르지 않아 한국 날짜만 보여요."

# F1 오늘 날짜
TODAY_KOREA = "오늘(한국): {date}"
TODAY_LOCAL = "오늘({country}): {date}"

# F1 삭제 · 복구
DELETE_BUTTON = "삭제"
DELETE_CONFIRM = "정말 삭제할까요? 오더 {order_no}은(는) 목록에서 숨겨지고, 아래 '삭제된 오더 보기'에서 복구할 수 있어요."
DELETE_YES = "네, 삭제할게요"
DELETE_NO = "취소"
DELETED = "오더 {order_no}을(를) 삭제했어요. '삭제된 오더 보기'에서 복구할 수 있어요."
DELETED_TITLE = "삭제된 오더 보기"
NO_DELETED = "삭제된 오더 없음"
RESTORE_BUTTON = "복구"
RESTORED = "오더 {order_no}을(를) 복구했어요."

# F1 선적 완료
SHIP_BUTTON = "선적 완료"
SHIP_PROMPT = "오더 {order_no}의 실제 선적일(B/L On board date)을 입력해 주세요."
SHIP_SAVE = "선적 완료로 저장"
SHIPPED = "오더 {order_no}을(를) 선적 완료로 저장했어요 (선적일 {date})."
ERR_SHIPPED_FUTURE = "실제 선적일이 오늘(한국 {today})보다 뒤예요. 이미 선적한 날짜를 입력해 주세요."

# 공통
ERR_FILE = "데이터 파일을 읽지 못했어요({path}). 파일이 다른 프로그램에서 열려 있으면 닫고 새로고침해 주세요."

# F2 L/C 선적 기한 경고
LC_OVER = "L/C 기한 {days}일 초과"
LC_SAME_DAY = "L/C 기한 당일 출항"
LC_LEFT = "L/C 기한까지 {days}일 남음"
LC_SHIPPED_OK = "기한 내 선적"
LC_SHIPPED_LATE = "L/C 기한 {days}일 넘겨 선적"
REPORT_WAITING = "{order_no} ETD {etd}, L/C 기한 {lc} → {label}"
REPORT_SHIPPED = "{order_no} 실제 선적일 {shipped}, L/C 기한 {lc} → {label}"
SUMMARY = "🔴 기한 초과 {red}건 · 🟡 임박 {yellow}건 (선적 대기 오더 기준)"
NO_RISK = "기한 위험 오더 없음"
SUMMARY_LATE_SHIPPED = "기한을 넘겨 선적한 오더 {n}건"
RISK_TITLE = "L/C 선적 기한 경고 (보고용 문장)"

# F3 ETD 변경 기록
CHANGE_TITLE = "ETD 변경하기"
CHANGE_ORDER = "변경할 오더"
CHANGE_NEW_ETD = "새 ETD"
CHANGE_REASON = "사유"
CHANGE_SAVE = "ETD 변경 저장"
CHANGED = "{order_no} ETD를 {old} → {new}로 바꿨어요 (사유: {reason})."
ERR_REASON = "사유 칸이 비어 있어요. 롤오버 · 기상 악화처럼 사유를 적어 주세요."
ERR_SAME_ETD = "지금 ETD({etd})와 같은 날짜예요. 바뀐 날짜를 입력해 주세요."
ERR_NO_ORDER = "변경할 오더를 먼저 골라 주세요."
HIST_NONE = "변경 없음"
HIST_LATER = "처음 ETD보다 {days}일 늦어짐 ({n}회 변경)"
HIST_EARLIER = "처음 ETD보다 {days}일 앞당겨짐 ({n}회 변경)"
HIST_SAME = "처음 ETD와 같음 ({n}회 변경)"
HISTORY_TITLE = "ETD 변경 기록"
DEMO_BUTTON = "선사 조회 (데모)"
DEMO_NOTICE = "데모: 실제 선사와 연결되지 않음"
DEMO_REASON = "선사 조회(데모)"
DEMO_RESULT = "{changed}건 변경 · {skipped}건 건너뜀"
DEMO_NONE = "변경된 ETD 없음"
