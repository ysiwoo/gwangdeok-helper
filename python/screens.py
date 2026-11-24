# screens.py : 앱 창에 보여줄 화면(HTML 조각)을 만드는 함수들
# 계산은 schedule.py 같은 기능 파일이 하고, 이 파일은 그 결과를 화면 모양(HTML)으로 바꾸기만 한다.
# 화면 모양(CSS)은 프로젝트 폴더의 app.html에 있다.

import io
import html
import contextlib
from datetime import date, datetime, timedelta

import os
from urllib.parse import quote, urlencode

import schedule
import rooms
import wrong_notes
import visitors
import meal
import exam_finder
import ai_helper
import share
import planner


# 함수를 실행하면서 print로 출력된 글자를 모아 돌려준다.
#   입력: 실행할 함수 / 출력: 출력된 글자(문자열)
def capture_output(func):
    """함수를 실행하면서 print로 출력된 글자를 모아 돌려준다.
    (콘솔 모드에서 화면에 나오던 내용을 앱 창에도 그대로 보여주기 위해)
    입력: 실행할 함수
    출력: 출력된 글자(문자열)"""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        func()
    return buffer.getvalue()


# 카드 하나(플래너의 흰 카드 모양)를 만든다.
#   입력: 작은 영어 제목, 카드 제목, 내용 HTML, 오른쪽 위 버튼 HTML / 출력: 카드 HTML 문자열
def card(eyebrow, title, body, actions=""):
    """카드 하나(플래너의 흰 카드 모양)를 만든다.
    입력: 작은 영어 제목, 카드 제목, 내용 HTML, 오른쪽 위 버튼 HTML
    출력: 카드 HTML 문자열"""
    return ('<section class="paper-card">'
            + '<div class="card-head"><div>'
            + '<p class="eyebrow">' + eyebrow + "</p>"
            + '<h2 class="card-title">' + title + "</h2></div>"
            + '<div class="card-actions">' + actions + "</div></div>"
            + body + "</section>")


# 파이썬이 출력한 실행 기록을 보여주는 칸을 만든다.
#   입력: 출력 글자 / 출력: HTML 문자열 (글자가 없으면 빈 문자열)
def log_box(text):
    """파이썬이 출력한 실행 기록을 보여주는 칸을 만든다.
    입력: 출력 글자
    출력: HTML 문자열 (글자가 없으면 빈 문자열)"""
    if text.strip() == "":
        return ""
    return ('<details class="log" open><summary>실행 기록 (파이썬 print 출력)</summary><pre>'
            + html.escape(text) + "</pre></details>")


# 일정 목록을 <ul>로 만든다.
#   입력: 일정 리스트, 오늘 날짜 / 출력: HTML 문자열
def schedule_list(items, today):
    """일정 목록을 <ul>로 만든다. (한 줄은 schedule.py의 make_schedule_item이 만든다)
    입력: 일정 리스트, 오늘 날짜
    출력: HTML 문자열"""
    if len(items) == 0:
        return '<p class="muted">일정이 없어요. 「일정 업데이트」를 눌러 주세요.</p>'
    rows = []
    for item in items:
        rows.append(schedule.make_schedule_item(item, today))
    return '<ul class="schedule-list">' + "".join(rows) + "</ul>"


# 교실 검색 입력 칸을 만든다.
#   입력: 지금 검색어 (입력 칸에 그대로 남겨 둠) / 출력: HTML 문자열
def room_search_form(query):
    """교실 검색 입력 칸을 만든다.
    입력: 지금 검색어 (입력 칸에 그대로 남겨 둠)
    출력: HTML 문자열"""
    return ('<form class="search" data-action="rooms/search">'
            + '<input class="input" name="q" value="' + html.escape(query) + '" '
            + 'placeholder="교실 이름이나 반 (예: 과학실, 2-3)" aria-label="찾을 교실">'
            + '<button class="btn primary">찾기</button></form>')


# 검색 결과를 "건물 이름 몇 층 방 이름" 목록으로 만든다.
#   입력: 검색어 / 출력: HTML 문자열
def room_results(query):
    """검색 결과를 "건물 이름 몇 층 방 이름" 목록으로 만든다.
    입력: 검색어
    출력: HTML 문자열"""
    all_rooms = rooms.load_rooms()
    if len(all_rooms) == 0:
        return ('<p class="muted">교실 목록이 아직 없어요. 「교실 찾기」 탭에서 '
                + '「교실 목록 만들기」를 먼저 눌러 주세요.</p>')
    if query.strip() == "":
        return ""
    found = rooms.search_rooms(all_rooms, query)
    if len(found) == 0:
        return '<p class="muted">「' + html.escape(query) + '」(이)가 들어간 교실을 찾지 못했어요.</p>'
    rows = []
    for room in found:
        place = room["building"] + " " + room["floor_name"]
        # 「3D에서 보기」: 3D 캠퍼스 화면에 건물 id·층·방 이름을 넘겨 그 교실로 이동시킨다
        target = urlencode({"b": room["building_id"], "f": room["floor"], "r": room["name"]})
        rows.append('<li><span class="place">' + html.escape(place) + "</span>"
                    + '<span class="room-name">' + html.escape(room["name"]) + "</span>"
                    + '<button class="btn small" data-room="' + html.escape(target) + '">3D에서 보기</button></li>')
    return '<ul class="room-list">' + "".join(rows) + "</ul>"


# 건물별·층별 방 개수 표를 만든다.
#   입력: 없음 / 출력: HTML 문자열
def room_count_table():
    """건물별·층별 방 개수 표를 만든다. (rooms.py의 count_rooms 결과를 표로)
    출력: HTML 문자열"""
    all_rooms = rooms.load_rooms()
    if len(all_rooms) == 0:
        return '<p class="muted">아직 교실 목록이 없어요.</p>'
    rows = []
    for building, counts in rooms.count_rooms(all_rooms):
        floor_texts = []
        for floor_name in counts:
            floor_texts.append(floor_name + " " + str(counts[floor_name]))
        rows.append("<tr><th>" + html.escape(building) + "</th><td>" + str(sum(counts.values()))
                    + "</td><td>" + ", ".join(floor_texts) + "</td></tr>")
    return ('<table class="count-table"><thead><tr><th>건물</th><th>합계</th><th>층별</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table>"
            + '<p class="muted">전체 ' + str(len(all_rooms)) + "개 · 계단·복도·화장실·연결복도 제외</p>")


