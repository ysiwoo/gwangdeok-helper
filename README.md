# 광덕고 학교생활 도우미

광덕고등학교 학생·교사·방문객을 위한 학교생활 도우미입니다. (정보 수행평가)
학교 일정 D-day, 교실 찾기(3D 캠퍼스 길 안내), 시험 자료 찾기, 오답 분석(학생), 수행평가 등록(플래너), 방문 안내(방문객),
이번 달 급식(모두), 공유(웹 주소·QR코드), 탭별 **AI 도우미**를 **파이썬**으로 처리하고, HTML·JavaScript는 파이썬이 만든 결과를 **보여주는 화면**으로만 씁니다.

- 평가 요소: 입출력(`input`/`print`), 함수, 파일 입출력(읽기·쓰기)
- 사용한 라이브러리: 표준 라이브러리(`re`, `datetime`, `urllib`, `http.server`, `json` 등) + `matplotlib`(그래프) + `qrcode`(QR코드). AI(Gemini API)는 표준 라이브러리 `urllib`로 호출합니다.
- **데이터는 모두 메모장(.txt) 파일**에 저장합니다. 첫 줄은 제목, 둘째 줄부터 한 줄에 한 건, 칸 사이는 Tab입니다. 메모장으로 열어 읽고 고칠 수 있습니다. (UTF-8)
- 설치: `pip install matplotlib qrcode`

---

## 1. 실행 방법

프로그램은 두 가지 방식으로 실행할 수 있고, **두 방식 모두 같은 파이썬 함수를 씁니다.**

### ① 앱 모드 (화면으로 쓰기)
- 이 폴더 안의 **`학교생활 도우미 실행.bat`**을 더블클릭합니다. (폴더를 다른 곳이나 다른 컴퓨터로 옮겨도 그대로 실행됩니다)
- 바탕화면 **「학교생활 도우미」** 아이콘을 더블클릭합니다.
- 또는 터미널에서 `pythonw python/app.py` (창 없이) / `python python/app.py`를 실행합니다.
- 실행하면 다음 순서로 동작합니다.
  1. 파이썬이 내 컴퓨터 안에서만 쓰는 작은 서버(`127.0.0.1:8765`)를 켭니다.
  2. Edge가 주소창 없는 앱 창으로 열립니다.
  3. 앱 창을 닫으면 약 2분 뒤 서버도 스스로 꺼집니다.
- 이미 켜져 있을 때 다시 실행하면, 예전 서버를 끄고 고친 코드로 새로 켭니다.

### ② 콘솔 모드 (input / print 메뉴)
- 바탕화면 **「학교생활 도우미 (콘솔)」** 아이콘을 누르거나, `run.bat`을 실행하거나, `python python/main.py`를 실행합니다.

```
========== 광덕고 학교생활 도우미 ==========
 [학생]
  1 학교 일정 업데이트      5 시험 기록 입력
  2 D-day 보기              6 오답 기록 입력
  3 교실 목록 만들기        7 오답 분석·보고서 저장
  4 교실 검색              11 시험 자료 찾기
 [방문객 · 교사 · 모두]
  8 방문 안내 (어디로 가야 하나요?)
  9 수행평가 등록
 10 이번 달 급식
 12 공유 (웹 주소·QR코드)
 13 스터디 플래너 (할 일·공부 시간)
  0 종료
```

