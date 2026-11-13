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
    "incoterms": "인코텀즈",
    "incoterms_place": "인코텀즈 장소",
    "port_of_discharge": "도착항",
    "lc_expiry": "L/C 유효기한",
    "lc_presentation_days": "서류 제시 기간",
    "lc_port_loading": "L/C 선적항(44E)",
    "lc_port_discharge": "L/C 도착항(44F)",
    "lc_ship_by_confirm": "L/C 선적 기한 확인",
    "order_no": "오더번호",
    "buyer": "바이어",
    "buyer_country": "바이어 국가",
    "item": "품목",
    "payment_terms": "결제 조건",
    "port_of_loading": "선적항",
    "etd": "ETD",
    "eta": "ETA",
    "lc_ship_by": "L/C 선적 기한",
    "shipped_on": "실제 선적일",
    "carrier": "선사",
    "vessel": "선명/항차",
    "booking_no": "부킹번호",
    "bl_no": "B/L 번호",
    "cutoff": "서류 마감일",
    "action": "대응 계획",
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

# v2 결제 조건 · 선적항
ERR_PAYMENT = "결제 조건은 L/C · T/T · D/P 중에서 골라 주세요."
ERR_PORT = "선적항은 목록에서 골라 주세요."
NOTE_NO_LC = "{terms} 거래라 L/C 기한은 저장하지 않았어요."
LC_NA = "L/C 아님 ({terms})"
LC_NA_SHIPPED = "선적 완료 ({terms} · L/C 판정 없음)"
REPORT_NA = "{order_no} ETD {etd} → {label}"
THIRD_COUNTRY = "삼국 간"
TODAY_PORT = "오늘(선적항 {port}): {date}"

# F4 보고 내보내기
REPORT_HEAD = "[ETD 레이더] {date} L/C 기한 위험 보고 — 🔴 {red}건 · 🟡 {yellow}건"
REPORT_TITLE = "보고 내보내기"
COPY_HELP = "오른쪽 위 복사 아이콘을 누르면 보고 문장 전체가 복사돼요."
CSV_BUTTON = "엑셀(CSV) 내보내기"
CSV_NAME = "etd-radar_{date}.csv"

# v3 ETD 지남 · 서류 마감
LATE = "ETD {days}일 지남 · 선적 미확인"
REPORT_LATE = "{order_no} ETD {etd} → {label}"
CUTOFF_OVER = "서류 마감 {days}일 지남"
CUTOFF_SOON = "서류 마감 D-{days}"
CUTOFF_TODAY = "서류 마감 D-Day"

# v3 보고
REPORT_HEAD_V3 = "[ETD 레이더] {date} 선적 위험 보고 — 🚨 {late}건 · 🔴 {red}건 · 🟡 {yellow}건"
REPORT_NONE = "위험 오더 없음"
ACTION_SUFFIX = " · 조치: {action}"
ACTION_NONE = "(미정)"

# v3 수정 · 되돌리기 · 검색 · 불러오기
EDITED = "오더 {order_no}을(를) 수정했어요."
ERR_EDIT_REASON = "{field}이(가) 바뀌었어요. 바꾼 사유를 적어 주세요. (예: L/C 연장(Amendment), 롤오버)"
NO_CHANGE = "바뀐 내용이 없어요."
UNSHIP_CONFIRM = "오더 {order_no}을(를) 다시 '선적 대기'로 되돌릴까요? 실제 선적일({date})은 지워져요."
UNSHIPPED = "오더 {order_no}을(를) 선적 대기로 되돌렸어요."
UNSHIP_REASON = "선적 완료 되돌리기"
FIELD_LC = "L/C 기한"
FIELD_STATUS = "상태"
SEARCH_EMPTY = "검색 결과가 없어요."
IMPORT_RESULT = "{added}건 추가 · {skipped}건 건너뜀(이미 있음) · {errors}건 오류"
IMPORT_ERR_LINE = "{line}번째 줄: {reason}"
IMPORT_EMPTY = "불러올 오더가 없어요. 이 앱에서 내보낸 CSV인지 확인해 주세요."
IMPORT_NO_HEADER = "오더번호 칸을 찾지 못했어요. 이 앱에서 내보낸 CSV인지 확인해 주세요."
ALERTS_TITLE = "오늘 확인할 것"
ALERTS_NONE = "오늘 확인할 것 없음"

