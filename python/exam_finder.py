# exam_finder.py : 시험 자료 찾기
# - data/exam_list.txt(날짜, 학년, 종류, 시험명, 주관, 링크, 안내)를 읽어 검색한다
# - 시험 이름·연도·월로 검색하면, 그 시험을 내려받을 수 있는 공식 사이트(평가원·EBSi)로 연결한다

import os
from datetime import date

import schedule
import textdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAM_LIST_PATH = os.path.join(BASE_DIR, "data", "exam_list.txt")
EXAM_KEYS = ["날짜", "학년", "종류", "시험명", "주관", "링크", "안내"]

# 종류 약자 → 풀어 쓴 이름 (검색할 때 둘 다 찾을 수 있게)
KIND_NAMES = {"수능": "대학수학능력시험", "모평": "모의평가 평가원", "학평": "학력평가 교육청"}


# data/exam_list.txt를 읽는다.
#   입력: 없음 / 출력: 시험 딕셔너리 리스트 (파일이 없으면 빈 리스트)
def load_exam_list():
    """[파일 읽기] data/exam_list.txt를 읽는다.
    출력: 시험 딕셔너리 리스트 (파일이 없으면 빈 리스트)"""
    if not os.path.exists(EXAM_LIST_PATH):
        return []
    return textdb.read_table(EXAM_LIST_PATH, EXAM_KEYS, EXAM_KEYS)


# 검색할 때 쓰는 글자를 만든다.
#   입력: 시험 딕셔너리 / 출력: 문자열
def exam_search_text(exam):
    """검색할 때 쓰는 글자를 만든다. 날짜는 "2026년 9월"처럼도 찾을 수 있게 붙인다.
    입력: 시험 딕셔너리 / 출력: 문자열"""
    text = exam["학년"] + " " + exam["종류"] + " " + exam["시험명"] + " " + exam["주관"]
    text += " " + KIND_NAMES.get(exam["종류"], "")
    if exam["날짜"] != "":
        year, month, day = exam["날짜"].split("-")
        text += " " + exam["날짜"] + " " + year + " " + year + "년 " + str(int(month)) + "월"
    return text.lower()


# 검색어의 낱말이 모두 들어간 시험을 찾는다.
#   입력: 시험 리스트, 검색어 / 출력: 찾은 시험 리스트
def search_exams(exams, query):
    """검색어의 낱말이 모두 들어간 시험을 찾는다. 검색어가 비어 있으면 전부 돌려준다.
    예) "2026 고2 9월" → 2026년 9월 고2 학력평가
    입력: 시험 리스트, 검색어 / 출력: 찾은 시험 리스트"""
    words = query.lower().split()
    found = []
    for exam in exams:
        text = exam_search_text(exam)
        matched = True
        for word in words:
            if word not in text:
                matched = False
        if matched:
            found.append(exam)
    return found


# 시험 날짜를 오늘과 비교한 상태 글자를 만든다.
#   입력: 시험 딕셔너리, 오늘 날짜 / 출력: "D-10", "시행 완료", 날짜가 없으면 ""
def exam_status(exam, today):
    """시험 날짜를 오늘과 비교한 상태 글자를 만든다.
    입력: 시험 딕셔너리, 오늘 날짜 / 출력: "D-10", "시행 완료", 날짜가 없으면 "" """
    if exam["날짜"] == "":
        return ""
    dday = schedule.calc_dday(exam["날짜"], today)
    if dday < 0:
        return "시행 완료"
    return schedule.dday_text(dday)


# 시험 링크에 붙일 이름을 정한다.
#   입력: 시험 딕셔너리, 오늘 날짜 / 출력: 문자열
def link_label(exam, today):
    """시험 링크에 붙일 이름을 정한다.
    아직 시행 전인 시험 → "공식 안내", 나머지 → "기출 받으러 가기"
    입력: 시험 딕셔너리, 오늘 날짜 / 출력: 문자열"""
    if exam["날짜"] != "" and schedule.calc_dday(exam["날짜"], today) >= 0:
        return "공식 안내"
    return "기출 받으러 가기"


# 시험 한 건을 한 줄 글자로 만든다.
#   입력: 시험 딕셔너리, 오늘 날짜 / 출력: 문자열
def exam_line(exam, today):
    """[출력용] 시험 한 건을 한 줄 글자로 만든다.
    입력: 시험 딕셔너리, 오늘 날짜 / 출력: 문자열"""
    line = "[" + exam["종류"] + "] " + exam["시험명"] + " · " + exam["학년"] + " · " + exam["주관"]
    if exam["날짜"] != "":
        line += " · " + exam["날짜"] + " (" + exam_status(exam, today) + ")"
    return line


# 메뉴 11: 검색어를 입력받아 시험을 찾고, 받을 수 있는 곳을 출력한다.
#   입력: 없음 / 출력: 없음
def search_exams_menu():
    """[입력][출력] 메뉴 11: 검색어를 입력받아 시험을 찾고, 받을 수 있는 곳을 출력한다. Enter면 끝."""
    exams = load_exam_list()
    if len(exams) == 0:
        print("data/exam_list.txt에 시험 목록이 없습니다.")
        return
    today = date.today()
    print("\n시험 자료 찾기 (시험 이름·연도·월로 검색 → 기출문제 받는 곳)")
    while True:
        query = input("검색어 (예: 2026 9월 모평, 수능, 고2 학평 / 그만하려면 Enter): ").strip()
        if query == "":
            return
        found = search_exams(exams, query)
        if len(found) == 0:
            print("  '" + query + "'에 맞는 시험을 찾지 못했어요.")
        for exam in found:
            print("  " + exam_line(exam, today))
            print("     " + link_label(exam, today) + ": " + exam["링크"])
            print("     " + exam["안내"])


# 이 파일만 따로 실행했을 때: python python/exam_finder.py
if __name__ == "__main__":
    search_exams_menu()
