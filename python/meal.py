# meal.py : 이번 달 급식 (학생·교사·방문객 모두)
# - 나이스 급식식단정보 API로 이번 달 중식·석식을 받아 data/meal.txt(메모장)에 저장한다
# - 메뉴 이름 뒤의 알레르기 번호 "(5.6.13)"를 따로 떼어 알레르기 이름으로 바꿔 보여준다
# 학교 코드 찾기·API 요청은 schedule.py의 함수를 그대로 쓴다.

import os
import re
from datetime import date, datetime, timedelta

import schedule
import textdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAL_PATH = os.path.join(BASE_DIR, "data", "meal.txt")

# 메모장 파일(meal.txt)은 한 줄에 메뉴 하나: 날짜, 끼니, 칼로리, 메뉴, 알레르기 번호(예: 5.6.13)
MEAL_KEYS = ["날짜", "끼니", "칼로리", "메뉴", "알레르기"]

# 식품 알레르기 유발 물질 번호 (식품의약품안전처 표시 기준)
ALLERGIES = {1: "난류", 2: "우유", 3: "메밀", 4: "땅콩", 5: "대두", 6: "밀", 7: "고등어", 8: "게",
             9: "새우", 10: "돼지고기", 11: "복숭아", 12: "토마토", 13: "아황산류", 14: "호두",
             15: "닭고기", 16: "쇠고기", 17: "오징어", 18: "조개류", 19: "잣"}


# 메뉴 한 줄에서 이름과 알레르기 번호를 나눈다.
#   입력: 메뉴 글자 / 출력: 딕셔너리
def parse_dish(text):
    """메뉴 한 줄에서 이름과 알레르기 번호를 나눈다.
    예) "감자탕 (5.6.9.10.13)" → {"name": "감자탕", "allergies": [5, 6, 9, 10, 13]}
    입력: 메뉴 글자 / 출력: 딕셔너리"""
    text = text.strip()
    match = re.match(r"^(.*?)\s*\(([\d.]+)\)$", text)
    if match is None:
        return {"name": text, "allergies": []}
    numbers = []
    for part in match.group(2).split("."):
        if part != "":
            numbers.append(int(part))
    return {"name": match.group(1).strip(), "allergies": numbers}


# 나이스가 보내는 메뉴 글자("밥 <br/>국 (5.6)<br/>...")를 메뉴 리스트로 바꾼다.
#   입력: 메뉴 전체 글자 / 출력: [{"name", "allergies"}, ...]
def parse_dishes(ddish_text):
    """나이스가 보내는 메뉴 글자("밥 <br/>국 (5.6)<br/>...")를 메뉴 리스트로 바꾼다.
    입력: 메뉴 전체 글자 / 출력: [{"name", "allergies"}, ...]"""
    dishes = []
    for line in ddish_text.split("<br/>"):
        if line.strip() != "":
            dishes.append(parse_dish(line))
    return dishes


# 알레르기 번호 리스트를 이름으로 바꾼다.
#   입력: 번호 리스트 / 출력: 문자열
def allergy_text(numbers):
    """알레르기 번호 리스트를 이름으로 바꾼다. 예) [1, 2] → "난류, 우유"
    입력: 번호 리스트 / 출력: 문자열"""
    names = []
    for number in numbers:
        names.append(ALLERGIES.get(number, str(number)))
    return ", ".join(names)


# 이번 달의 첫날과 마지막 날을 구한다.
#   입력: 오늘 날짜(date) / 출력: (첫날, 마지막 날)
def month_range(today):
    """이번 달의 첫날과 마지막 날을 구한다.
    입력: 오늘 날짜(date) / 출력: (첫날, 마지막 날)"""
    first = today.replace(day=1)
    next_month = (first + timedelta(days=32)).replace(day=1)    # 다음 달 1일
    return first, next_month - timedelta(days=1)