UPDATE_BUTTON = '<button class="btn small primary" data-action="schedule/update" data-busy="업데이트 중… (최대 30초)">일정 업데이트</button>'


# 학교 일정 화면: 전체 일정을 날짜순으로 보여준다.
#   입력: 실행 기록 글자 (없으면 ""), 검색어(이 화면에서는 쓰지 않음) / 출력: HTML 문자열
def schedule_screen(log="", query=""):
    """학교 일정 화면: 지난 일정은 빼고, 남은 일정을 D-day가 가까운 순서로 보여준다.
    입력: 실행 기록 글자 (없으면 ""), 검색어(이 화면에서는 쓰지 않음)
    출력: HTML 문자열"""
    today = date.today()
    items = schedule.upcoming_schedules(schedule.load_schedule(), today)
    legend = ('<p class="legend"><span class="exam">시험</span><span class="perf">수행평가</span>'
              + '<span class="event">행사</span><span class="etc">기타</span></p>')
    body = legend + schedule_list(items, today)
    return (log_box(log) + card("SCHOOL CALENDAR", "학교 일정 · " + str(len(items)) + "건", body, UPDATE_BUTTON)
            + share_card())


# 공유 카드: 공유 페이지 만들기·웹에 올리기 버튼, 웹 주소와 QR코드.
#   입력: 없음 / 출력: HTML
def share_card():
    """공유 카드: 공유 페이지 만들기·웹에 올리기 버튼, 웹 주소와 QR코드. 출력: HTML"""
    url = schedule.load_config(quiet=True).get("SHARE_URL", "")
    buttons = ('<button class="btn small" data-action="share/make" data-busy="만드는 중…">공유 페이지 만들기</button> '
               + '<button class="btn small primary" data-action="share/upload" data-busy="올리는 중… (최대 3분)">웹에 올리기</button>')
    body = ('<p class="muted small">일정·급식·교실·방문 장소·시험 목록을 휴대폰에서도 볼 수 있게 docs/ 폴더에 페이지와 메모장 파일을 만들고, '
            + "GitHub에 올려 웹 주소와 QR코드로 공유해요.</p>")
    if url == "":
        body += '<p class="muted">config.txt에 SHARE_URL(웹 주소)과 GITHUB_REPO(저장소 주소)를 적어 주세요.</p>'
    else:
        body += '<p>웹 주소: <a href="' + html.escape(url) + '" target="_blank" rel="noopener">' + html.escape(url) + "</a></p>"
        if os.path.exists(share.QR_PATH):
            stamp = str(int(os.path.getmtime(share.QR_PATH)))
            body += '<img class="qr" src="docs/qr.svg?v=' + stamp + '" alt="웹 주소 QR코드" width="180" height="180">'
    return card("SHARE", "공유 · 웹 주소와 QR코드", body, buttons)


# 교실 찾기 화면: 검색 칸과 결과, 건물별·층별 방 개수 표를 보여준다.
#   입력: 실행 기록 글자, 검색어 / 출력: HTML 문자열
def rooms_screen(log="", query=""):
    """교실 찾기 화면: 검색 칸과 결과, 건물별·층별 방 개수 표를 보여준다.
    입력: 실행 기록 글자, 검색어
    출력: HTML 문자열"""
    build_button = ('<button class="btn small" data-action="rooms/build" data-busy="만드는 중…">'
                    + "교실 목록 만들기</button>")
    search_card = card("FIND A ROOM", "교실 찾기", room_search_form(query) + room_results(query))
    data_card = card("ROOM DATA", "교실 목록 (data.js에서 추출)", room_count_table(), build_button)
    return log_box(log) + '<div class="layout two">' + search_card + data_card + "</div>"


# ---------------- 오답 노트 화면 ----------------

# 입력 칸 하나(이름표 + 칸)를 만든다.
#   입력: 이름표, 칸 이름, 이전 입력값 딕셔너리, 칸 종류, 추가 속성 / 출력: HTML 문자열
def field(label, name, form, input_type="text", extra=""):
    """입력 칸 하나(이름표 + 칸)를 만든다. 전에 입력한 값이 있으면 그대로 넣어 둔다.
    입력: 이름표, 칸 이름, 이전 입력값 딕셔너리, 칸 종류, 추가 속성
    출력: HTML 문자열"""
    value = html.escape(str(form.get(name, "")))
    return ('<label class="field"><span>' + label + "</span>"
            + '<input class="input" type="' + input_type + '" name="' + name + '" value="' + value + '" ' + extra + "></label>")


# 입력 칸에서 고를 수 있는 추천 목록(datalist)을 만든다.
#   입력: 목록 id, 값 리스트 / 출력: HTML 문자열
def datalist(list_id, values):
    """입력 칸에서 고를 수 있는 추천 목록(datalist)을 만든다. 같은 이름을 다르게 쓰는 실수를 줄여 준다.
    입력: 목록 id, 값 리스트 / 출력: HTML 문자열"""
    options = ""
    for value in sorted(set(values)):
        options += '<option value="' + html.escape(value) + '">'
    return '<datalist id="' + list_id + '">' + options + "</datalist>"


