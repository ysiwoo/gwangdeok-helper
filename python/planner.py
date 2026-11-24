# planner.py : 스터디 플래너 (공부 계획·할 일, 공부 시간, D-day, 월간 달력)
# - 할 일은 data/todos.txt, 공부 시간은 data/study_time.txt(메모장)에 이어서 저장한다
# - 학교 시험과 수행평가는 schedule.txt에서 읽어 D-day와 달력에 자동으로 넣는다

import os
import calendar
from datetime import date, datetime, timedelta

import schedule
import textdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODOS_PATH = os.path.join(BASE_DIR, "data", "todos.txt")
STUDY_PATH = os.path.join(BASE_DIR, "data", "study_time.txt")
TODO_KEYS = ["날짜", "할 일", "완료"]            # 완료 칸: "O" 또는 "X"
STUDY_KEYS = ["날짜", "과목", "공부 시간(분)"]
PLANNER_CATEGORIES = ["시험", "수행평가"]         # 플래너 D-day·달력에 넣을 학교 일정


# 날짜 글자가 연도-월-일 형식인지 확인한다.
#   입력: 문자열 / 출력: True, False
def is_day(text):
    """날짜 글자가 연도-월-일 형식인지 확인한다. 입력: 문자열 / 출력: True, False"""
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# ---------------- 1. 공부 계획·할 일 ----------------

# 할 일 목록을 모두 불러온다.
#   입력: 없음 / 출력: 딕셔너리 리스트
def load_todos():
    """[파일 읽기] todos.txt에서 할 일을 모두 불러온다. (없으면 새로 만든다) 출력: 딕셔너리 리스트"""
    return textdb.read_table(TODOS_PATH, TODO_KEYS, TODO_KEYS)


# 할 일 한 건을 검사하고 파일 끝에 덧붙인다.
#   입력: 날짜 'YYYY-MM-DD', 할 일 / 출력: 오류 메시지 (문제없으면 "")
def add_todo(day, text):
    """[파일 쓰기] 할 일 한 건을 검사하고 todos.txt 끝에 덧붙인다.
    입력: 날짜 'YYYY-MM-DD', 할 일 / 출력: 오류 메시지 (문제없으면 "")"""
    day, text = day.strip(), text.strip()
    if text == "":
        return "할 일을 입력하세요."
    if not is_day(day):
        return "날짜 형식이 맞지 않습니다."
    textdb.append_row(TODOS_PATH, TODO_KEYS, TODO_KEYS, {"날짜": day, "할 일": text, "완료": "X"})
    return ""


# 할 일 하나의 완료 표시를 바꾼다.
#   입력: 줄 번호(정수) / 출력: 바꿨으면 True
def toggle_todo(number):
    """[파일 읽기][파일 쓰기] number번째(0부터) 할 일의 완료 표시를 O ↔ X로 바꿔 다시 저장한다.
    입력: 줄 번호(정수) / 출력: 바꿨으면 True"""
    todos = load_todos()
    if number < 0 or number >= len(todos):
        return False
    if todos[number]["완료"] == "O":
        todos[number]["완료"] = "X"
    else:
        todos[number]["완료"] = "O"
    textdb.write_table(TODOS_PATH, TODO_KEYS, TODO_KEYS, todos)
    return True


# 그날의 할 일을 줄 번호와 함께 고른다.
#   입력: 날짜 / 출력: [(전체 목록에서의 줄 번호, 할 일 딕셔너리), ...]
def todos_on(day):
    """그날의 할 일을 고른다. 입력: 날짜 / 출력: [(전체 목록에서의 줄 번호, 할 일 딕셔너리), ...]"""
    result = []
    number = 0
    for todo in load_todos():
        if todo["날짜"] == day:
            result.append((number, todo))
        number += 1
    return result


# ---------------- 2. 공부 시간 ----------------

# 공부 시간 기록을 모두 불러온다.
#   입력: 없음 / 출력: 딕셔너리 리스트
def load_study_times():
    """[파일 읽기] study_time.txt에서 공부 시간 기록을 모두 불러온다. 출력: 딕셔너리 리스트"""
    return textdb.read_table(STUDY_PATH, STUDY_KEYS, STUDY_KEYS)


# 공부 시간 한 건을 검사하고 파일 끝에 덧붙인다.
#   입력: 날짜, 과목, 공부한 시간(분) / 출력: 오류 메시지 (문제없으면 "")
def add_study_time(day, subject, minutes):
    """[파일 쓰기] 공부 시간 한 건을 검사하고 study_time.txt 끝에 덧붙인다.
    입력: 날짜, 과목, 공부한 시간(분) / 출력: 오류 메시지 (문제없으면 "")"""
    day, subject, minutes = day.strip(), subject.strip(), str(minutes).strip()
    if subject == "":
        return "과목을 입력하세요."
    if not is_day(day):
        return "날짜 형식이 맞지 않습니다."
    if not minutes.isdigit() or int(minutes) < 1 or int(minutes) > 1440:
        return "공부 시간은 1부터 1440 사이의 숫자(분)로 입력하세요."
    textdb.append_row(STUDY_PATH, STUDY_KEYS, STUDY_KEYS,
                      {"날짜": day, "과목": subject, "공부 시간(분)": minutes})
    return ""


# 최근 7일 동안의 과목별 공부 시간을 더한다.
#   입력: 오늘 날짜(date) / 출력: [(과목, 분), ...] 많이 공부한 순
def week_study_totals(today):
    """최근 7일(오늘 포함) 동안 과목별 공부 시간을 더한다.
    입력: 오늘 날짜(date) / 출력: [(과목, 분), ...] 많이 공부한 순"""
    first = (today - timedelta(days=6)).strftime("%Y-%m-%d")
    last = today.strftime("%Y-%m-%d")
    totals = {}
    for row in load_study_times():
        if first <= row["날짜"] <= last and row["공부 시간(분)"].isdigit():
            totals[row["과목"]] = totals.get(row["과목"], 0) + int(row["공부 시간(분)"])
    result = list(totals.items())
    result.sort(key=lambda item: item[1], reverse=True)
    return result


