# schedule.py : 학교 일정 수집기
# - 학교 홈페이지 robots.txt 확인
# - 나이스 교육정보 개방 포털 API로 학사일정 받기
# - 수행평가 일정(performance.txt)과 합쳐 data/schedule.txt로 저장 (메모장 파일)
# - 오늘 기준 D-day 계산 후 가까운 순서로 출력

import os
import json
import html
import urllib.request
import urllib.parse
import urllib.robotparser
import urllib.error
from datetime import date, datetime, timedelta

import textdb

# 이 파일(python/schedule.py)의 한 단계 위 폴더 = 프로젝트 폴더
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_PATH = os.path.join(BASE_DIR, "python", "config.txt")
PERFORMANCE_PATH = os.path.join(DATA_DIR, "performance.txt")
SCHEDULE_PATH = os.path.join(DATA_DIR, "schedule.txt")

# 메모장 표 파일의 칸: 프로그램에서 쓰는 이름(KEYS)과 파일 첫 줄에 보이는 제목(LABELS)
SCHEDULE_KEYS = ["date", "category", "title", "subject", "source"]
SCHEDULE_LABELS = ["날짜", "분류", "제목", "과목", "출처"]
PERFORMANCE_KEYS = ["과목", "날짜", "내용"]   # 기획서: 과목, 날짜, 내용 순서로 한 줄
SCHEDULE_HTML_PATH = os.path.join(BASE_DIR, "schedule.html")

HOMEPAGE = "https://gwangdeok.jge.hs.kr"

# 일정 목록에서 뺄 일정 (매주 있어서 목록만 길어지는 것)
SKIP_TITLES = ["토요휴업일"]
NEIS_URL = "https://open.neis.go.kr/hub/"


# 설정 파일 python/config.txt(메모장)를 읽는다.
#   입력: quiet가 True면 파일이 없어도 안내를 출력하지 않는다 / 출력: 설정 딕셔너리 (파일이 없으면 기본값 딕셔너리)
def load_config(quiet=False):
    """[파일 읽기] 설정 파일 python/config.txt(메모장)를 읽는다.
    파일 모양: 한 줄에 "이름 = 값". # 으로 시작하는 줄은 설명이라 건너뛴다.
    입력: quiet가 True면 파일이 없어도 안내를 출력하지 않는다
    출력: 설정 딕셔너리 (파일이 없으면 기본값 딕셔너리)"""
    config = {"NEIS_API_KEY": "", "GEMINI_API_KEY": "", "SCHOOL_NAME": "광덕고등학교", "REGION_KEYWORD": "광주",
              "SHARE_URL": "", "GITHUB_REPO": ""}
    if not os.path.exists(CONFIG_PATH):
        if not quiet:
            print("※ python/config.txt 가 없습니다. config.example.txt를 복사해 인증키를 넣어 주세요.")
        return config
    with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
        for line in f.readlines():
            line = line.strip()
            if line == "" or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            config[name.strip()] = value.strip()
    return config


# 주소(url)에 접속해 받은 글자를 돌려준다.
#   입력: url 문자열 / 출력: 받은 내용(문자열). 접속에 실패하면 오류가 난다.
def read_url(url):
    """주소(url)에 접속해 받은 글자를 돌려준다.
    입력: url 문자열
    출력: 받은 내용(문자열). 접속에 실패하면 오류가 난다."""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (school project)"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


