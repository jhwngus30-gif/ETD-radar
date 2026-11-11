# 📡 ETD 레이더 (etd-radar)

> 밀린 ETD와 L/C 선적 기한 위험을 한눈에 잡아내는 선적 일정 레이더

**🔗 배포 주소:** (Vercel 배포 후 여기에 주소를 적어 주세요)

## 왜 만들었나
종합상사 신입 해외영업 담당자는 오더 여러 건의 ETD를 선사·포워더 메일로 따로 확인하다 보니,
일정이 밀린 건을 늦게 알아채고 ETD가 밀려 **L/C 선적 기한을 넘기거나 기한 직전에야** 알게 됩니다.
ETD 레이더는 오더별 ETD와 L/C 선적 기한을 한곳에 모아 위험을 먼저 보여 줍니다.

## 기능
| | 기능 | 핵심 |
|---|---|---|
| F1 | 오더 등록 · 목록 | ETD 빠른 순 정렬, 한국어 입력 안내, 한국·바이어 현지 오늘 날짜, 숨기기 삭제 · 복구, 선적 완료(B/L 선적일) |
| F2 | L/C 선적 기한 경고 | 여유 일수 = L/C 기한 − ETD → 🔴 초과 / 🟡 0~7일 임박 / 🟢 8일 이상, 선적 완료는 실제 선적일로 최종 판정, **보고용 한 문장** |
| F3 | ETD 변경 기록 | 사유 필수 · 추가만 하는 변경 기록, "처음 ETD보다 9일 늦어짐 (2회 변경)", 선사 조회 **데모** |

- 임박 기준 7일: 정기선은 주 1회 운항이 많아 **롤오버 한 번에 ETD가 약 1주** 밀리기 때문
- 모든 회사명 · 오더는 **가상 데이터**이며, 선사 조회는 실제 선사와 연결되지 않은 데모입니다.

## AI 직원 팀 (Claude Code 서브에이전트)
| 직원 | 하는 일 | 권한 |
|---|---|---|
| 🧪 `date-tester` | PRD 완료 기준을 pytest로 시험 (경계값 −1·0·7·8일, 시차, 없는 날짜) | 읽기 · 쓰기(`tests/`만) · 실행 |
| 📋 `spec-checker` | PRD 완료 기준 · 「하지 않을 것」 위반 판정, 출시 가능 여부 | 읽기만 |
| ⭐📝 `report-checker` | 경고 문장이 오더번호 · 날짜 · 일수를 담아 상사 보고에 그대로 쓸 수 있는지 검사 | 읽기만 |

업무 매뉴얼 `/radar-ship` : 기능 고르기 → 만들기 → 직원 3명 검사 → 고치고 재검사 → 출시 표시.

## 폴더 구성
```
PRD.md          기획서 (기능 · 완료 기준 · 하지 않을 것)
CLAUDE.md       회사 규칙 (데이터 보호 · 한국어 에러 · 허락 없이 배포 금지 …)
STAFF.md        직원 설계표
.claude/        서브에이전트 3명 · 업무 매뉴얼 /radar-ship
logic.py        계산 · 입력 검사   storage.py  파일 읽기 · 쓰기
app.py          Streamlit 화면     config.py / messages.py  설정 · 문구
tests/          pytest 테스트 (52개)
data/           가상 데이터 (orders.csv · etd_changes.csv · carrier_demo.json)
web/index.html  배포용 웹 대시보드 (같은 규칙 · 같은 가상 데이터)
```

## 실행
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py     # 로컬 앱
python -m pytest -q                # 테스트
```
웹 대시보드(`web/`)는 정적 페이지라 Vercel에 **Root Directory = `web`** 으로 배포합니다.