# 시험 기록 입력 칸들을 만든다.
#   입력: 이전 입력값 / 출력: HTML
def exam_form(form):
    """시험 기록 입력 칸들. 입력: 이전 입력값 / 출력: HTML"""
    if "day" not in form:
        form = dict(form)
        form["day"] = date.today().strftime("%Y-%m-%d")
    return ('<form class="form-grid" data-action="notes/exam">'
            + field("시험명", "name", form, "text", 'list="exam-names" placeholder="2학기 중간고사"')
            + field("날짜", "day", form, "date")
            + field("과목", "subject", form, "text", 'list="subjects" placeholder="수학"')
            + field("전체 문항 수", "total", form, "number", 'min="1"')
            + field("맞은 수", "correct", form, "number", 'min="0"')
            + '<button class="btn primary">시험 기록 저장</button></form>')


# 오답 기록 입력 칸들을 만든다.
#   입력: 이전 입력값 / 출력: HTML
def wrong_form(form):
    """오답 기록 입력 칸들. 틀린 이유는 1~4 중에서 고른다. 입력: 이전 입력값 / 출력: HTML"""
    options = ""
    for key in wrong_notes.REASONS:
        selected = " selected" if str(form.get("reason", "")) == str(key) else ""
        options += '<option value="' + str(key) + '"' + selected + ">" + str(key) + " " + wrong_notes.REASONS[key] + "</option>"
    return ('<form class="form-grid" data-action="notes/wrong">'
            + field("시험명", "exam", form, "text", 'list="exam-names"')
            + field("과목", "subject", form, "text", 'list="subjects"')
            + field("단원", "unit", form, "text", 'list="units" placeholder="미분"')
            + field("문제 번호", "number", form, "number", 'min="1"')
            + '<label class="field"><span>틀린 이유</span><select class="input" name="reason">' + options + "</select></label>"
            + '<button class="btn primary">오답 기록 저장</button></form>')


# 막대 모양 표를 만든다.
#   입력: [(이름, 값 글자, 0~100 비율), ...] / 출력: HTML
def bar_rows(rows):
    """막대 모양 표를 만든다. 입력: [(이름, 값 글자, 0~100 비율), ...] / 출력: HTML"""
    if len(rows) == 0:
        return '<p class="muted">아직 기록이 없어요.</p>'
    html_rows = ""
    for name, value_text, percent in rows:
        html_rows += ('<div class="bar-row"><span class="bar-name">' + html.escape(name) + "</span>"
                      + '<span class="bar"><span style="width:' + format(min(percent, 100), ".1f") + '%"></span></span>'
                      + '<span class="bar-value">' + value_text + "</span></div>")
    return '<div class="bars">' + html_rows + "</div>"


# 분석 결과(과목별 오답률·틀린 이유·우선순위·단원별)를 화면 모양으로 만든다.
#   입력: wrong_notes.analyze()의 결과 / 출력: HTML
def analysis_body(result):
    """분석 결과(과목별 오답률·틀린 이유·우선순위·단원별)를 화면 모양으로 만든다.
    입력: wrong_notes.analyze()의 결과 / 출력: HTML"""
    rate_rows = []
    for subject, total, wrong, rate in result["rates"]:
        rate_rows.append((subject, format(rate, ".1f") + "% <small>(" + str(wrong) + "/" + str(total) + ")</small>", rate))
    reason_rows = []
    for reason, count, percent in result["reasons"]:
        reason_rows.append((reason, str(count) + "개 <small>(" + format(percent, ".0f") + "%)</small>", percent))

    if result["exam_title"] is None:
        exam_info = "다가오는 시험 일정이 없어 남은 일수를 " + str(wrong_notes.DEFAULT_DAYS) + "일로 계산했어요."
    else:
        exam_info = "다음 시험 「" + html.escape(result["exam_title"]) + "」까지 D-" + str(result["days_left"])
    priority = ""
    rank = 1
    for subject, unit, count, score in result["priorities"]:
        priority += ('<li><span class="rank">' + str(rank) + "</span><span>" + html.escape(subject + " · " + unit)
                     + '</span><span class="muted">오답 ' + str(count) + "개 · 점수 " + format(score, ".2f") + "</span></li>")
        rank += 1
    if priority == "":
        priority = '<li class="muted">오답 기록이 없어요.</li>'

    unit_rows = ""
    for subject, unit, count in result["units"]:
        unit_rows += "<tr><td>" + html.escape(subject) + "</td><td>" + html.escape(unit) + "</td><td>" + str(count) + "</td></tr>"
    units_table = '<p class="muted">아직 기록이 없어요.</p>'
    if unit_rows != "":
        units_table = '<table class="count-table"><thead><tr><th>과목</th><th>단원</th><th>오답 수</th></tr></thead><tbody>' + unit_rows + "</tbody></table>"

    review_rows = ""
    for day, subject, unit, number in result["reviews"][0:10]:
        review_rows += ("<tr><td>" + day + "</td><td>" + html.escape(subject) + "</td><td>"
                        + html.escape(unit + " " + number + "번") + "</td></tr>")
    reviews_table = '<p class="muted">남은 복습이 없어요.</p>'
    if review_rows != "":
        reviews_table = ('<table class="count-table"><thead><tr><th>복습 날짜</th><th>과목</th><th>문제</th></tr></thead><tbody>'
                         + review_rows + "</tbody></table>")

    return ('<h3 class="sub-title">공부 우선순위 TOP 5</h3><p class="muted small">' + exam_info
            + " · 점수 = 오답 수 × 10 ÷ (남은 일수 + 1)</p>"
            + '<ol class="priority">' + priority + "</ol>"
            + '<h3 class="sub-title">복습 날짜</h3><p class="muted small">기록일로부터 1일·3일·7일 뒤 (가까운 10개)</p>'
            + reviews_table
            + '<h3 class="sub-title">과목별 오답률</h3>' + bar_rows(rate_rows)
            + '<h3 class="sub-title">틀린 이유</h3>' + bar_rows(reason_rows)
            + '<h3 class="sub-title">단원별 오답 수</h3>' + units_table)