# 홈페이지의 robots.txt를 읽어 target_url을 수집해도 되는지 확인하고 결과를 출력한다.
#   입력: 홈페이지 주소, 수집할 페이지 주소(없으면 홈페이지 첫 화면) / 출력: 허용이면 True, 금지이거나 확인할 수 없으면 False
def check_robots(site_url, target_url=""):
    """[출력] 홈페이지의 robots.txt를 읽어 target_url을 수집해도 되는지 확인하고 결과를 출력한다.
    robots.txt 표준(RFC 9309)에 따라
    - robots.txt가 없으면(404 같은 4xx) 제한이 없으므로 허용
    - 접속이 안 되거나 401·403(접근 거부)이면 허용 여부를 알 수 없으므로 수집하지 않음
    - robots.txt가 있으면 그 규칙대로 판단
    입력: 홈페이지 주소, 수집할 페이지 주소(없으면 홈페이지 첫 화면)
    출력: 허용이면 True, 금지이거나 확인할 수 없으면 False"""
    if target_url == "":
        target_url = site_url + "/"
    robots_url = site_url + "/robots.txt"
    print("robots.txt 확인:", robots_url)
    try:
        text = read_url(robots_url)
    except urllib.error.HTTPError as error:
        if 400 <= error.code < 500 and error.code not in [401, 403]:
            print("  → robots.txt가 없습니다 (" + str(error.code) + "). 수집 제한이 없으므로 허용")
            return True
        print("  → robots.txt를 읽지 못했습니다 (" + str(error.code) + ")")
        print("  → 허용 여부를 알 수 없으므로 홈페이지 크롤링은 하지 않습니다.")
        return False
    except Exception as error:
        print("  → robots.txt를 읽지 못했습니다 (" + str(error) + ")")
        print("  → 허용 여부를 알 수 없으므로 홈페이지 크롤링은 하지 않습니다.")
        return False

    print("  ----- robots.txt 내용 -----")
    print(text.strip())
    print("  ---------------------------")
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(text.splitlines())
    allowed = parser.can_fetch("*", target_url)
    if allowed:
        print("  → 수집 허용")
    else:
        print("  → 수집 금지: 홈페이지 크롤링은 하지 않습니다.")
    return allowed


# 나이스 API(service)에 요청해 받은 행(row) 목록을 돌려준다.
#   입력: 서비스 이름(예: "schoolInfo"), 인증키, 요청 조건 딕셔너리 / 출력: 결과 행들의 리스트 (결과가 없으면 빈 리스트)
def neis_request(service, api_key, params):
    """나이스 API(service)에 요청해 받은 행(row) 목록을 돌려준다.
    입력: 서비스 이름(예: "schoolInfo"), 인증키, 요청 조건 딕셔너리
    출력: 결과 행들의 리스트 (결과가 없으면 빈 리스트)"""
    params["Type"] = "json"
    params["pSize"] = 1000
    if api_key != "":
        params["KEY"] = api_key
    url = NEIS_URL + service + "?" + urllib.parse.urlencode(params)
    data = json.loads(read_url(url))
    if service not in data:
        # 결과가 없을 때는 {"RESULT": {"CODE": "INFO-200", ...}} 형태로 온다
        print("  나이스 응답:", data.get("RESULT", {}).get("MESSAGE", data))
        return []
    return data[service][1]["row"]


# 학교 기본정보 API로 시도교육청 코드와 학교 코드를 찾는다.
#   입력: 인증키, 학교 이름, 지역 이름에 들어간 글자(예: "광주") / 출력: (시도교육청 코드, 학교 코드). 못 찾으면 (None, None)
def find_school_code(api_key, school_name, region_keyword):
    """[출력] 학교 기본정보 API로 시도교육청 코드와 학교 코드를 찾는다.
    입력: 인증키, 학교 이름, 지역 이름에 들어간 글자(예: "광주")
    출력: (시도교육청 코드, 학교 코드). 못 찾으면 (None, None)"""
    rows = neis_request("schoolInfo", api_key, {"SCHUL_NM": school_name})
    for row in rows:
        if region_keyword in row["LCTN_SC_NM"]:
            print("  학교 찾음:", row["SCHUL_NM"], "/", row["ORG_RDNMA"],
                  "/ 교육청 코드", row["ATPT_OFCDC_SC_CODE"], "/ 학교 코드", row["SD_SCHUL_CODE"])
            return row["ATPT_OFCDC_SC_CODE"], row["SD_SCHUL_CODE"]
    print("  학교를 찾지 못했습니다:", school_name, region_keyword)
    return None, None


# 일정 목록에서 뺄 일정인지 확인한다.
#   입력: 일정 제목 / 출력: True(뺀다) / False
def is_skipped(title):
    """일정 목록에서 뺄 일정인지 확인한다. (SKIP_TITLES에 있는 이름이면 뺀다)
    입력: 일정 제목 / 출력: True(뺀다) / False"""
    return title.strip() in SKIP_TITLES


# 분류에 쓰는 낱말 (시험을 먼저 검사한다)
EXAM_WORDS = ["고사", "시험", "평가"]
EVENT_WORDS = ["축제", "광덕제", "체육대회", "체육한마당", "수학여행", "현장체험", "체험학습", "수련", "입학식", "졸업식",
               "개학식", "방학식", "종업식", "시업식", "행사", "대회", "발표회", "캠프", "소풍", "견학", "기념식"]


