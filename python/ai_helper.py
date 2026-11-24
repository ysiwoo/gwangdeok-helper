# ai_helper.py : 무료 AI(Google Gemini API)로 학교생활 도우미 기능 쓰기
# - 설정 파일 python/config.txt의 GEMINI_API_KEY로 Gemini에 질문한다 (키가 없으면 기능이 꺼진다)
# - 탭(카테고리)마다 그 탭의 자료(메모장 파일에서 읽은 일정·급식·교실·시험·오답·방문 안내)를 함께 보내
#   우리 학교 자료를 근거로 답하게 한다
#
# 사용한 라이브러리: 표준 라이브러리(urllib, json)만 사용 (따로 설치할 것 없음)
# Gemini API 키 발급: https://aistudio.google.com (무료 등급은 하루·분당 사용량 제한이 있음)

import json
import urllib.request
import urllib.error
from datetime import date

import schedule
import rooms
import wrong_notes
import visitors
import meal
import exam_finder
import planner

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/"
# 차례대로 시도할 모델: 앞의 모델이 바쁘거나(503) 답이 늦으면 다음 모델로 다시 물어본다
# (빠르고 덜 붐비는 Flash-Lite를 먼저 쓴다. "-latest"는 구글이 최신 모델로 알아서 연결해 주는 이름)
MODELS = ["gemini-flash-lite-latest", "gemini-flash-latest"]


# config.txt에서 Gemini API 키를 읽는다.
#   입력: 없음 / 출력: 키 문자열 (없으면 "")
def get_api_key():
    """[파일 읽기] config.txt에서 Gemini API 키를 읽는다. 출력: 키 문자열 (없으면 "")"""
    return schedule.load_config(quiet=True).get("GEMINI_API_KEY", "").strip()


# AI 기능을 쓸 수 있는지(키가 있는지) 확인한다.
#   입력: 없음 / 출력: True / False
def is_enabled():
    """AI 기능을 쓸 수 있는지(키가 있는지) 확인한다. 출력: True / False"""
    return get_api_key() != ""


# 대화 리스트를 Gemini 형식으로 바꾼다.
#   입력: [{"role": "user"/"assistant", "content": 글자}, ...] / 출력: Gemini contents 리스트
def to_gemini_contents(messages):
    """대화 리스트를 Gemini 형식으로 바꾼다. (Gemini는 AI 쪽 역할 이름이 "model")
    입력: [{"role": "user"/"assistant", "content": 글자}, ...] / 출력: Gemini contents 리스트"""
    contents = []
    for message in messages:
        role = "user"
        if message["role"] == "assistant":
            role = "model"
        contents.append({"role": role, "parts": [{"text": str(message["content"])}]})
    return contents