# 나이스 급식 한 행을 급식 딕셔너리로 바꾼다.
#   입력: 'YYYY-MM-DD', 나이스 행 / 출력: {"date", "type", "dishes", "calorie"}
def make_meal(day_text, row):
    """나이스 급식 한 행을 급식 딕셔너리로 바꾼다.
    입력: 'YYYY-MM-DD', 나이스 행 / 출력: {"date", "type", "dishes", "calorie"}"""
    return {"date": day_text, "type": row["MMEAL_SC_NM"],
            "dishes": parse_dishes(row["DDISH_NM"]), "calorie": row["CAL_INFO"]}


# 나이스 급식 API로 이번 달(1일~말일) 급식을 받는다.
#   입력: 없음 / 출력: [{"date", "type", "dishes", "calorie"}, ...]
def fetch_meals():
    """[출력] 나이스 급식 API로 이번 달(1일~말일) 급식을 받는다.
    인증키가 있으면 한 번에 받고, 없으면 한 번에 5건만 주므로 하루씩 나눠서 요청한다.
    출력: [{"date", "type", "dishes", "calorie"}, ...]"""
    config = schedule.load_config()
    api_key = config["NEIS_API_KEY"]
    office_code, school_code = schedule.find_school_code(api_key, config["SCHOOL_NAME"], config["REGION_KEYWORD"])
    if school_code is None:
        return []
    first, last = month_range(date.today())
    print("  기간:", first.strftime("%Y-%m-%d"), "~", last.strftime("%Y-%m-%d"))
    meals = []
    if api_key != "":
        rows = schedule.neis_request("mealServiceDietInfo", api_key, {
            "ATPT_OFCDC_SC_CODE": office_code, "SD_SCHUL_CODE": school_code,
            "MLSV_FROM_YMD": first.strftime("%Y%m%d"), "MLSV_TO_YMD": last.strftime("%Y%m%d"),
        })
        for row in rows:
            ymd = row["MLSV_YMD"]
            meals.append(make_meal(ymd[0:4] + "-" + ymd[4:6] + "-" + ymd[6:8], row))
    else:
        day = first
        while day <= last:
            rows = schedule.neis_request("mealServiceDietInfo", "", {
                "ATPT_OFCDC_SC_CODE": office_code, "SD_SCHUL_CODE": school_code,
                "MLSV_YMD": day.strftime("%Y%m%d"),
            })
            for row in rows:
                meals.append(make_meal(day.strftime("%Y-%m-%d"), row))
            day = day + timedelta(days=1)
    meals.sort(key=lambda meal: meal["date"])
    print("  급식", len(meals), "끼니를 받았습니다.")
    return meals


# 급식 목록을 data/meal.txt(메모장)로 저장한다.
#   입력: 급식 리스트 / 출력: 없음
def save_meals(meals):
    """[파일 쓰기] 급식 목록을 data/meal.txt(메모장)로 저장한다. 메뉴 하나를 한 줄로 쓴다.
    입력: 급식 리스트"""
    rows = []
    for meal in meals:
        for dish in meal["dishes"]:
            numbers = []
            for number in dish["allergies"]:
                numbers.append(str(number))
            rows.append({"날짜": meal["date"], "끼니": meal["type"], "칼로리": meal["calorie"],
                         "메뉴": dish["name"], "알레르기": ".".join(numbers)})
    textdb.write_table(MEAL_PATH, MEAL_KEYS, MEAL_KEYS, rows)
    print("저장 완료:", MEAL_PATH, "(" + str(len(rows)) + "줄)")