# 오늘 저장한 오답률 그래프가 있으면 화면에 보여준다.
#   입력: 날짜 / 출력: HTML
def chart_image(today):
    """오늘 저장한 오답률 그래프가 있으면 화면에 보여준다. 입력: 날짜 / 출력: HTML"""
    name = "과목별오답률_" + today.strftime("%Y-%m-%d") + ".png"
    if not os.path.exists(os.path.join(wrong_notes.REPORT_DIR, name)):
        return ""
    return ('<figure class="chart"><img src="data/reports/' + quote(name) + '" alt="과목별 오답률 막대그래프">'
            + "<figcaption>data/reports/" + name + "</figcaption></figure>")


# 최근 기록(시험 5건, 오답 5건)을 보여준다.
#   입력: 시험·오답 리스트 / 출력: HTML
def recent_records(exams, wrong_list):
    """최근 기록(시험 5건, 오답 5건)을 보여준다. 입력: 시험·오답 리스트 / 출력: HTML"""
    exam_rows = ""
    for exam in reversed(exams[-5:]):
        exam_rows += ("<li><span>" + html.escape(exam["날짜"] + " " + exam["시험명"] + " · " + exam["과목"]) + "</span>"
                      + '<span class="muted">' + exam["맞은 수"] + "/" + exam["전체 문항 수"] + "</span></li>")
    wrong_rows = ""
    for item in reversed(wrong_list[-5:]):
        wrong_rows += ("<li><span>" + html.escape(item["과목"] + " · " + item["단원"] + " " + item["문제 번호"] + "번") + "</span>"
                       + '<span class="muted">' + html.escape(item["틀린 이유"]) + "</span></li>")
    if exam_rows == "":
        exam_rows = '<li class="muted">없음</li>'
    if wrong_rows == "":
        wrong_rows = '<li class="muted">없음</li>'
    return ('<h3 class="sub-title">시험 (전체 ' + str(len(exams)) + '건)</h3><ul class="records">' + exam_rows + "</ul>"
            + '<h3 class="sub-title">오답 (전체 ' + str(len(wrong_list)) + '건)</h3><ul class="records">' + wrong_rows + "</ul>")


# 오답 노트 화면: 입력 칸 2개, 분석 결과, 최근 기록을 보여준다.
#   입력: 실행 기록, 검색어(쓰지 않음), 알림 문구, 오류인지, 이전 입력값, 알림을 띄울 칸("exam"/"wrong") / 출력: HTML 문자열
def notes_screen(log="", query="", message="", is_error=False, form=None, which=""):
    """오답 노트 화면: 입력 칸 2개, 분석 결과, 최근 기록을 보여준다.
    입력: 실행 기록, 검색어(쓰지 않음), 알림 문구, 오류인지, 이전 입력값, 알림을 띄울 칸("exam"/"wrong")
    출력: HTML 문자열"""
    if form is None:
        form = {}
    result = wrong_notes.analyze()
    notice = ""
    if message != "":
        notice = '<p class="notice ' + ("error" if is_error else "ok") + '">' + html.escape(message) + "</p>"

    exam_card = card("RECORD EXAM", "시험 기록 입력", (notice if which == "exam" else "") + exam_form(form if which == "exam" else {}))
    wrong_card = card("RECORD MISTAKE", "오답 기록 입력", (notice if which == "wrong" else "") + wrong_form(form if which == "wrong" else {}))
    analyze_button = '<button class="btn small primary" data-action="notes/analyze" data-busy="저장 중…">분석·보고서 저장</button>'
    analysis_card = card("ANALYSIS", "오답 분석", chart_image(result["today"]) + analysis_body(result), analyze_button)
    records_card = card("RECENT", "최근 기록", recent_records(wrong_notes.load_exams(), result["wrongs"]))

    names = []
    subjects = []
    units = []
    for exam in wrong_notes.load_exams():
        names.append(exam["시험명"])
        subjects.append(exam["과목"])
    for item in result["wrongs"]:
        names.append(item["시험명"])
        subjects.append(item["과목"])
        units.append(item["단원"])
    lists = datalist("exam-names", names) + datalist("subjects", subjects) + datalist("units", units)

    return (log_box(log) + lists + '<div class="layout two">'
            + '<div class="col">' + exam_card + wrong_card + records_card + "</div>"
            + '<div class="col">' + analysis_card + "</div></div>")


# 시험 기록 저장 버튼: 검사해서 맞으면 저장하고, 틀리면 이유를 알려준다.
#   입력: 입력값 / 출력: 화면 HTML
def save_exam_action(form):
    """시험 기록 저장 버튼: 검사해서 맞으면 저장하고, 틀리면 이유를 알려준다. 입력: 입력값 / 출력: 화면 HTML"""
    record, error = wrong_notes.make_exam_record(form.get("name", ""), form.get("day", ""), form.get("subject", ""),
                                                 form.get("total", ""), form.get("correct", ""))
    if error != "":
        return notes_screen(message=error, is_error=True, form=form, which="exam")
    wrong_notes.add_exam(record)
    message = "저장했어요: " + record["시험명"] + " " + record["과목"] + " " + str(record["맞은 수"]) + "/" + str(record["전체 문항 수"])
    return notes_screen(message=message, which="exam")


# 오답 기록 저장 버튼: 저장한 뒤 시험명·과목·단원은 남겨 두어 다음 문제를 바로 입력할 수 있게 한다.
#   입력: 입력값 / 출력: 화면 HTML
def save_wrong_action(form):
    """오답 기록 저장 버튼: 저장한 뒤 시험명·과목·단원은 남겨 두어 다음 문제를 바로 입력할 수 있게 한다.
    입력: 입력값 / 출력: 화면 HTML"""
    record, error = wrong_notes.make_wrong_record(form.get("exam", ""), form.get("subject", ""), form.get("unit", ""),
                                                  form.get("number", ""), form.get("reason", ""))
    if error != "":
        return notes_screen(message=error, is_error=True, form=form, which="wrong")
    wrong_notes.add_wrong(record)
    keep = {"exam": record["시험명"], "subject": record["과목"], "unit": record["단원"], "reason": form.get("reason", "")}
    message = "저장했어요: " + record["과목"] + " " + record["단원"] + " " + str(record["문제 번호"]) + "번 (" + record["틀린 이유"] + ")"
    return notes_screen(message=message, form=keep, which="wrong")