# 학사일정 제목에 들어간 낱말로 분류한다.
#   입력: 일정 제목 문자열 / 출력: "시험", "행사", "기타" 중 하나 (수행평가는 수행평가 파일에서 따로 읽는다)
def classify(title):
    """학사일정 제목에 들어간 낱말로 분류한다.
    입력: 일정 제목 문자열
    출력: "시험", "행사", "기타" 중 하나 (수행평가는 수행평가 파일에서 따로 읽는다)"""
    for word in EXAM_WORDS:
        if word in title:
            return "시험"
    for word in EVENT_WORDS:
        if word in title:
            return "행사"
    return "기타"


# 나이스 학사일정 API로 오늘부터 1년 동안의 학사일정을 받는다.
#   입력: 설정 딕셔너리 / 출력: 일정 딕셔너리 리스트 [{"date", "title", "category", "subject", "source"}, ...]
def fetch_school_schedule(config):
    """[출력] 나이스 학사일정 API로 오늘부터 1년 동안의 학사일정을 받는다.
    입력: 설정 딕셔너리
    출력: 일정 딕셔너리 리스트 [{"date", "title", "category", "subject", "source"}, ...]"""
    api_key = config["NEIS_API_KEY"]
    if api_key == "":
        print("※ 인증키가 없어 나이스 API가 일정 5건만 보내 줍니다.")

    office_code, school_code = find_school_code(api_key, config["SCHOOL_NAME"], config["REGION_KEYWORD"])
    if school_code is None:
        return []

    start = date.today()
    end = start + timedelta(days=365)
    rows = neis_request("SchoolSchedule", api_key, {
        "ATPT_OFCDC_SC_CODE": office_code,
        "SD_SCHUL_CODE": school_code,
        "AA_FROM_YMD": start.strftime("%Y%m%d"),
        "AA_TO_YMD": end.strftime("%Y%m%d"),
    })

    schedules = []
    skipped = 0
    for row in rows:
        ymd = row["AA_YMD"]                       # 예: "20261119"
        day = ymd[0:4] + "-" + ymd[4:6] + "-" + ymd[6:8]
        title = row["EVENT_NM"]
        if is_skipped(title):
            skipped += 1
            continue
        schedules.append({"date": day, "title": title, "category": classify(title),
                          "subject": "", "source": "학사일정"})
    print("  학사일정", len(schedules), "건을 받았습니다. (토요휴업일 등", skipped, "건 제외)")
    return schedules


# data/performance.txt(과목, 날짜, 내용)를 읽는다.
#   입력: 없음 / 출력: 일정 딕셔너리 리스트 (분류는 모두 "수행평가")
def read_performance():
    """[파일 읽기] data/performance.txt(과목, 날짜, 내용)를 읽는다. (없으면 제목 줄만 있는 새 파일)
    입력: 없음
    출력: 일정 딕셔너리 리스트 (분류는 모두 "수행평가")"""
    schedules = []
    for row in textdb.read_table(PERFORMANCE_PATH, PERFORMANCE_KEYS, PERFORMANCE_KEYS):
        title = row["과목"] + " " + row["내용"]
        schedules.append({"date": row["날짜"], "title": title, "category": "수행평가",
                          "subject": row["과목"], "source": "수행평가"})
    print("  수행평가 일정", len(schedules), "건을 읽었습니다.")
    return schedules


# 일정 목록을 날짜순으로 정렬해 data/schedule.txt(메모장)에 저장한다.
#   입력: 일정 딕셔너리 리스트 / 출력: 없음
def save_schedule(schedules):
    """[파일 쓰기] 일정 목록을 날짜순으로 정렬해 data/schedule.txt(메모장)에 저장한다.
    입력: 일정 딕셔너리 리스트
    출력: 없음"""
    schedules.sort(key=lambda item: item["date"])
    textdb.write_table(SCHEDULE_PATH, SCHEDULE_KEYS, SCHEDULE_LABELS, schedules)
    print("저장 완료:", SCHEDULE_PATH, "(" + str(len(schedules)) + "건)")