# data/meal.txt(메모장)를 읽어, 같은 날짜·끼니의 메뉴끼리 다시 묶는다.
#   입력: 없음 / 출력: (급식 리스트, 받은 시각). 파일이 없으면 ([], "")
def load_meals():
    """[파일 읽기] data/meal.txt(메모장)를 읽어, 같은 날짜·끼니의 메뉴끼리 다시 묶는다.
    받은 시각은 파일을 마지막으로 저장한 시각으로 알 수 있다.
    출력: (급식 리스트, 받은 시각). 파일이 없으면 ([], "")"""
    if not os.path.exists(MEAL_PATH):
        return [], ""
    meals = []
    for row in textdb.read_table(MEAL_PATH, MEAL_KEYS, MEAL_KEYS):
        numbers = []
        for part in row["알레르기"].split("."):
            if part.isdigit():
                numbers.append(int(part))
        dish = {"name": row["메뉴"], "allergies": numbers}
        last = None
        if len(meals) > 0:
            last = meals[-1]
        if last is not None and last["date"] == row["날짜"] and last["type"] == row["끼니"]:
            last["dishes"].append(dish)                 # 같은 끼니면 메뉴만 추가
        else:
            meals.append({"date": row["날짜"], "type": row["끼니"], "calorie": row["칼로리"], "dishes": [dish]})
    saved_time = datetime.fromtimestamp(os.path.getmtime(MEAL_PATH)).strftime("%Y-%m-%d %H:%M")
    return meals, saved_time


# 급식을 날짜별로 묶는다.
#   입력: 급식 리스트 / 출력: [(날짜, [그날 급식들]), ...] 날짜순
def meals_by_day(meals):
    """급식을 날짜별로 묶는다. 이번 달 급식만 남긴다.
    입력: 급식 리스트 / 출력: [(날짜, [그날 급식들]), ...] 날짜순"""
    this_month = date.today().strftime("%Y-%m")
    groups = {}
    for meal in meals:
        if meal["date"][0:7] == this_month:
            if meal["date"] not in groups:
                groups[meal["date"]] = []
            groups[meal["date"]].append(meal)
    result = []
    for day in sorted(groups):
        result.append((day, groups[day]))
    return result


# 한 끼니의 메뉴와 알레르기를 출력한다.
#   입력: 급식 딕셔너리 / 출력: 없음
def print_meal(meal):
    """[출력] 한 끼니의 메뉴와 알레르기를 출력한다. 입력: 급식 딕셔너리"""
    print("  [" + meal["type"] + "] " + meal["calorie"])
    for dish in meal["dishes"]:
        line = "    - " + dish["name"]
        if len(dish["allergies"]) > 0:
            line += "  (알레르기: " + allergy_text(dish["allergies"]) + ")"
        print(line)


# 메뉴 10(앞부분): 급식을 새로 받아 저장한다.
#   입력: 없음 / 출력: 없음
def update_meals():
    """[출력][파일 쓰기] 메뉴 10(앞부분): 급식을 새로 받아 저장한다."""
    print("나이스 급식 받는 중…")
    try:
        meals = fetch_meals()
    except Exception as error:
        print("  나이스 API 접속 실패:", error)
        return
    if len(meals) == 0:
        # 받은 급식이 없으면(접속 문제·방학) 저장해 둔 급식을 지우지 않는다
        print("  받은 급식이 없어 예전에 저장한 급식을 그대로 둡니다.")
        return
    save_meals(meals)


# 메뉴 10: 이번 달 급식을 새로 받아 저장한 뒤, 날짜별로 출력한다.
#   입력: 없음 / 출력: 없음
def show_meals():
    """[출력] 메뉴 10: 이번 달 급식을 새로 받아 저장한 뒤, 날짜별로 출력한다."""
    update_meals()
    days = meals_by_day(load_meals()[0])
    if len(days) == 0:
        print("이번 달에 등록된 급식이 없어요. (방학일 수 있어요)")
        return
    for day, meals in days:
        title = day
        if day == date.today().strftime("%Y-%m-%d"):
            title += " (오늘)"
        print("\n" + title)
        for meal in meals:
            print_meal(meal)


# 이 파일만 따로 실행했을 때: python python/meal.py
if __name__ == "__main__":
    show_meals()