# ---------------- 급식 화면 ----------------

# 하루치 급식 카드를 만든다.
#   입력: 날짜, 그날 급식 리스트 / 출력: HTML
def meal_day_card(day, meals):
    """하루치 급식 카드를 만든다. 메뉴 옆에 알레르기 이름을 작게 붙인다.
    입력: 날짜, 그날 급식 리스트 / 출력: HTML"""
    when = datetime.strptime(day, "%Y-%m-%d").date()
    weekday = "월화수목금토일"[when.weekday()]
    title = str(when.month) + "월 " + str(when.day) + "일 (" + weekday + ")"
    eyebrow = "TODAY" if when == date.today() else "MEAL"
    body = ""
    for item in meals:
        dishes = ""
        for dish in item["dishes"]:
            allergy = ""
            if len(dish["allergies"]) > 0:
                allergy = '<span class="allergy">' + html.escape(meal.allergy_text(dish["allergies"])) + "</span>"
            dishes += "<li>" + html.escape(dish["name"]) + allergy + "</li>"
        body += ('<div class="meal"><p class="meal-type">' + html.escape(item["type"])
                 + ' <span class="muted">' + html.escape(item["calorie"]) + "</span></p>"
                 + '<ul class="dishes">' + dishes + "</ul></div>")
    return card(eyebrow, title, body)


# 급식 화면: 이번 달 날짜별 중식·석식, 칼로리, 알레르기 이름을 보여준다.
#   입력: 실행 기록, 검색어(쓰지 않음) / 출력: HTML
def meal_screen(log="", query=""):
    """급식 화면: 이번 달 날짜별 중식·석식, 칼로리, 알레르기 이름을 보여준다.
    입력: 실행 기록, 검색어(쓰지 않음) / 출력: HTML"""
    meals, updated = meal.load_meals()
    button = '<button class="btn small primary" data-action="meal/update" data-busy="받는 중…">급식 업데이트</button>'
    info = "나이스 급식 정보"
    if updated != "":
        info += " · " + updated + " 받음"
    days = meal.meals_by_day(meals)
    if len(days) == 0:
        body = '<p class="muted">이번 달 급식이 없어요. 「급식 업데이트」를 눌러 주세요. (방학에는 급식이 없어요)</p>'
    else:
        body = '<div class="meal-grid">'
        for day, day_meals in days:
            body += meal_day_card(day, day_meals)
        body += "</div>"
    title = "급식 · " + str(date.today().month) + "월"
    return log_box(log) + card("SCHOOL MEAL", title, '<p class="muted">' + info + "</p>", button) + body


# ---------------- 시험 자료 화면 ----------------

KIND_CLASS = {"수능": "exam", "모평": "exam", "학평": "perf"}


# 자주 쓰는 검색어 버튼 (누르면 그 검색어로 바로 찾는다).
#   입력: 지금 검색어 / 출력: HTML
def exam_chips(query):
    """자주 쓰는 검색어 버튼 (누르면 그 검색어로 바로 찾는다). 입력: 지금 검색어 / 출력: HTML"""
    chips = ""
    for word in ["전체", "수능", "모평", "학평"]:
        value = word
        if word == "전체":
            value = ""
        selected = ""
        if query.strip() == value:
            selected = " on"
        chips += ('<form data-action="exams/search"><input type="hidden" name="q" value="' + value + '">'
                  + '<button class="chip' + selected + '">' + word + "</button></form>")
    return '<div class="chips">' + chips + "</div>"


# 찾은 시험 목록을 공식 사이트 링크와 함께 만든다.
#   입력: 시험 리스트, 오늘 날짜 / 출력: HTML
def exam_rows(found, today):
    """찾은 시험 목록. 시험마다 기출문제를 받는 공식 사이트로 연결한다.
    입력: 시험 리스트, 오늘 날짜 / 출력: HTML"""
    rows = ""
    for exam in found:
        info = exam["학년"] + " · " + exam["주관"]
        if exam["날짜"] != "":
            info = exam["날짜"] + " · " + info
        status = exam_finder.exam_status(exam, today)
        link_text = exam_finder.link_label(exam, today) + " ↗"
        rows += ('<li class="' + KIND_CLASS.get(exam["종류"], "etc") + '">'
                 + '<span class="cat">' + html.escape(exam["종류"]) + "</span>"
                 + '<div class="exam-main"><strong>' + html.escape(exam["시험명"]) + "</strong>"
                 + '<span class="muted">' + html.escape(info) + "</span>"
                 + "<small>" + html.escape(exam["안내"]) + "</small></div>"
                 + '<span class="exam-status">' + status + "</span>"
                 + '<a class="btn small" href="' + html.escape(exam["링크"]) + '" target="_blank" rel="noopener">'
                 + link_text + "</a></li>")
    return '<ul class="exam-list">' + rows + "</ul>"


# 시험 자료 화면: 시험 이름·연도·월로 검색하고, 기출문제를 받을 수 있는 공식 사이트로 연결한다.
#   입력: 실행 기록, 검색어 / 출력: HTML
def exams_screen(log="", query=""):
    """시험 자료 화면: 시험 이름·연도·월로 검색하고, 기출문제를 받을 수 있는 공식 사이트로 연결한다.
    입력: 실행 기록, 검색어 / 출력: HTML"""
    exams = exam_finder.load_exam_list()
    found = exam_finder.search_exams(exams, query)
    form = ('<form class="search" data-action="exams/search">'
            + '<input class="input" name="q" value="' + html.escape(query) + '" '
            + 'placeholder="예: 2026 9월 모평, 수능, 고2 학평" aria-label="시험 검색">'
            + '<button class="btn primary">찾기</button></form>')
    note = ('<p class="muted small">시험 이름·연도·월로 검색하세요. 수능·모의평가(평가원)와 학력평가(교육청) 기출문제는 '
            + "연결된 공식 사이트에서 무료로 받을 수 있어요.</p>")
    if len(found) == 0:
        result = '<p class="muted">「' + html.escape(query) + '」에 맞는 시험을 찾지 못했어요.</p>'
    else:
        result = '<p class="muted small">' + str(len(found)) + "건</p>" + exam_rows(found, date.today())
    return log_box(log) + card("PAST EXAMS", "시험 자료 찾기", note + form + exam_chips(query) + result)