# v3.1 일괄 등록 · 선사 연동 시뮬레이션
BULK_TITLE = "여러 오더 한 번에 등록"
TEMPLATE_BUTTON = "빈 양식(CSV) 내려받기"
TEMPLATE_NAME = "etd-radar_오더등록양식.csv"
PASTE_HELP = "엑셀에서 칸 이름 줄까지 함께 복사해 붙여 넣으세요."
SIM_TITLE = "선사 연동 시뮬레이션 (데모)"
SIM_NO_KEY = "부킹번호나 B/L 번호가 있어야 조회할 수 있어요. 오더 수정에서 먼저 넣어 주세요."
SIM_STEP1 = "조회 키 확인 — {key_name} {key} · 선사 {carrier}"
SIM_STEP2 = "선사 API 요청 — GET {url}"
SIM_STEP3 = "응답 수신 — 출항 예정(DEPA · EST) {etd} · {vessel}"
SIM_STEP4_CHANGED = "ETD 비교 — 현재 {old} → 선사 예정 {new} ({words})"
SIM_STEP4_SAME = "ETD 비교 — 현재 {old}, 선사 예정과 같음"
SIM_APPLY = "반영하기"
SIM_SAME = "변경 없음 — 반영할 내용이 없어요."


# ---------- v3.2 인코텀즈 · 입력 크로스체크 (F1-16·17, F7) ----------
BOOKER_BUYER = "바이어 측 포워더가 부킹 ({term}) → ETD는 바이어 포워더에 확인"
BOOKER_SELLER = "우리가 부킹 ({term}) → 선사 · 포워더에 직접 대응"
BOOKER_NONE = "인코텀즈 미입력 → 누가 배를 잡는지 확인 필요"
ERR_INCOTERMS = "인코텀즈는 EXW · FCA · FAS · FOB · CFR · CIF · CPT · CIP · DAP · DPU · DDP 중에서 골라 주세요."
ERR_PRESENT_DAYS = "서류 제시 기간은 1~90 사이 숫자(일)로 입력해 주세요. 비우면 21일로 봐요."
X_ETA_BEFORE = "ETA({eta})가 ETD({etd})보다 빨라요. 두 날짜를 확인해 주세요."
X_ETA_SAME = "ETA와 ETD가 같은 날이에요. 도착일이 맞는지 확인해 주세요."
X_CUTOFF_AFTER = "서류 마감({cutoff})이 ETD({etd})보다 늦어요. 서류 마감은 출항 전이에요."
X_TRANSIT_LONG = "운항 기간이 {days}일이에요. 날짜 오타가 아닌지 확인해 주세요."
X_CUTOFF_EARLY = "서류 마감이 ETD보다 {days}일 앞이에요. 날짜 오타가 아닌지 확인해 주세요."
X_ETD_FAR = "ETD가 오늘부터 {days}일 뒤예요. 연도 오타가 아닌지 확인해 주세요."
X_LC_CONFIRM = "L/C 선적 기한 두 번 입력한 값이 달라요 ({a} / {b}). L/C 원본 44C 칸을 다시 확인해 주세요."
X_EXPIRY_MISSING = "L/C 유효기한(31D)이 비어 있어요. L/C 원본을 보고 채워 주세요."
X_EXPIRY_BEFORE = "L/C 유효기한({exp})이 선적 기한({ship})보다 빨라요. L/C 원본 31D · 44C 칸을 확인해 주세요."
X_PRESENT_SHORT = "{base}부터 유효기한까지 서류 낼 시간이 {days}일뿐이에요 (L/C 기준 {need}일). 서류 준비 일정을 확인해 주세요."
X_44E = "L/C 선적항(44E)이 오더 선적항과 달라요: L/C \"{lc}\" · 오더 {port}"
X_44F = "L/C 도착항(44F)이 오더 도착항과 달라요: L/C \"{lc}\" · 오더 \"{pod}\""
X_INCO_MISSING = "인코텀즈가 비어 있어요. PI · L/C에 적힌 조건을 채워 주세요."
X_INCO_LOADING = "{term} 지정 장소는 선적항이어야 해요: 지정 장소 \"{place}\" · 선적항 {port}"
X_INCO_DISCHARGE = "{term} 지정 장소는 도착항이어야 해요: 지정 장소 \"{place}\" · 도착항 \"{pod}\""
X_DUP = "같은 {field}({value})가 {others}에도 있어요. 합적(같은 컨테이너에 여러 오더)이 아니면 오타를 확인해 주세요."
CHECK_TITLE = "입력 확인 필요"
CHECK_ALERT = "입력 확인 필요 {n}건"