# data/schedule.txt(메모장)를 읽는다.
#   입력: 없음 / 출력: 일정 딕셔너리 리스트 (파일이 없으면 빈 리스트)
def load_schedule():
    """[파일 읽기] data/schedule.txt(메모장)를 읽는다.
    입력: 없음
    출력: 일정 딕셔너리 리스트 (파일이 없으면 빈 리스트)"""
    if not os.path.exists(SCHEDULE_PATH):
        return []
    return textdb.read_table(SCHEDULE_PATH, SCHEDULE_KEYS, SCHEDULE_LABELS)


# D-day(남은 날 수)를 계산한다.
#   입력: "YYYY-MM-DD" 형식 날짜 문자열, 오늘 날짜(date) / 출력: 남은 일수(정수). 오늘이면 0, 지났으면 음수
def calc_dday(day_text, today):
    """D-day(남은 날 수)를 계산한다.
    입력: "YYYY-MM-DD" 형식 날짜 문자열, 오늘 날짜(date)
    출력: 남은 일수(정수). 오늘이면 0, 지났으면 음수"""
    target = datetime.strptime(day_text, "%Y-%m-%d").date()
    return (target - today).days


# 지난 일정을 빼고 D-day를 붙여 가까운 순서로 정렬한다.
#   입력: 일정 딕셔너리 리스트, 오늘 날짜(date) / 출력: "dday" 값이 추가된 일정 리스트 (가까운 순)
def upcoming_schedules(schedules, today):
    """지난 일정을 빼고 D-day를 붙여 가까운 순서로 정렬한다.
    입력: 일정 딕셔너리 리스트, 오늘 날짜(date)
    출력: "dday" 값이 추가된 일정 리스트 (가까운 순)"""
    result = []
    for item in schedules:
        dday = calc_dday(item["date"], today)
        if dday >= 0:
            new_item = dict(item)
            new_item["dday"] = dday
            result.append(new_item)
    result.sort(key=lambda item: item["dday"])
    return result


# D-day 숫자를 "D-3", "D-DAY" 같은 글자로 바꾼다.
#   입력: 남은 일수(정수) / 출력: 문자열
def dday_text(dday):
    """D-day 숫자를 "D-3", "D-DAY" 같은 글자로 바꾼다.
    입력: 남은 일수(정수)
    출력: 문자열"""
    if dday == 0:
        return "D-DAY"
    return "D-" + str(dday)


# ---------------- 일정 페이지(schedule.html) 만들기 ----------------

# 페이지 모양(CSS). 분류마다 색을 정해 둔다: 시험 = 빨강, 수행평가 = 파랑, 행사 = 초록, 기타 = 회색
PAGE_STYLE = """
body { margin: 0; background: #f3f6f4; color: #1c2a23; font-family: "Malgun Gothic", sans-serif; }
main { max-width: 720px; margin: 0 auto; padding: 24px 16px; }
h1 { margin: 0 0 4px; font-size: 26px; }
.sub { margin: 0 0 16px; color: #4f6158; font-size: 14px; }
a { color: #2f7d4f; font-weight: bold; }
.legend span { display: inline-block; margin-right: 12px; font-size: 14px; }
ul { list-style: none; padding: 0; }
li { display: flex; align-items: center; gap: 12px; background: white; border-left: 6px solid #9aa5a0;
     border-radius: 8px; padding: 10px 14px; margin: 8px 0; }
li.exam { border-left-color: #d0453b; }
li.perf { border-left-color: #2f6fd0; }
li.event { border-left-color: #2f9a55; }
li.past { opacity: 0.45; }
.date { width: 100px; color: #4f6158; font-size: 14px; }
.cat { font-size: 12px; padding: 2px 8px; border-radius: 10px; background: #e6ebe8; }
.exam .cat { background: #fbe3e1; color: #a3291f; }
.perf .cat { background: #e1ebfb; color: #1f4fa3; }
.event .cat { background: #dff3e5; color: #1f7a3f; }
.title { flex: 1; }
.dday { font-size: 24px; font-weight: bold; }
.exam .dday { color: #d0453b; }
.perf .dday { color: #2f6fd0; }
.event .dday { color: #2f9a55; }
.etc .dday { color: #6b7570; font-size: 18px; }
"""

# 분류 이름 → HTML class 이름
CATEGORY_CLASS = {"시험": "exam", "수행평가": "perf", "행사": "event", "기타": "etc"}