# ---------------- 스터디 플래너 화면 ----------------

# 플래너의 오늘 할 일 목록(완료 버튼 포함)을 만든다.
#   입력: 날짜 / 출력: HTML
def todo_list(day):
    """그날 할 일 목록을 만든다. 왼쪽 버튼을 누르면 완료 표시가 바뀐다. 입력: 날짜 / 출력: HTML"""
    rows = ""
    for number, todo in planner.todos_on(day):
        mark, style = "○", ""
        if todo["완료"] == "O":
            mark, style = "✔", ' style="text-decoration:line-through;opacity:.55"'
        rows += ('<li><form data-action="planner/toggle"><input type="hidden" name="n" value="' + str(number) + '">'
                 + '<button class="chip" aria-label="완료 표시 바꾸기">' + mark + "</button></form>"
                 + "<span" + style + ">" + html.escape(todo["할 일"]) + "</span></li>")
    if rows == "":
        return '<p class="muted">오늘 할 일이 없어요. 아래에서 추가해 보세요.</p>'
    return '<ul class="records todo-list">' + rows + "</ul>"


# 월간 달력(일~토)을 만들고 시험·수행평가와 할 일 개수를 넣는다.
#   입력: 연도, 월, 오늘 날짜 / 출력: HTML
def calendar_table(year, month, today):
    """월간 달력 표를 만든다. 학교 시험·수행평가가 자동으로 들어가고, 할 일은 "끝낸 수/전체"로 보인다.
    입력: 연도, 월, 오늘 날짜 / 출력: HTML"""
    events = planner.school_events()
    todos = planner.load_todos()
    head = ""
    for name in ["일", "월", "화", "수", "목", "금", "토"]:
        head += "<th>" + name + "</th>"
    body = ""
    for week in planner.month_weeks(year, month):
        body += "<tr>"
        for column in range(7):
            number = week[column]
            if number == 0:                      # 이번 달이 아닌 칸
                body += "<td></td>"
                continue
            day = date(year, month, number)
            summary = planner.day_summary(day.strftime("%Y-%m-%d"), events, todos)
            css = ["", "sun"][column == 0] + ["", "sat"][column == 6] + ["", " today"][day == today]
            cell = '<span class="num">' + str(number) + "</span>"
            for item in summary["events"]:
                cell += ('<span class="ev ' + schedule.CATEGORY_CLASS.get(item["category"], "etc") + '" title="'
                         + html.escape(item["category"] + " · " + item["title"]) + '">' + html.escape(item["title"]) + "</span>")
            if summary["todo"] > 0:
                cell += '<span class="muted">할 일 ' + str(summary["done"]) + "/" + str(summary["todo"]) + "</span>"
            body += '<td class="' + css.strip() + '">' + cell + "</td>"
        body += "</tr>"
    return '<table class="cal"><thead><tr>' + head + "</tr></thead><tbody>" + body + "</tbody></table>"


# 달력의 이전 달·다음 달 버튼을 만든다.
#   입력: 보고 있는 연도, 월 / 출력: HTML
def month_buttons(year, month):
    """달력 위의 이전 달·다음 달 버튼. 입력: 보고 있는 연도, 월 / 출력: HTML"""
    before = date(year, month, 1) - timedelta(days=1)
    after = date(year, month, 28) + timedelta(days=7)
    buttons = ""
    for label, target in [("◀ 이전 달", before), ("다음 달 ▶", after)]:
        buttons += ('<form data-action="planner/month" style="display:inline"><input type="hidden" name="q" value="'
                    + target.strftime("%Y-%m") + '"><button class="btn small">' + label + "</button></form> ")
    return buttons


# 스터디 플래너 화면(D-day, 할 일, 공부 시간, 달력, 수행평가 등록)을 만든다.
#   입력: 실행 기록, 달력에 보여줄 달 "YYYY-MM"(비우면 이번 달), 알림 문구, 오류인지, 이전 입력값 / 출력: HTML
def planner_screen(log="", query="", message="", is_error=False, form=None):
    """스터디 플래너 화면(첫 화면): D-day, 오늘 할 일, 공부 시간, 월간 달력, 수행평가 등록을 보여준다.
    입력: 실행 기록, 달력에 보여줄 달 "YYYY-MM"(비우면 이번 달), 알림 문구, 오류인지, 이전 입력값 / 출력: HTML"""
    if form is None:
        form = {}
    today = date.today()
    day = today.strftime("%Y-%m-%d")
    notice = ""
    if message != "":
        notice = '<p class="notice ' + ("error" if is_error else "ok") + '">' + html.escape(message) + "</p>"

    dday_card = card("D-DAY", "다가오는 시험·수행평가", schedule_list(planner.planner_ddays(today), today))

    todo_form = ('<form class="form-grid" data-action="planner/todo">'
                 + field("날짜", "day", {"day": form.get("day", day)}, "date")
                 + field("할 일", "text", {}, "text", 'placeholder="수학 문제집 3단원"')
                 + '<button class="btn primary">할 일 추가</button></form>')
    todo_card = card("TODAY", "오늘 할 일 · 공부 계획", todo_list(day) + todo_form)

    totals = planner.week_study_totals(today)
    rows = []
    for subject, minutes in totals:
        rows.append((subject, planner.minutes_text(minutes), minutes * 100 / totals[0][1]))
    study_form = ('<form class="form-grid" data-action="planner/study">'
                  + field("날짜", "day", {"day": day}, "date")
                  + field("과목", "subject", form, "text", 'placeholder="수학"')
                  + field("공부한 시간(분)", "minutes", form, "number", 'min="1" max="1440" placeholder="50"')
                  + '<button class="btn primary">공부 시간 기록</button></form>')
    study_card = card("STUDY TIME", "공부 시간 · 최근 7일", bar_rows(rows) + study_form)

    year, month = today.year, today.month
    if len(query) == 7 and planner.is_day(query + "-01"):
        year, month = int(query[0:4]), int(query[5:7])
    calendar_card = card("CALENDAR", str(year) + "년 " + str(month) + "월",
                         '<p class="muted small">학교 시험(빨강)과 수행평가(파랑)가 자동으로 들어가요.</p>'
                         + calendar_table(year, month, today), month_buttons(year, month))

    perf_form = ('<form class="form-grid" data-action="planner/performance">'
                 + field("과목", "subject", form, "text", 'placeholder="국어"')
                 + field("날짜", "pday", form, "date", 'min="' + day + '"')
                 + field("내용", "content", form, "text", 'placeholder="화법 발표 평가"')
                 + '<button class="btn primary">수행평가 등록</button></form>')
    perf_card = card("PERFORMANCE", "수행평가 등록",
                     '<p class="muted small">등록하면 학교 일정·D-day·달력에 바로 나타나요.</p>' + perf_form)

    return (log_box(log) + notice + '<div class="layout two">'
            + '<div class="col">' + dday_card + todo_card + study_card + "</div>"
            + '<div class="col">' + calendar_card + perf_card + "</div></div>")