### 처음 한 번만 하는 설정
| 할 일 | 방법 |
|---|---|
| 설정 파일 만들기 | `python/config.example.txt`를 복사해 이름을 `python/config.txt`로 바꾸고 메모장으로 엽니다. `config.txt`는 `.gitignore`에 들어 있어 git에 올라가지 않습니다. |
| 나이스 인증키 | `NEIS_API_KEY =` 뒤에 키를 넣습니다. 없으면 학사일정을 5건만 받습니다. 발급: [open.neis.go.kr](https://open.neis.go.kr) |
| Gemini API 키 (무료) | `GEMINI_API_KEY =` 뒤에 키를 넣습니다. 없으면 AI 기능이 꺼지고 안내 문구가 나옵니다. 발급: [aistudio.google.com](https://aistudio.google.com) — 무료 등급은 하루·분당 사용량 제한이 있고, 보낸 내용이 서비스 개선에 쓰일 수 있습니다. |
| 교실 목록 만들기 | 콘솔 메뉴 3을 실행하거나, 앱 「교실 찾기」 탭에서 「교실 목록 만들기」를 누릅니다. |
| 수행평가 일정 | 앱 「스터디 플래너」 탭의 「수행평가 등록」(또는 콘솔 메뉴 9)에서 등록합니다. `data/performance.txt`를 메모장으로 열어 `과목[Tab]날짜[Tab]내용` 한 줄을 직접 적어도 됩니다. |
| 공유 (처음 한 번) | ① GitHub에 새 저장소(예: `gwangdeok-helper`, Public)를 만듭니다. ② `config.txt`에 `GITHUB_REPO = https://github.com/아이디/gwangdeok-helper.git`, `SHARE_URL = https://아이디.github.io/gwangdeok-helper/`를 적습니다. ③ 「웹에 올리기」(또는 메뉴 12 → y)를 한 번 누른 뒤, 저장소 Settings → Pages에서 Branch를 `main` / `(root)`로 저장합니다. 처음 올릴 때 GitHub 로그인 창이 뜹니다. |

---

## 2. 앱 화면 (위쪽 탭으로 이동, 페이지가 넘어가지 않음)

| 탭 | 내용 | 화면을 만드는 곳 |
|---|---|---|
| **스터디 플래너** (첫 화면) | 다가오는 시험·수행평가 D-day, 오늘 할 일·공부 계획(추가·완료 표시), 공부 시간 기록과 최근 7일 과목별 합계, 월간 달력(일~토, 학교 시험·수행평가 자동 표시), 수행평가 등록 | 파이썬 `planner.py` + `screens.py` |
| **학교 일정** | 날짜순 일정, 분류별 색(시험 빨강 · 수행평가 파랑 · 행사 초록 · 기타 회색), 남은 일정마다 D-day, 「일정 업데이트」 버튼. 아래 **공유** 카드: 「공유 페이지 만들기」·「웹에 올리기」, 웹 주소와 QR코드 | 파이썬 `screens.py` |
| **급식** | 이번 달 날짜별 중식·석식, 칼로리, 메뉴별 알레르기 이름 | 파이썬 `screens.py` |
| **교실 찾기** | 교실·반 검색, 건물별·층별 방 개수 표, 「3D에서 보기」 버튼 | 파이썬 `screens.py` |
| **시험 자료** | 시험 이름·연도·월로 검색(예: "2026 9월 모평"), 빠른 선택(수능·모평·학평), 기출문제를 받는 공식 사이트(평가원·EBSi)로 연결 | 파이썬 `screens.py` |
| **오답 노트** | 시험·오답 입력, 공부 우선순위 TOP 5, 복습 날짜, 오답률 막대·그래프, 최근 기록 | 파이썬 `screens.py` |
| **3D 캠퍼스** | 3D 캠퍼스 모델. 위쪽 검색창에서 교실을 찾으면 그 건물·층으로 이동해 주황색으로 강조합니다. | `index.html` (기존 작품) + 파이썬 서버의 교실 검색 |
| **방문객** | 방문 목적 버튼 11개(행정실·보건실·Wee 클래스 등) → 누르면 3D 캠퍼스에서 위치 표시 | 파이썬 `screens.py` |

버튼을 누르면 파이썬 함수가 실행되고, 콘솔에서 `print`로 나오던 내용은 화면의 **「실행 기록」** 칸에 그대로 보입니다.

**AI 도우미:** 학교 일정·급식·교실 찾기·시험 자료·오답 노트·방문객 탭 아래에 「AI에게 물어보기」가 있습니다. 파이썬이 그 탭의 자료(메모장 파일)를 함께 보내, 우리 학교 자료를 근거로 답합니다. (예: 오답 노트 → "내 오답으로 공부 계획 세워 줘", 급식 → "오늘 급식에 우유 들어간 메뉴 있어?") 스터디 플래너 탭에서도 할 일·공부 시간·D-day를 근거로 물어볼 수 있습니다. 무료인 Google Gemini API(Flash-Lite, 바쁘면 Flash로 다시 시도)를 씁니다.

---

## 3. 파일 구조

```
Programming assignment/
├─ python/                    ← 파이썬 프로그램 (평가 대상)
│  ├─ main.py                 콘솔 모드 메뉴 (input/print)
│  ├─ app.py                  앱 모드 (http.server로 화면 보내기, 앱 창 열기)
│  ├─ screens.py              앱 화면(HTML 조각) 만들기
│  ├─ planner.py              스터디 플래너 (할 일, 공부 시간, D-day, 달력)
│  ├─ schedule.py             1. 학교 일정 수집기
│  ├─ rooms.py                2. 교실 데이터·검색
│  ├─ wrong_notes.py          3. 오답 분석기
│  ├─ visitors.py             방문 안내 (방문객)
│  ├─ meal.py                 오늘의 급식 (모두)
│  ├─ exam_finder.py          시험 자료 찾기
│  ├─ share.py                공유 (공유 페이지·파일 만들기, GitHub에 올리기, QR코드)
│  ├─ ai_helper.py            AI 도우미 (Gemini API: 탭별 질문)
│  ├─ textdb.py               메모장(.txt) 표 파일 읽기·쓰기 (모든 데이터가 사용)
│  └─ config.example.txt      설정 예시 (나이스·Gemini 키, 공유 주소) → config.txt로 복사
├─ data/                      ← 파이썬이 읽고 쓰는 파일
│  ├─ todos.txt               할 일·공부 계획 (날짜, 할 일, 완료)
│  ├─ study_time.txt          공부 시간 기록 (날짜, 과목, 분)
│  ├─ performance.txt         수행평가 일정 (플래너·메뉴 9로 등록 · 메모장으로 직접 입력)
│  ├─ places.txt              방문 안내 장소 (목적·건물·층·방 이름·설명)
│  ├─ exam_list.txt           시험 목록 (날짜·학년·종류·시험명·주관·링크·안내)
│  ├─ meal.txt                급식 (자동 생성, 한 줄에 메뉴 하나)
│  ├─ schedule.txt            학사일정 + 수행평가 (자동 생성)
│  ├─ rooms.txt               교실 목록 (자동 생성)
│  ├─ exams.txt               시험 기록 (입력하면 생성)
│  ├─ wrong_answers.txt       오답 기록 (입력하면 생성)
│  └─ reports/                분석보고서_날짜.txt, 과목별오답률_날짜.png, 복습일정.txt
├─ docs/                      공유 페이지·메모장 파일·qr.svg (share.py가 만듦, GitHub Pages가 웹 주소로 보여 주는 폴더)
├─ app.html                   앱 화면 틀 (탭 전환만 하는 JS)
├─ schedule.html              파이썬이 만든 일정 페이지 (JS 없음, 더블클릭으로 열림)
├─ assets/app.ico             앱 아이콘
├─ 학교생활 도우미 실행.bat    앱 모드 실행 (더블클릭)
├─ run.bat                    콘솔 모드 실행
├─ index.html                 3D 캠퍼스 (src/를 합쳐 만든 파일, 기존 작품)
├─ src/                       3D 캠퍼스 소스 (data.js = 건물·층·방 데이터)
├─ build.mjs                  src/ → index.html 빌드 스크립트
└─ models/                    3D 모델 파일(.glb)
```

- 코드 비율(빈 줄 제외 줄 수): **파이썬 약 56%**, HTML 약 28%, JavaScript 약 16%. 스터디 플래너도 파이썬(`planner.py`)으로 만들었고, HTML·JavaScript는 3D 캠퍼스(기존 작품)와 화면 틀입니다.

---

## 4. 기능별 함수 목록

표시: **[입력]** `input` 사용 · **[출력]** `print` 사용 · **[읽기]** 파일 읽기 · **[쓰기]** 파일 쓰기

### main.py — 콘솔 메뉴
| 함수 | 하는 일 | 표시 |
|---|---|---|
| `show_menu` | 메뉴를 보여준다 | [출력] |
| `input_menu_number` | 메뉴 번호를 입력받는다 (0~13이 아니면 다시) | [입력] |
| `main` · `run_menu` | 메뉴를 반복하며 고른 기능을 실행, 0이면 종료 (Ctrl+C·Ctrl+Z로 끝내도 오류 화면 없이 종료) | [입력] [출력] |

### schedule.py — 1. 학교 일정 수집기
| 함수 | 하는 일 | 표시 |
|---|---|---|
| `load_config` | `config.txt`(메모장, `이름 = 값`)에서 인증키를 읽는다 | [읽기] |
| `read_url` · `neis_request` | 주소에 접속해 글자 받기, 나이스 API 요청해 행 목록 받기 | |
| `check_robots` | robots.txt를 읽어 그 페이지를 수집해도 되는지 출력. 표준(RFC 9309)대로 robots.txt가 없으면(404) 허용, 접속 불가·403이면 크롤링 안 함, 있으면 규칙대로 | [출력] |
| `find_school_code` | 나이스 학교 기본정보 API로 교육청·학교 코드를 찾는다 (코드를 직접 적지 않음) | [출력] |
| `fetch_school_schedule` | 나이스 학사일정 API로 오늘부터 1년치 일정을 받는다 | [출력] |
| `is_skipped` | 목록에서 뺄 일정인지 확인 (`SKIP_TITLES` = 토요휴업일) | |
| `classify` | 학사일정 제목 낱말로 "시험" / "행사" / "기타" 분류 (`EXAM_WORDS`, `EVENT_WORDS`). 수행평가는 수행평가 파일에서 읽음 | |
| `read_performance` | `performance.txt`를 읽는다 | [읽기] |
| `save_schedule` / `load_schedule` | `schedule.txt` 저장 / 읽기 | [쓰기] / [읽기] |
| `calc_dday` · `upcoming_schedules` · `dday_text` | D-day 계산, 지난 일정 제외 후 가까운 순 정렬 | |
| `make_schedule_item` · `make_schedule_page` | 일정을 HTML로 만든다 | |
| `save_schedule_page` | `schedule.html` 저장 | [쓰기] |
| `update_schedule` | 메뉴 1: robots 확인 → 학사일정 받기 → 수행평가와 합치기 → 저장 | [출력] |
| `show_dday` | 메뉴 2: D-day를 가까운 순으로 출력 | [출력] |
| `check_subject` · `check_day` · `check_content` | 수행평가 검사: 과목 빈 칸 / 날짜 형식·지난 날짜 / 내용 빈 칸 (기획서 알고리즘 1의 문구) | |
| `make_performance_record` | 과목 → 날짜 → 내용 순서로 검사해 기록을 만든다 (앱이 씀) | |
| `performance_done_text` | "수행평가가 등록되었습니다 (D-7)" 문구 | |
| `add_performance` | `performance.txt`를 이어쓰기(`"a"`)로 열어 과목·날짜·내용을 Tab으로 한 줄 저장 | [쓰기] |
| `saved_school_schedules` | 저장된 일정에서 학사일정만 고르기 (새로 받지 못했을 때 예전 일정을 지우지 않게) | [읽기] |
| `rebuild_with_performance` | 학사일정은 다시 받지 않고 수행평가 부분만 다시 합쳐 json·html·js 저장 | [출력] [쓰기] |
| `register_performance` | (플래너 화면) 수행평가 검사 → `performance.txt`에 추가 → 학교 일정에 반영 | [쓰기] |
| `input_until_ok` | 검사를 통과할 때까지 입력받기 (틀리면 이유 출력) | [입력] [출력] |
| `input_performance` | 메뉴 9 (알고리즘 1): 과목 → 날짜 → 내용 입력, 틀린 칸만 다시 입력 → 저장 → 일정 반영 → 완료·D-day 출력 | [입력] [출력] [쓰기] |

### rooms.py — 2. 교실 데이터·검색
| 함수 | 하는 일 | 표시 |
|---|---|---|
| `read_data_js` | 3D 캠퍼스의 `src/data.js`를 읽는다 | [읽기] |
| `split_top_level` · `find_closing` · `inside` · `get_const` | 괄호·따옴표를 고려해 자바스크립트 글자를 나누고 찾는 도우미 | |
| `calc_number` · `eval_name` | `f+'0'+(i+1)+'호 기숙사'` 같은 방 이름 식을 계산 | |
| `parse_room_items` | `RM(...)`, `CLS(...)`, `...D_SVC`, `...J_SVC(2)`, `.map(...)`을 읽어 방 목록으로 | |
| `call_room_function` · `parse_floors` · `parse_buildings` | 함수형 방 묶음, 층 정보, `forEach push`, 건물 목록(BLD) 읽기 | |
| `floor_label` | 층 이름 정하기: 3D 캠퍼스와 같은 규칙으로 계단실·물탱크실만 있는 층은 "옥탑", 체육관 2층은 "2층 관람석" | |
| `extract_rooms` | 계단·복도·화장실·뚫린 공간·연결복도 제외, 같은 건물·층의 같은 이름 합치기, 층 이름 붙이기 | |
| `save_rooms` / `load_rooms` | `rooms.txt` 저장 / 읽기 | [쓰기] / [읽기] |
| `count_rooms` · `print_room_counts` | 건물별·층별 방 개수 계산·출력 (예: 만대관 … 4층 6, 옥탑 1) | [출력] |
| `is_class_number` · `search_rooms` | 검색. `2-3` 같은 반 이름은 반 번호가 정확히 같은 방만 (2-1 검색에 2-10 제외) | |
| `room_text` | "덕린관 4층 Lincoln 2-3", "만대관 옥탑 물탱크실" 형식 글자 | |
| `make_rooms` | 메뉴 3: 교실 목록 만들기 + 개수 출력 | [출력] |
| `search_menu` | 메뉴 4: 검색어를 입력받아 결과 출력 (없으면 안내) | [입력] [출력] |

### wrong_notes.py — 3. 오답 분석기
| 함수 | 하는 일 | 표시 |
|---|---|---|
| `load_exams` · `load_wrongs` | 시험·오답 기록 불러오기 (없으면 새 파일 생성) | [읽기] |
| `add_exam` · `add_wrong` | 기록 한 건을 파일 끝에 덧붙이기 (이어서 기록, `"a"` 모드) | [쓰기] |
| `to_int` · `make_exam_record` · `make_wrong_record` | 입력값 검사 (숫자인지, 맞은 수 ≤ 전체 문항 수, 틀린 이유 번호 1~4). 콘솔과 앱이 함께 씀 | |
| `input_text` · `input_number` · `input_date` | 올바른 값이 나올 때까지 다시 입력받기 (날짜는 Enter = 오늘) | [입력] |
| `input_exam` | 메뉴 5: 시험 기록 입력 → `exams.txt` | [입력] [출력] [쓰기] |
| `input_wrong` | 메뉴 6: 오답 기록 입력 → `wrong_answers.txt` | [입력] [출력] [쓰기] |
| `subject_wrong_rates` | 과목별 오답률 = (전체 − 맞은 수) ÷ 전체 × 100, 과목별 합산 | |
| `unit_wrong_counts` · `reason_counts` | 단원별 오답 수, 틀린 이유별 개수·비율 | |
| `next_exam` | `schedule.txt`에서 가장 가까운 "시험"까지 남은 일수 (없으면 30일) | |
| `priority_score` | **우선순위 공식**: 오답 수 × 10 ÷ (남은 일수 + 1) — 공식을 바꾸려면 이 함수만 고치면 됨 | |
| `study_priorities` | 점수 높은 순 상위 5개 단원 | |
| `review_dates` | 복습 날짜 (기록일 + 1일·3일·7일) | |
| `upcoming_reviews` | 아직 안 지난 복습 날짜 모으기 (보고서·화면에 표시) | |
| `analyze` · `make_report_text` | 모든 분석 계산, 보고서 글자 만들기 | |
| `save_report` | `reports/분석보고서_날짜.txt` | [쓰기] |
| `save_chart` | `reports/과목별오답률_날짜.png` (matplotlib, 맑은 고딕으로 한글 처리) | [쓰기] |
| `save_review_schedule` | `reports/복습일정.txt` | [쓰기] |
| `analyze_and_save` | 메뉴 7: 분석 출력 + 보고서·그래프·복습 일정 저장 | [출력] [쓰기] |

### planner.py — 스터디 플래너
| 함수 | 하는 일 | 표시 |
|---|---|---|
| `is_day` | 날짜 형식(연도-월-일) 검사 | |
| `load_todos` · `add_todo` · `toggle_todo` · `todos_on` | 할 일 읽기, 검사 후 덧붙이기(`"a"`), 완료 표시 바꿔 다시 쓰기(`"w"`), 그날 할 일 고르기 | [읽기] [쓰기] |
| `load_study_times` · `add_study_time` | 공부 시간 읽기, 검사(과목·날짜·1~1440분) 후 덧붙이기 | [읽기] [쓰기] |
| `week_study_totals` · `minutes_text` | 최근 7일 과목별 합계, "1시간 30분" 글자 | |
| `school_events` · `planner_ddays` | 학교 일정에서 시험·수행평가만 골라 D-day 가까운 5개 | [읽기] |
| `month_weeks` · `day_summary` | 일요일 시작 월간 달력, 날짜 칸에 넣을 시험·수행평가와 할 일 개수 | |
| `print_today` · `planner_menu` | 메뉴 13: 오늘의 플래너 출력, 할 일 추가·완료 표시·공부 시간 입력 | [입력] [출력] [쓰기] |

### textdb.py — 메모장(.txt) 표 파일 (모든 데이터 파일이 사용)
| 함수 | 하는 일 | 표시 |
|---|---|---|
| `read_table` | 첫 줄은 제목, 둘째 줄부터 Tab으로 나눠 딕셔너리 리스트로 읽기 (없으면 새로 만듦) | [읽기] |
| `write_table` | 표 전체를 새로 쓰기 (`"w"` 모드) | [쓰기] |
| `append_row` | 표 끝에 한 줄 덧붙이기 (`"a"` 모드, 메모장에서 끝 줄바꿈 없이 저장해도 안전) | [쓰기] |
| `clean` · `make_line` | 값 속 Tab·줄바꿈 정리, 한 줄 만들기 | |

### ai_helper.py — AI 도우미 (Google Gemini API, 무료)
| 함수 | 하는 일 | 표시 |
|---|---|---|
| `get_api_key` · `is_enabled` | `config.txt`의 `GEMINI_API_KEY` 확인 (없으면 기능 꺼짐) | [읽기] |
| `to_gemini_contents` · `call_gemini` · `answer_text` | 대화를 Gemini 형식으로 바꾸기, `urllib`로 요청 보내기, 응답에서 답 글자 꺼내기 | |
| `ask_ai` | Gemini에 질문. 모델이 바쁘거나 늦으면 다음 모델로 다시 시도, 키 오류·사용량 초과·연결 오류를 한국어로 안내 | |
| `lines_of` | 표 자료를 한 줄에 한 건씩 글자로 바꾸기 (AI에게 보낼 자료) | |
| `category_data` | 탭에 맞는 자료를 메모장 파일들에서 읽어 글자로 만들기 | [읽기] |
| `ask_for_tab` | 탭별 역할(`CATEGORY_GUIDE`) + 자료 + 질문으로 AI에게 묻기 | |

### visitors.py — 방문 안내 (방문객)
| 함수 | 하는 일 | 표시 |
|---|---|---|
| `load_places` | `places.txt`를 읽는다 | [읽기] |
| `find_room` | 안내 장소가 `rooms.txt`에 실제로 있는지 찾는다 | |
| `place_list` | 장소마다 실제 방 정보(건물 id·층)를 붙인 목록 | [읽기] |
| `show_places` | 메뉴 8: 방문 목적 목록 → 번호를 고르면 위치·설명 출력 (없는 번호면 다시) | [입력] [출력] |

### meal.py — 오늘의 급식 (모두)
| 함수 | 하는 일 | 표시 |
|---|---|---|
| `parse_dish` · `parse_dishes` | `"감자탕 (5.6.13)"` → 이름 `감자탕` + 알레르기 번호 `[5, 6, 13]` | |
| `allergy_text` | 알레르기 번호 → 이름 (5 → 대두) | |
| `month_range` · `make_meal` | 이번 달 첫날·말일 구하기, 나이스 한 행 → 급식 딕셔너리 | |
| `fetch_meals` | 나이스 급식 API로 이번 달 1일~말일 (인증키가 있으면 한 번에, 없으면 하루씩 요청) | [출력] |
| `save_meals` / `load_meals` | `meal.txt` 저장 / 읽기 | [쓰기] / [읽기] |
| `meals_by_day` | 날짜별로 묶기 (이번 달만) | |
| `print_meal` · `update_meals` · `show_meals` | 메뉴 10: 이번 달 급식 받기·저장 후 날짜별 출력 (알레르기 이름) | [출력] [쓰기] |

### exam_finder.py — 시험 자료 찾기
| 함수 | 하는 일 | 표시 |
|---|---|---|
| `load_exam_list` | `exam_list.txt`를 읽는다 | [읽기] |
| `exam_search_text` | 검색용 글자 만들기 (날짜를 "2026년 9월"로도, "모평"을 "모의평가"로도 찾을 수 있게) | |
| `search_exams` | 검색어의 낱말이 **모두** 들어간 시험 찾기 | |
| `link_label` | 시행 전이면 "공식 안내", 나머지는 "기출 받으러 가기" | |
| `exam_status` · `exam_line` | D-day 또는 "시행 완료", 한 줄 글자 | |
| `search_exams_menu` | 메뉴 11: 검색어를 입력받아 시험과 받을 수 있는 곳을 출력 | [입력] [출력] |

### share.py — 공유 (웹 주소·QR코드)
| 함수 | 하는 일 | 표시 |
|---|---|---|
| `app_style` · `web_links` · `make_page` · `all_rooms_card` | 앱 화면 틀(app.html)의 모양을 그대로 가져와, 앱과 같은 탭 줄·카드 모양의 웹 페이지를 만든다. 웹에는 서버가 없어 입력·버튼은 보기 전용, 「3D에서 보기」는 링크로 바꾸고 교실 찾기에는 전체 교실 목록을 붙인다 | [읽기] |
| `write_page` | `docs/`에 페이지 파일 저장 | [쓰기] |
| `make_share_pages` | 앱의 8개 탭(플래너·일정·급식·교실·시험 자료·오답 노트·3D 캠퍼스·방문객)을 `screens.py`가 만든 화면 그대로 `docs/`에 웹 페이지로 저장하고, 3D 캠퍼스·메모장 파일 5개·오답률 그래프를 복사한다 | [읽기] [쓰기] [출력] |
| `make_qr` | 웹 주소로 `docs/qr.svg`를 만들고 콘솔에도 QR코드를 그린다 | [쓰기] [출력] |
| `run_git` · `upload_share` | 프로그램 폴더를 git으로 GitHub 저장소에 올린다 (`config.txt`는 제외, GitHub Pages가 `docs/`를 웹 주소로 보여 줌) | [출력] |
| `update_share` | 만들기 → (올리기) → QR코드 | [출력] [쓰기] |
| `share_menu` | 메뉴 12: 웹에 올릴지 물어본 뒤 실행 | [입력] [출력] |

### screens.py — 앱 화면 만들기
| 함수 | 하는 일 |
|---|---|
| `capture_output` | 기능을 실행하며 `print` 출력을 모아 화면 「실행 기록」에 보여준다 |
| `card` · `log_box` · `field` · `datalist` · `bar_rows` | 카드, 실행 기록, 입력 칸, 추천 목록, 막대 표 같은 화면 부품 |
| `planner_screen` · `todo_list` · `calendar_table` · `month_buttons` · `planner_action` · `capture_planner` | 스터디 플래너 탭 (할 일, 공부 시간, 달력, 수행평가 등록)과 그 버튼 처리 |
| `schedule_screen` · `schedule_list` · `share_card` | 학교 일정 탭, 공유 카드(버튼·웹 주소·QR코드) |
| `rooms_screen` · `room_search_form` · `room_results` · `room_count_table` | 교실 찾기 탭 |
| `notes_screen` · `exam_form` · `wrong_form` · `analysis_body` · `chart_image` · `recent_records` | 오답 노트 탭 |
| `save_exam_action` · `save_wrong_action` | 입력 칸의 값을 검사해 저장하거나 틀린 이유를 보여준다 |
| `meal_screen` · `meal_day_card` | 급식 탭 |
| `exams_screen` · `exam_chips` · `exam_rows` | 시험 자료 탭 |
| `guide_screen` · `place_buttons` | 방문객 탭 |
| `coming_soon_screen` | 없는 탭·기능일 때 안내 화면 |
| `ai_card` | 탭 아래 「AI에게 물어보기」 카드 (질문 칸, 예시 질문 버튼, 답) |
| `screen_only` · `get_screen` · `do_action` · `run_action` | 탭 이름·버튼 이름에 맞는 함수를 골라 실행하고, 화면 아래에 AI 카드를 붙인다 |

### app.py — 앱 모드 서버
| 함수 | 하는 일 |
|---|---|
| `AppHandler.do_GET` · `do_POST` · `handle_api` | `/api/screen`(탭 화면), `/api/<기능>`(버튼), `/api/rooms/find`(3D 검색, JSON), `/api/ping`(창이 열려 있다는 신호), `/api/quit` 처리. `python/` 폴더(인증키)는 보내지 않음 |
| `send_html` · `send_json` | 결과를 브라우저로 보낸다 (UTF-8) |
| `start_server` · `main` | 서버 켜기 (켜져 있으면 예전 서버를 끄고 새로 켬) |
| `find_edge` · `open_window` | Edge 앱 창 열기 (없으면 기본 브라우저) |
| `watch_and_quit` | 앱 창이 닫혀 신호가 끊기면 서버 끄기 |

---

## 5. 데이터 파일 형식 (모두 메모장 .txt, 칸 사이는 Tab)

| 파일 | 열(항목) |
|---|---|
| `performance.txt` | 과목, 날짜, 내용 |
| `todos.txt` | 날짜, 할 일, 완료(O/X) |
| `study_time.txt` | 날짜, 과목, 공부 시간(분) |
| `config.txt` | `이름 = 값` 한 줄씩 (`#`은 설명): `NEIS_API_KEY`, `GEMINI_API_KEY`, `SCHOOL_NAME`, `REGION_KEYWORD`, `GITHUB_REPO`, `SHARE_URL` |
| `places.txt` | 목적, 건물, 층, 방 이름, 설명 — 방 이름은 `rooms.txt`에 있는 이름과 같아야 함 |
| `meal.txt` | 날짜, 끼니, 칼로리, 메뉴, 알레르기(예: `5.6.13`) — 이번 달, 한 줄에 메뉴 하나, 읽을 때 끼니별로 다시 묶음. 받은 시각은 파일 수정 시각 |
| `exam_list.txt` | 날짜(없으면 "역대 기출" 항목), 학년, 종류(수능·모평·학평), 시험명, 주관, 링크, 안내 — 2026년 일정은 확정 일정 기사로 확인 |
| `schedule.txt` | 날짜, 분류, 제목, 과목, 출처 |
| `rooms.txt` | 건물, 층(숫자, 3D 이동용), 층 이름(예: 4층, 옥탑), 방 이름, 종류, 건물 id, 동 — 249개 |
| `exams.txt` | 시험명, 날짜, 과목, 전체 문항 수, 맞은 수 |
| `wrong_answers.txt` | 기록일, 시험명, 과목, 단원, 문제 번호, 틀린 이유 — *기록일은 복습 날짜 계산을 위해 자동으로 넣음* |
| `reports/복습일정.txt` | 기록일, 시험명, 과목, 단원, 문제 번호, 1일 뒤, 3일 뒤, 7일 뒤 |

---

## 6. 단계별 구현 현황

| 기능 | 단계 | 결과 |
|---|---|---|
| robots.txt 확인 | 1단계 | 구현. 없으면(404) 허용, 접속이 안 되면 "허용 여부를 알 수 없음 → 크롤링 안 함", 있으면 규칙대로 |
| 나이스 학사일정 → schedule.txt | 2단계 | 구현 (대안 사용 안 함). 학교 코드는 API로 검색 |
| 키워드 분류(시험·행사·기타), performance.txt 합치기, D-day 정렬 | 1단계 | 구현 |
| data.js → rooms.txt, 개수 출력, 교실 검색 | 1단계 | 구현. Node.js로 data.js를 직접 실행한 결과와 249개 모두 일치 확인 |
| 반 이름 검색 (2-3) | 2단계 | 구현 (대안 사용 안 함) |
| 시험·오답 기록, 오답률, 단원·이유 분석, 우선순위, 보고서 | 1단계 | 구현 |
| 과목별 오답률 그래프 (matplotlib) | 2단계 | 구현 (대안 사용 안 함) |
| 복습 일정 파일 | 2단계 | 구현 (`복습일정.txt`) |
| 메뉴 프로그램 (main.py) | 1단계 | 구현 |
| 3D 캠퍼스 검색 → 건물·층 이동 | 2단계 | 구현 (대안 사용 안 함) |
| 검색한 교실 강조 | 2단계 | 구현 (주황색 상자 + 이름표) |
| 학교 일정 페이지, 분류별 색 | 1단계 | 구현 (파이썬이 `schedule.html` 생성 + 앱 「학교 일정」 탭) |
| 시험·수행평가 D-day 크게 표시 | 2단계 | 구현 |
| **(추가) 방문 안내** — 방문 목적별 위치, 3D 표시 | 1단계 | 구현 |
| **(추가) 수행평가 등록** — 플래너 새 일정 창에서 등록 (콘솔 메뉴 9) | 1단계 | 구현 |
| **(추가) 이번 달 급식** — 중식·석식, 칼로리, 알레르기 이름 | 1단계 | 구현 (원래 3단계였던 급식을 추가 기능으로 옮김) |
| **(추가) 시험 자료 찾기** — 시험 이름·연도·월로 검색, 기출 받는 공식 사이트로 연결 | 1단계 | 구현 (내려받을 수 없는 사설 모의고사는 제외) |
| **(추가) 데이터 메모장(.txt) 저장** | 1단계 | 구현 (csv·json → txt, `textdb.py`) |
| **(추가) AI 도우미** — 탭별 질문 (플래너 탭 포함) | 1단계 | 구현 (무료 Gemini API, 키 필요) |
| **(추가) 공유** — 공유 페이지·메모장 파일 → GitHub Pages 웹 주소, QR코드 | 1단계 | 구현 (올리기는 GitHub 저장소·로그인 필요) |
| 시험 범위, 우선순위 공식 비교, 행사 핀, 경로 안내 | 3단계 | 구현하지 않음 |

---

## 7. 3D 캠퍼스 고치기 (Node.js 필요)

- **3D 캠퍼스:** `src/` 안의 파일을 고친 뒤 `node build.mjs` → `index.html`이 새로 만들어집니다.
  - `src/data.js`의 `RM('이름','용도',u0,v0,u1,v1)` 한 줄이 방 하나입니다.
  - data.js를 고쳤다면 교실 목록도 다시 만드세요 (메뉴 3).
  - 길 안내 코드는 `src/model.js`의 `goRoom` 함수, 검색창은 `src/head-model.html`에 있습니다.
- 3D 캠퍼스 원본(게임 포함)은 `Desktop/gwangdeok-campus`에 그대로 있습니다.