# 일정 하나를 HTML 목록 한 줄(<li>)로 만든다.
#   입력: 일정 딕셔너리, 오늘 날짜(date) / 출력: <li>...</li> 문자열
def make_schedule_item(item, today):
    """일정 하나를 HTML 목록 한 줄(<li>)로 만든다.
    입력: 일정 딕셔너리, 오늘 날짜(date)
    출력: <li>...</li> 문자열"""
    dday = calc_dday(item["date"], today)
    css_class = CATEGORY_CLASS.get(item["category"], "etc")
    if dday < 0:
        css_class = css_class + " past"      # 지난 일정은 흐리게

    # 아직 안 지난 일정마다 남은 날(D-day)을 표시한다
    dday_html = ""
    if dday >= 0:
        dday_html = '<span class="dday">' + dday_text(dday) + "</span>"

    # html.escape: 제목에 < > & 같은 글자가 있어도 화면이 깨지지 않게 바꿔 준다
    return ('<li class="' + css_class + '">'
            + '<span class="date">' + item["date"] + "</span>"
            + '<span class="cat">' + item["category"] + "</span>"
            + '<span class="title">' + html.escape(item["title"]) + "</span>"
            + dday_html + "</li>")


# 일정 목록 전체로 HTML 페이지 글자를 만든다.
#   입력: 일정 딕셔너리 리스트, 오늘 날짜(date) / 출력: HTML 문서 전체 문자열
def make_schedule_page(schedules, today):
    """일정 목록 전체로 HTML 페이지 글자를 만든다.
    입력: 일정 딕셔너리 리스트, 오늘 날짜(date)
    출력: HTML 문서 전체 문자열"""
    items = upcoming_schedules(schedules, today)      # 지난 일정은 빼고 가까운 순서로
    lines = []
    for item in items:
        lines.append(make_schedule_item(item, today))

    return ("<!doctype html>\n<html lang=\"ko\">\n<head>\n<meta charset=\"utf-8\">\n"
            + "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            + "<title>광덕고 학교 일정</title>\n<style>" + PAGE_STYLE + "</style>\n</head>\n<body>\n<main>\n"
            + "<h1>광덕고 학교 일정</h1>\n"
            + '<p class="sub">기준일 ' + today.strftime("%Y-%m-%d")
            + " · 파이썬 schedule.py가 만든 페이지</p>\n"
            + '<p class="legend"><span style="color:#d0453b">■ 시험</span>'
            + '<span style="color:#2f6fd0">■ 수행평가</span><span style="color:#2f9a55">■ 행사</span>'
            + '<span style="color:#9aa5a0">■ 기타</span></p>\n'
            + "<ul>\n" + "\n".join(lines) + "\n</ul>\n</main>\n</body>\n</html>\n")