# 플래너 화면의 버튼(할 일·완료·공부 시간·달 이동·수행평가)을 처리한다.
#   입력: 기능 이름(예: "planner/todo"), 입력값 딕셔너리 / 출력: HTML
def planner_action(action, form):
    """플래너 화면의 버튼을 처리하고, 결과가 반영된 플래너 화면을 돌려준다.
    입력: 기능 이름(예: "planner/todo"), 입력값 딕셔너리 / 출력: HTML"""
    if action == "planner/month":
        return planner_screen(query=form.get("q", ""))
    if action == "planner/toggle":
        if form.get("n", "").isdigit():
            planner.toggle_todo(int(form["n"]))
        return planner_screen()
    if action == "planner/todo":
        error = planner.add_todo(form.get("day", ""), form.get("text", ""))
        return planner_screen(message=error, is_error=True, form=form)
    if action == "planner/study":
        error = planner.add_study_time(form.get("day", ""), form.get("subject", ""), form.get("minutes", ""))
        if error != "":
            return planner_screen(message=error, is_error=True, form=form)
        return planner_screen(message="공부 시간을 기록했어요.")
    # planner/performance : 수행평가 등록 (기획서 알고리즘 1의 검사·저장·반영을 그대로 쓴다)
    record, error = schedule.register_performance(form.get("pday", ""), form.get("subject", ""), form.get("content", ""))
    if error != "":
        return planner_screen(message=error, is_error=True, form=form)
    return planner_screen(message=schedule.performance_done_text(record))


# ---------------- 방문객 화면 ----------------

# 누르면 3D 캠퍼스에서 그 방으로 이동하는 방문 목적별 버튼들을 만든다.
#   입력: 없음 / 출력: HTML
def place_buttons():
    """방문 목적별 안내 버튼들. 누르면 3D 캠퍼스에서 그 방으로 이동한다. 출력: HTML"""
    buttons = ""
    for place in visitors.place_list():
        inner = ("<strong>" + html.escape(place["purpose"]) + "</strong>"
                 + '<span class="where">' + html.escape(place["text"]) + "</span>"
                 + "<small>" + html.escape(place["desc"]) + "</small>")
        if place["room"] is None:
            buttons += '<div class="place missing">' + inner + "<small>⚠ 교실 목록에 없는 방이에요</small></div>"
        else:
            room = place["room"]
            target = urlencode({"b": room["building_id"], "f": room["floor"], "r": room["name"]})
            buttons += '<button class="place" data-room="' + html.escape(target) + '">' + inner + "</button>"
    if buttons == "":
        return '<p class="muted">data/places.txt에 안내 장소가 없어요.</p>'
    return '<div class="place-grid">' + buttons + "</div>"


# 방문객 화면: 방문 목적별 안내(누르면 3D 캠퍼스에서 위치 표시)를 보여준다.
#   입력: 실행 기록, 검색어(쓰지 않음) / 출력: HTML
def guide_screen(log="", query=""):
    """방문객 화면: 방문 목적별 안내(누르면 3D 캠퍼스에서 위치 표시)를 보여준다.
    (수행평가 등록은 스터디 플래너의 「새 일정」 창으로 옮겼다)
    입력: 실행 기록, 검색어(쓰지 않음) / 출력: HTML"""
    visit_card = card("FOR VISITORS", "어디로 가야 하나요?",
                      '<p class="muted small">방문 목적을 누르면 3D 캠퍼스에서 위치를 보여드려요.</p>' + place_buttons())
    return log_box(log) + visit_card


# ---------------- AI에게 물어보기 (모든 탭 공통) ----------------