# 분을 "1시간 30분" 같은 글자로 바꾼다.
#   입력: 분(정수) / 출력: 문자열
def minutes_text(minutes):
    """분을 "1시간 30분" 같은 글자로 바꾼다. 입력: 분(정수) / 출력: 문자열"""
    if minutes < 60:
        return str(minutes) + "분"
    if minutes % 60 == 0:
        return str(minutes // 60) + "시간"
    return str(minutes // 60) + "시간 " + str(minutes % 60) + "분"


# ---------------- 3. D-day와 달력 (학교 시험·수행평가 자동 표시) ----------------

# 학교 일정 중 시험·수행평가만 고른다.
#   입력: 없음 / 출력: 일정 리스트
def school_events():
    """[파일 읽기] schedule.txt에서 플래너에 넣을 학교 일정(시험·수행평가)만 고른다. 출력: 일정 리스트"""
    result = []
    for item in schedule.load_schedule():
        if item["category"] in PLANNER_CATEGORIES:
            result.append(item)
    return result


# 가까운 시험·수행평가 D-day를 5개까지 고른다.
#   입력: 오늘 날짜 / 출력: "dday"가 붙은 일정 리스트
def planner_ddays(today):
    """아직 안 지난 시험·수행평가를 가까운 순서로 5개까지 고른다.
    입력: 오늘 날짜 / 출력: "dday"가 붙은 일정 리스트"""
    return schedule.upcoming_schedules(school_events(), today)[0:5]


# 한 달 달력을 주 단위(일요일 시작)로 만든다.
#   입력: 연도, 월 / 출력: [[일, 월, 화, 수, 목, 금, 토], ...] 날짜 숫자 리스트
def month_weeks(year, month):
    """한 달 달력을 주 단위로 만든다. 일요일부터 시작하고, 그 달이 아닌 칸은 0이다.
    입력: 연도, 월 / 출력: [[일, 월, 화, 수, 목, 금, 토], ...] 날짜 숫자 리스트"""
    return calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)


# 달력 한 칸(하루)에 들어갈 내용을 모은다.
#   입력: 날짜 'YYYY-MM-DD', 학교 일정 리스트, 할 일 리스트 / 출력: {"events": 그날 시험·수행평가 리스트, "todo": 할 일 수, "done": 끝낸 할 일 수}
def day_summary(day, events, todos):
    """달력 한 칸에 들어갈 내용을 모은다.
    입력: 날짜 'YYYY-MM-DD', 학교 일정 리스트, 할 일 리스트
    출력: {"events": 그날 시험·수행평가 리스트, "todo": 할 일 수, "done": 끝낸 할 일 수}"""
    summary = {"events": [], "todo": 0, "done": 0}
    for item in events:
        if item["date"] == day:
            summary["events"].append(item)
    for todo in todos:
        if todo["날짜"] == day:
            summary["todo"] += 1
            if todo["완료"] == "O":
                summary["done"] += 1
    return summary


# ---------------- 콘솔 메뉴 ----------------

# 오늘의 플래너(D-day, 할 일, 공부 시간)를 출력한다.
#   입력: 오늘 날짜 / 출력: 없음
def print_today(today):
    """[출력] 오늘의 플래너(D-day, 오늘 할 일, 최근 7일 공부 시간)를 출력한다. 입력: 오늘 날짜"""
    day = today.strftime("%Y-%m-%d")
    print("\n스터디 플래너 (" + day + ")")
    for item in planner_ddays(today):
        print("  " + schedule.dday_text(item["dday"]).rjust(6), item["date"], "[" + item["category"] + "]", item["title"])
    print("  오늘 할 일")
    todos = todos_on(day)
    if len(todos) == 0:
        print("    (없음)")
    count = 1
    for number, todo in todos:
        print("    " + str(count) + ". [" + todo["완료"] + "] " + todo["할 일"])
        count += 1
    print("  최근 7일 공부 시간")
    for subject, minutes in week_study_totals(today):
        print("    " + subject + ": " + minutes_text(minutes))


# 메뉴 13: 플래너를 보여주고 할 일·공부 시간을 입력받는다.
#   입력: 없음 / 출력: 없음
def planner_menu():
    """[입력][출력][파일 쓰기] 메뉴 13: 오늘의 플래너를 보여주고, 할 일 추가·완료 표시·공부 시간 기록을 입력받는다.
    그냥 Enter를 누르면 끝낸다."""
    today = date.today()
    day = today.strftime("%Y-%m-%d")
    while True:
        print_today(today)
        choice = input("  1 할 일 추가  2 완료 표시  3 공부 시간 기록  (그만하려면 Enter): ").strip()
        if choice == "":
            return
        if choice == "1":
            error = add_todo(day, input("  할 일: "))
        elif choice == "2":
            todos = todos_on(day)
            text = input("  완료 표시를 바꿀 번호: ").strip()
            if text.isdigit() and 1 <= int(text) <= len(todos):
                toggle_todo(todos[int(text) - 1][0])
                error = ""
            else:
                error = "목록에 있는 번호를 입력하세요."
        elif choice == "3":
            error = add_study_time(day, input("  과목: "), input("  공부한 시간(분): "))
        else:
            error = "1, 2, 3 중에서 고르세요."
        if error != "":
            print("  " + error)


# 이 파일만 따로 실행했을 때: python python/planner.py
if __name__ == "__main__":
    planner_menu()