# Gemini 모델 하나에 요청을 보내고 받은 JSON을 돌려준다.
#   입력: 모델 이름, 보낼 내용(딕셔너리) / 출력: 응답 딕셔너리
def call_gemini(model, body):
    """Gemini 모델 하나에 요청을 보내고 받은 JSON을 돌려준다. 실패하면 오류가 난다.
    입력: 모델 이름, 보낼 내용(딕셔너리) / 출력: 응답 딕셔너리"""
    request = urllib.request.Request(API_URL + model + ":generateContent",
                                     data=json.dumps(body).encode("utf-8"),
                                     headers={"x-goog-api-key": get_api_key(),
                                              "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


# Gemini 응답에서 답 글자를 꺼낸다.
#   입력: 응답 딕셔너리 / 출력: (답 글자, 오류 메시지)
def answer_text(data):
    """Gemini 응답에서 답 글자를 꺼낸다.
    입력: 응답 딕셔너리 / 출력: (답 글자, 오류 메시지)"""
    candidates = data.get("candidates", [])
    if len(candidates) == 0:                       # 질문 자체가 안전 기준에 막힌 경우
        return "", "이 질문에는 답할 수 없어요."
    candidate = candidates[0]
    text = ""
    for part in candidate.get("content", {}).get("parts", []):
        if "text" in part and not part.get("thought", False):
            text += part["text"]
    reason = candidate.get("finishReason", "")
    if text.strip() == "" and reason not in ["STOP", "MAX_TOKENS"]:
        return "", "이 질문에는 답할 수 없어요."
    if reason == "MAX_TOKENS":
        text += "\n(답이 길어서 중간에 끊겼어요)"
    return text.strip(), ""


# AI(Gemini)에게 대화를 보내고 답 글자를 받는다.
#   입력: 역할 설명(system), 대화 리스트, JSON으로 받을지 / 출력: (답 글자, 오류 메시지). 성공하면 오류 메시지는 ""
def ask_ai(system, messages, want_json=False):
    """AI(Gemini)에게 대화를 보내고 답 글자를 받는다. 모델이 바쁘면 다음 모델로 다시 시도한다.
    입력: 역할 설명(system), 대화 리스트, JSON으로 받을지
    출력: (답 글자, 오류 메시지). 성공하면 오류 메시지는 "" """
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": to_gemini_contents(messages)}
    if want_json:
        body["generationConfig"] = {"responseMimeType": "application/json"}
    error_message = ""
    for model in MODELS:
        try:
            return answer_text(call_gemini(model, body))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            if error.code in [401, 403] or "API key" in detail or "API_KEY" in detail:
                return "", "Gemini API 키가 올바르지 않아요. config.txt의 GEMINI_API_KEY를 확인하세요."
            if error.code == 400:
                return "", "AI가 이 요청을 처리하지 못했어요. 질문을 바꿔 보세요."
            if error.code == 429:
                return "", "무료 사용량을 다 썼어요. 잠시(또는 내일) 뒤에 다시 물어보세요."
            error_message = "AI 서버가 바빠요 (" + str(error.code) + "). 잠시 뒤 다시 시도하세요."
        except TimeoutError:
            error_message = "AI 답이 너무 늦어요. 잠시 뒤 다시 물어보세요."      # 다음 모델로 한 번 더
        except urllib.error.URLError as error:
            if "timed out" in str(error):
                error_message = "AI 답이 너무 늦어요. 잠시 뒤 다시 물어보세요."
            else:
                return "", "인터넷 연결을 확인하세요."
    return "", error_message


# ---------------- 탭(카테고리)별 도우미 ----------------

ROLE = ("너는 광덕고등학교 학교생활 도우미야. 학생·교사·방문객에게 한국어로 짧고 친절하게 답해. "
        "아래 [자료]에 있는 내용을 근거로 답하고, 자료에 없는 학교 정보는 지어내지 말고 모른다고 말해. "
        "마크다운 기호(**, # 등) 없이 보통 글로 답해. 오늘 날짜는 {today}야.")

# 탭마다 AI가 맡을 일
CATEGORY_GUIDE = {
    "planner": "공부 계획 도우미: 할 일, 공부 시간, 다가오는 시험·수행평가 D-day를 보고 오늘 무엇을 공부하면 좋을지 알려줘.",
    "schedule": "학교 일정 도우미: 시험·수행평가 D-day를 보고 언제 무엇을 준비하면 좋을지 알려줘.",
    "meal": "급식 도우미: 메뉴, 알레르기, 칼로리 질문에 답해. 알레르기는 [자료]의 메뉴 옆 괄호를 따라.",
    "rooms": "길 안내 도우미: 교실 위치를 '건물 이름 몇 층 방 이름' 형식으로 알려줘.",
    "exams": "시험 자료 도우미: 시험 일정과 기출을 어디서 받는지 알려주고 시험 준비 방법을 조언해.",
    "notes": "공부 코치: 오답 분석 결과(과목별 오답률, 단원, 틀린 이유, 우선순위, 남은 일수)를 보고 구체적인 공부 계획과 조언을 해 줘.",
    "guide": "방문 안내 도우미: 학교를 찾은 방문객(학부모·전학생 등)에게 목적에 맞는 장소와 위치를 알려줘.",
}

# 탭마다 눌러서 바로 물어볼 수 있는 예시 질문
PRESET_QUESTIONS = {
    "planner": ["오늘 공부 계획 세워 줘", "이번 주 공부 시간 어땠어?"],
    "schedule": ["다가오는 시험 준비 계획 세워 줘", "이번 달 일정 요약해 줘"],
    "meal": ["오늘 급식에 우유 들어간 메뉴 있어?", "이번 주 가장 맛있어 보이는 날은?"],
    "rooms": ["2학년 교실은 어디 있어?", "과학실 가는 길 알려 줘"],
    "exams": ["고2 9월 학평 기출은 어디서 받아?", "수능까지 남은 기간 공부법 알려 줘"],
    "notes": ["내 오답으로 공부 계획 세워 줘", "가장 먼저 복습할 단원은?"],
    "guide": ["전학 서류는 어디서 떼?", "학부모 상담은 어디로 가면 돼?"],
}


# 딕셔너리 리스트를 한 줄에 한 건씩 "값 | 값 | 값" 글자로 바꾼다.
#   입력: 리스트, 넣을 이름들 / 출력: 문자열
def lines_of(rows, keys):
    """딕셔너리 리스트를 한 줄에 한 건씩 "값 | 값 | 값" 글자로 바꾼다. (AI에게 보낼 자료 만들기)
    입력: 리스트, 넣을 이름들 / 출력: 문자열"""
    lines = []
    for row in rows:
        values = []
        for key in keys:
            values.append(str(row.get(key, "")))
        lines.append(" | ".join(values))
    return "\n".join(lines)


# 탭에 맞는 자료를 메모장 파일들에서 읽어 글자로 만든다.
#   입력: 탭 이름 / 출력: 자료 글자
def category_data(tab):
    """[파일 읽기] 탭에 맞는 자료를 메모장 파일들에서 읽어 글자로 만든다.
    입력: 탭 이름 / 출력: 자료 글자"""
    today = date.today()
    if tab == "planner":
        day = today.strftime("%Y-%m-%d")
        todos = []
        for number, todo in planner.todos_on(day):
            todos.append(todo)
        return ("[다가오는 시험·수행평가]\n" + lines_of(planner.planner_ddays(today), ["date", "category", "title", "dday"])
                + "\n\n[오늘 할 일] 할 일 | 완료(O/X)\n" + lines_of(todos, ["할 일", "완료"])
                + "\n\n[최근 7일 공부 시간(분)] " + str(planner.week_study_totals(today)))
    if tab == "schedule":
        items = schedule.upcoming_schedules(schedule.load_schedule(), today)
        return "날짜 | 분류 | 제목 | D-day\n" + lines_of(items, ["date", "category", "title", "dday"])
    if tab == "meal":
        text = ""
        for day, meals in meal.meals_by_day(meal.load_meals()[0]):
            for item in meals:
                dishes = []
                for dish in item["dishes"]:
                    dishes.append(dish["name"] + "(" + meal.allergy_text(dish["allergies"]) + ")")
                text += day + " " + item["type"] + " " + item["calorie"] + ": " + ", ".join(dishes) + "\n"
        return text
    if tab == "rooms":
        return "건물 | 층 | 방 이름\n" + lines_of(rooms.load_rooms(), ["building", "floor_name", "name"])
    if tab == "exams":
        return ("날짜 | 학년 | 종류 | 시험명 | 주관 | 링크\n"
                + lines_of(exam_finder.load_exam_list(), ["날짜", "학년", "종류", "시험명", "주관", "링크"]))
    if tab == "notes":
        return wrong_notes.make_report_text(wrong_notes.analyze())
    if tab == "guide":
        return "목적 | 건물 | 층 | 방 이름 | 설명\n" + lines_of(visitors.load_places(), ["목적", "건물", "층", "방 이름", "설명"])
    return ""


# 탭(카테고리)에 맞게 AI에게 물어본다.
#   입력: 탭 이름, 질문 / 출력: (답 글자, 오류 메시지)
def ask_for_tab(tab, question):
    """탭(카테고리)에 맞게 AI에게 물어본다.
    입력: 탭 이름, 질문 / 출력: (답 글자, 오류 메시지)"""
    if not is_enabled():
        return "", "AI 기능이 꺼져 있어요. config.txt에 GEMINI_API_KEY를 넣고 앱을 다시 켜 주세요."
    if question.strip() == "":
        return "", "질문을 입력하세요."
    system = (ROLE.replace("{today}", date.today().strftime("%Y-%m-%d")) + "\n"
              + CATEGORY_GUIDE.get(tab, "") + "\n\n[자료]\n" + category_data(tab))
    return ask_ai(system, [{"role": "user", "content": question.strip()}])