# 탭 아래에 붙는 「AI에게 물어보기」 카드를 만든다.
#   입력: 탭 이름, 질문, 답, 오류 메시지 / 출력: HTML (AI 도우미가 없는 탭이면 "")
def ai_card(tab, question="", answer="", error=""):
    """탭 아래에 붙는 「AI에게 물어보기」 카드. 탭마다 그 탭 자료를 근거로 답한다.
    입력: 탭 이름, 질문, 답, 오류 메시지 / 출력: HTML (AI 도우미가 없는 탭이면 "")"""
    if tab not in ai_helper.CATEGORY_GUIDE:
        return ""
    title = "AI에게 물어보기"
    if not ai_helper.is_enabled():
        body = ('<p class="muted small">python/config.txt에 <b>GEMINI_API_KEY</b>를 넣고 앱을 다시 켜면, '
                + "이 탭의 자료를 바탕으로 AI(Gemini)가 답해 줘요.</p>")
        return card("ASK AI", title, body)
    form = ('<form class="search" data-action="ai/ask">'
            + '<input class="input" name="q" value="' + html.escape(question) + '" placeholder="이 탭에 대해 무엇이든 물어보세요" aria-label="AI에게 질문">'
            + '<button class="btn primary" data-busy="생각 중…">물어보기</button></form>')
    chips = ""
    for preset in ai_helper.PRESET_QUESTIONS.get(tab, []):
        chips += ('<form data-action="ai/ask"><input type="hidden" name="q" value="' + html.escape(preset) + '">'
                  + '<button class="chip" data-busy="생각 중…">' + html.escape(preset) + "</button></form>")
    result = ""
    if error != "":
        result = '<p class="notice error">' + html.escape(error) + "</p>"
    elif answer != "":
        result = ('<div class="ai-answer"><p class="muted small">Q. ' + html.escape(question) + "</p>"
                  + "<div>" + html.escape(answer) + "</div></div>")
    note = '<p class="muted small">이 탭의 자료(메모장 파일)를 함께 보내 AI(Gemini)가 답해요. 답이 틀릴 수 있으니 중요한 건 학교에 확인하세요.</p>'
    return card("ASK AI", title, note + form + '<div class="chips">' + chips + "</div>" + result)


# 아직 만들지 않은 기능의 화면.
#   입력: 기능 이름 / 출력: HTML 문자열
def coming_soon_screen(title):
    """아직 만들지 않은 기능의 화면.
    입력: 기능 이름
    출력: HTML 문자열"""
    return card("COMING SOON", title, '<p class="muted">아직 만드는 중인 기능이에요.</p>')


# 플래너 버튼을 실행하면서, 그때 출력된 글자(일정 저장 기록)는 화면에 내보내지 않는다.
#   입력: 기능 이름, 입력값 / 출력: HTML
def capture_planner(action, form):
    """플래너 버튼을 실행한다. 수행평가 등록 때 print로 나오는 저장 기록은 모아 두기만 한다.
    입력: 기능 이름, 입력값 / 출력: HTML"""
    result = []
    capture_output(lambda: result.append(planner_action(action, form)))
    return result[0]


# 탭 이름 → 화면을 만드는 함수
SCREENS = {
    "planner": planner_screen,
    "schedule": schedule_screen,
    "rooms": rooms_screen,
    "notes": notes_screen,
    "meal": meal_screen,
    "guide": guide_screen,
    "exams": exams_screen,
}


# 탭 이름에 맞는 화면(AI 카드 없이)을 만든다.
#   입력: 탭 이름(예: "rooms"), 실행 기록 글자, 검색어 / 출력: HTML 문자열
def screen_only(name, log="", query=""):
    """탭 이름에 맞는 화면(AI 카드 없이)을 만든다.
    입력: 탭 이름(예: "rooms"), 실행 기록 글자, 검색어
    출력: HTML 문자열"""
    if name in SCREENS:
        return SCREENS[name](log, query)
    return coming_soon_screen(name)


# 탭 화면 아래에 「AI에게 물어보기」 카드를 붙여 만든다.
def get_screen(name, log="", query=""):
    """탭 화면 + 아래쪽 「AI에게 물어보기」 카드. 입력·출력은 screen_only와 같다."""
    return screen_only(name, log, query) + ai_card(name)


# 버튼(또는 입력 칸)으로 요청한 기능을 실행하고, 결과가 반영된 화면(AI 카드 없이)을 돌려준다.
#   입력: 기능 이름(예: "schedule/update"), 버튼이 있던 탭 이름, 입력 칸 값 딕셔너리 / 출력: HTML 문자열
def do_action(action, from_tab, form):
    """버튼(또는 입력 칸)으로 요청한 기능을 실행하고, 결과가 반영된 화면(AI 카드 없이)을 돌려준다.
    입력: 기능 이름(예: "schedule/update"), 버튼이 있던 탭 이름, 입력 칸 값 딕셔너리
    출력: HTML 문자열"""
    if action.startswith("planner/"):
        return capture_planner(action, form)
    if action == "schedule/update":
        log = capture_output(schedule.update_schedule)
        return screen_only(from_tab, log)
    if action == "rooms/build":
        log = capture_output(rooms.make_rooms)
        return screen_only(from_tab, log)
    if action == "rooms/search":
        return screen_only(from_tab, "", form.get("q", ""))
    if action == "notes/exam":
        return save_exam_action(form)
    if action == "notes/wrong":
        return save_wrong_action(form)
    if action == "notes/analyze":
        log = capture_output(wrong_notes.analyze_and_save)
        return notes_screen(log)
    if action == "meal/update":
        log = capture_output(meal.update_meals)
        return meal_screen(log)
    if action == "share/make":
        log = capture_output(share.update_share)
        return schedule_screen(log)
    if action == "share/upload":
        log = capture_output(lambda: share.update_share(True))
        return schedule_screen(log)
    if action == "exams/search":
        return exams_screen("", form.get("q", ""))
    return coming_soon_screen(action)


# 버튼·입력 칸 요청을 처리한다.
#   입력: 기능 이름, 버튼이 있던 탭 이름, 입력 칸 값 / 출력: HTML 문자열
def run_action(action, from_tab, form):
    """버튼·입력 칸 요청을 처리한다. AI 질문이면 AI 답을, 아니면 기능 결과 화면을 돌려준다.
    (어느 경우든 화면 아래에 「AI에게 물어보기」 카드를 붙인다)
    입력: 기능 이름, 버튼이 있던 탭 이름, 입력 칸 값 / 출력: HTML 문자열"""
    if action == "ai/ask":
        question = form.get("q", "")
        answer, error = ai_helper.ask_for_tab(from_tab, question)
        return screen_only(from_tab) + ai_card(from_tab, question, answer, error)
    return do_action(action, from_tab, form) + ai_card(from_tab)