# 일정 페이지를 만들어 schedule.html로 저장한다.
#   입력: 일정 딕셔너리 리스트 / 출력: 없음
def save_schedule_page(schedules):
    """[파일 쓰기] 일정 페이지를 만들어 schedule.html로 저장한다.
    입력: 일정 딕셔너리 리스트
    출력: 없음"""
    page = make_schedule_page(schedules, date.today())
    with open(SCHEDULE_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(page)
    print("일정 페이지 저장:", SCHEDULE_HTML_PATH)


# ---------------- 수행평가 등록 ----------------



# 수행평가 과목 검사.
#   입력: 과목 / 출력: 오류 메시지 (문제없으면 "")
def check_subject(subject):
    """수행평가 과목 검사. 입력: 과목 / 출력: 오류 메시지 (문제없으면 "")"""
    if subject.strip() == "":
        return "과목을 입력하세요"
    return ""


# 수행평가 날짜 검사: 연도-월-일 형식인지, 오늘보다 이전인지.
#   입력: 날짜 글자 / 출력: 오류 메시지 (문제없으면 "")
def check_day(day):
    """수행평가 날짜 검사: 연도-월-일 형식인지, 오늘보다 이전인지.
    입력: 날짜 글자 / 출력: 오류 메시지 (문제없으면 "")"""
    try:
        target = datetime.strptime(day.strip(), "%Y-%m-%d").date()
    except ValueError:
        return "날짜 형식이 맞지 않습니다"
    if target < date.today():
        return "이미 지난 날짜입니다"
    return ""


# 수행평가 내용 검사.
#   입력: 내용 / 출력: 오류 메시지 (문제없으면 "")
def check_content(content):
    """수행평가 내용 검사. 입력: 내용 / 출력: 오류 메시지 (문제없으면 "")"""
    if content.strip() == "":
        return "내용을 입력하세요"
    return ""


# 수행평가 한 건을 과목 → 날짜 → 내용 순서로 검사하고 만든다.
#   입력: 날짜 'YYYY-MM-DD', 과목, 내용 / 출력: (기록 딕셔너리, 오류 메시지). 문제가 없으면 오류 메시지는 ""
def make_performance_record(day, subject, content):
    """수행평가 한 건을 과목 → 날짜 → 내용 순서로 검사하고 만든다. (앱이 쓴다)
    입력: 날짜 'YYYY-MM-DD', 과목, 내용
    출력: (기록 딕셔너리, 오류 메시지). 문제가 없으면 오류 메시지는 "" """
    for error in [check_subject(subject), check_day(day), check_content(content)]:
        if error != "":
            return None, error
    return {"과목": subject.strip(), "날짜": day.strip(), "내용": content.strip()}, ""


# "수행평가가 등록되었습니다 (D-7)" 같은 등록 완료 문구를 만든다.
#   입력: 기록 / 출력: 문자열
def performance_done_text(record):
    """등록 완료 문구. 예) "수행평가가 등록되었습니다 (D-7)" 입력: 기록 / 출력: 문자열"""
    return "수행평가가 등록되었습니다 (" + dday_text(calc_dday(record["날짜"], date.today())) + ")"


# 수행평가 한 건을 performance.txt 끝에 과목·날짜·내용 한 줄로 덧붙인다.
#   입력: 기록 딕셔너리 / 출력: 없음
def add_performance(record):
    """[파일 쓰기] 수행평가 파일(data/performance.txt)을 이어쓰기("a")로 열고
    과목, 날짜, 내용을 Tab으로 이어 한 줄로 저장한 뒤 닫는다. (파일이 없으면 새로 만든다)
    입력: 기록 딕셔너리"""
    textdb.append_row(PERFORMANCE_PATH, PERFORMANCE_KEYS, PERFORMANCE_KEYS, record)


# 저장된 일정 파일에서 학사일정(수행평가가 아닌 것)만 골라 돌려준다.
#   입력: 없음 / 출력: 일정 딕셔너리 리스트
def saved_school_schedules():
    """[파일 읽기] 저장된 일정 파일에서 학사일정(수행평가가 아닌 것)만 골라 돌려준다.
    출력: 일정 딕셔너리 리스트"""
    school = []
    for item in load_schedule():
        if item["source"] != "수행평가" and not is_skipped(item["title"]):
            school.append(item)
    return school


# 학사일정은 다시 받지 않고, 저장된 일정의 수행평가 부분만 performance.txt로 바꿔 저장한다.
#   입력: 없음 / 출력: 없음
def rebuild_with_performance():
    """[출력][파일 쓰기] 학사일정은 다시 받지 않고, 저장된 일정의 수행평가 부분만 performance.txt로 바꿔 저장한다.
    (수행평가를 등록하면 학교 일정·플래너 D-day에 바로 나타나게)"""
    all_schedules = saved_school_schedules() + read_performance()
    save_schedule(all_schedules)
    save_schedule_page(all_schedules)


# 수행평가 한 건을 검사하고, 맞으면 performance.txt에 저장한 뒤 학교 일정에 바로 반영한다.
#   입력: 날짜 'YYYY-MM-DD', 과목, 내용 / 출력: (기록 딕셔너리, 오류 메시지). 문제가 없으면 오류 메시지는 ""
def register_performance(day, subject, content):
    """[파일 쓰기] 수행평가 한 건을 검사하고, 맞으면 performance.txt에 저장한 뒤 학교 일정에 바로 반영한다.
    (스터디 플래너의 「새 일정 → 수행평가」가 이 함수를 부른다)
    입력: 날짜 'YYYY-MM-DD', 과목, 내용
    출력: (기록 딕셔너리, 오류 메시지). 문제가 없으면 오류 메시지는 "" """
    record, error = make_performance_record(day, subject, content)
    if error != "":
        return None, error
    add_performance(record)
    rebuild_with_performance()
    return record, ""


# 검사를 통과할 때까지 입력받는다.
#   입력: 안내 문구, 검사 함수 / 출력: 입력한 글자
def input_until_ok(prompt, check):
    """[입력][출력] 검사를 통과할 때까지 입력받는다. 틀리면 이유를 출력하고 다시 입력받는다.
    입력: 안내 문구, 검사 함수 / 출력: 입력한 글자"""
    while True:
        text = input(prompt).strip()
        error = check(text)
        if error == "":
            return text
        print("  " + error)


# 메뉴 9: 수행평가 등록 (기획서 알고리즘 1)
#   입력: 없음 / 출력: 없음
def input_performance():
    """[입력][출력][파일 쓰기] 메뉴 9: 수행평가 등록 (기획서 알고리즘 1)
    과목 → 날짜 → 내용 순서로 입력받고, 틀리면 그 칸만 다시 입력받는다.
    저장 후 일정 파일을 고쳐 학교 일정·D-day·플래너 달력에 반영하고, 남은 날을 출력한다."""
    print("\n수행평가 등록")
    subject = input_until_ok("  과목: ", check_subject)
    day = input_until_ok("  날짜 (예: 2026-11-20): ", check_day)
    content = input_until_ok("  내용: ", check_content)
    record = {"과목": subject, "날짜": day, "내용": content}
    add_performance(record)
    rebuild_with_performance()
    print(performance_done_text(record))


# ---------------- main.py 메뉴에서 부르는 함수 ----------------

# 메뉴 1: robots.txt 확인 → 학사일정 받기 → 수행평가와 합치기 → schedule.txt 저장
#   입력: 없음 / 출력: 없음
def update_schedule():
    """[출력] 메뉴 1: robots.txt 확인 → 학사일정 받기 → 수행평가와 합치기 → schedule.txt 저장
    입력: 없음
    출력: 없음"""
    print("\n[1] robots.txt 확인")
    check_robots(HOMEPAGE)

    print("\n[2] 나이스 학사일정 받기")
    config = load_config()
    try:
        school = fetch_school_schedule(config)
    except Exception as error:
        print("  나이스 API 접속 실패:", error)
        school = []
    saved = saved_school_schedules()
    if len(school) == 0:
        # 새로 받지 못했으면, 저장해 둔 학사일정을 지우지 않고 그대로 쓴다
        school = saved
        print("  새로 받지 못해 예전에 저장한 학사일정", len(school), "건을 그대로 씁니다.")
    elif config["NEIS_API_KEY"] == "" and len(saved) > len(school):
        # 인증키가 없으면 5건만 오므로, 더 많이 저장해 둔 학사일정을 줄이지 않는다
        school = saved
        print("  인증키가 없어 일부만 받았습니다. 저장해 둔 학사일정", len(school), "건을 그대로 씁니다.")

    print("\n[3] 수행평가 일정 합치기")
    performance = read_performance()

    print("\n[4] 저장")
    all_schedules = school + performance
    save_schedule(all_schedules)
    save_schedule_page(all_schedules)


# 메뉴 2: schedule.txt를 읽어 지나지 않은 일정을 D-day 가까운 순서로 출력한다.
#   입력: 없음 / 출력: 없음
def show_dday():
    """[출력] 메뉴 2: schedule.txt를 읽어 지나지 않은 일정을 D-day 가까운 순서로 출력한다.
    입력: 없음
    출력: 없음"""
    schedules = load_schedule()
    if len(schedules) == 0:
        print("저장된 일정이 없습니다. 먼저 '1 학교 일정 업데이트'를 실행하세요.")
        return
    today = date.today()
    items = upcoming_schedules(schedules, today)
    print("\n오늘:", today.strftime("%Y-%m-%d"))
    if len(items) == 0:
        print("남은 일정이 없습니다.")
        return
    for item in items:
        print(dday_text(item["dday"]).rjust(6), item["date"], "[" + item["category"] + "]", item["title"])
    # 날짜가 지나면 D-day가 바뀌므로, 볼 때마다 일정 페이지도 오늘 기준으로 다시 만든다
    save_schedule_page(schedules)


# 이 파일만 따로 실행했을 때: python python/schedule.py
if __name__ == "__main__":
    update_schedule()
    show_dday()
