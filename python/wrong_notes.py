# wrong_notes.py : 오답 분석기
# - 시험 기록(data/exams.txt)과 오답 기록(data/wrong_answers.txt)을 입력받아 메모장 파일에 저장한다
#   (프로그램을 다시 켜도 저장된 파일을 불러와 이어서 기록한다. 파일이 없으면 새로 만든다)
# - 과목별 오답률, 단원별 오답 수, 틀린 이유별 개수·비율을 계산한다
# - 공부 우선순위(단원별 점수)를 계산해 상위 5개를 고른다
# - 분석 보고서(txt), 과목별 오답률 그래프(png), 복습 일정(txt)을 data/reports/ 에 저장한다

import os
from datetime import date, datetime, timedelta

import schedule
import textdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXAMS_PATH = os.path.join(DATA_DIR, "exams.txt")
WRONG_PATH = os.path.join(DATA_DIR, "wrong_answers.txt")
REPORT_DIR = os.path.join(DATA_DIR, "reports")

EXAM_FIELDS = ["시험명", "날짜", "과목", "전체 문항 수", "맞은 수"]
WRONG_FIELDS = ["기록일", "시험명", "과목", "단원", "문제 번호", "틀린 이유"]
REASONS = {1: "개념 부족", 2: "계산 실수", 3: "문제 오독", 4: "시간 부족"}

DEFAULT_DAYS = 30        # 다가오는 시험 일정이 없을 때 쓰는 "시험까지 남은 일수"
REVIEW_DAYS = [1, 3, 7]  # 복습 날짜: 기록일로부터 며칠 뒤


# ---------------- 1. 메모장 파일 읽기·쓰기 (textdb.py 사용) ----------------

# exams.txt에서 시험 기록을 모두 불러온다.
#   입력: 없음 / 출력: 딕셔너리 리스트
def load_exams():
    """[파일 읽기] exams.txt에서 시험 기록을 모두 불러온다. (없으면 새로 만든다) 출력: 딕셔너리 리스트"""
    return textdb.read_table(EXAMS_PATH, EXAM_FIELDS, EXAM_FIELDS)


# wrong_answers.txt에서 오답 기록을 모두 불러온다.
#   입력: 없음 / 출력: 딕셔너리 리스트
def load_wrongs():
    """[파일 읽기] wrong_answers.txt에서 오답 기록을 모두 불러온다. (없으면 새로 만든다) 출력: 딕셔너리 리스트"""
    return textdb.read_table(WRONG_PATH, WRONG_FIELDS, WRONG_FIELDS)


# 시험 기록 한 건을 exams.txt 끝에 덧붙인다.
#   입력: 기록 딕셔너리 / 출력: 없음
def add_exam(record):
    """[파일 쓰기] 시험 기록 한 건을 exams.txt 끝에 덧붙인다. (기존 기록은 그대로) 입력: 기록 딕셔너리"""
    textdb.append_row(EXAMS_PATH, EXAM_FIELDS, EXAM_FIELDS, record)


# 오답 기록 한 건을 wrong_answers.txt 끝에 덧붙인다.
#   입력: 기록 딕셔너리 / 출력: 없음
def add_wrong(record):
    """[파일 쓰기] 오답 기록 한 건을 wrong_answers.txt 끝에 덧붙인다. (기존 기록은 그대로) 입력: 기록 딕셔너리"""
    textdb.append_row(WRONG_PATH, WRONG_FIELDS, WRONG_FIELDS, record)


# ---------------- 2. 입력값 검사 (콘솔·앱이 함께 쓴다) ----------------

# 글자를 정수로 바꾼다.
#   입력: 문자열 / 출력: 정수 또는 None
def to_int(text):
    """글자를 정수로 바꾼다. 숫자가 아니면 None을 돌려준다.
    입력: 문자열 / 출력: 정수 또는 None"""
    text = str(text).strip()
    if text.isdigit():
        return int(text)
    return None


# 시험 기록 한 줄을 검사하고 만든다.
#   입력: 시험명, 날짜, 과목, 전체 문항 수, 맞은 수 (모두 문자열이어도 됨) / 출력: (기록 딕셔너리, 오류 메시지). 문제가 없으면 오류 메시지는 ""
def make_exam_record(name, day, subject, total, correct):
    """시험 기록 한 줄을 검사하고 만든다.
    입력: 시험명, 날짜, 과목, 전체 문항 수, 맞은 수 (모두 문자열이어도 됨)
    출력: (기록 딕셔너리, 오류 메시지). 문제가 없으면 오류 메시지는 "" """
    name, subject, day = name.strip(), subject.strip(), day.strip()
    total_num, correct_num = to_int(total), to_int(correct)
    if name == "" or subject == "":
        return None, "시험명과 과목을 입력하세요."
    if total_num is None or total_num < 1:
        return None, "전체 문항 수는 1 이상의 숫자로 입력하세요."
    if correct_num is None:
        return None, "맞은 수는 숫자로 입력하세요."
    if correct_num > total_num:
        return None, "맞은 수가 전체 문항 수보다 클 수 없어요."
    record = {"시험명": name, "날짜": day, "과목": subject, "전체 문항 수": total_num, "맞은 수": correct_num}
    return record, ""


# 오답 기록 한 줄을 검사하고 만든다.
#   입력: 시험명, 과목, 단원, 문제 번호, 틀린 이유 번호(1~4) / 출력: (기록 딕셔너리, 오류 메시지)
def make_wrong_record(exam, subject, unit, number, reason):
    """오답 기록 한 줄을 검사하고 만든다. 기록일은 오늘 날짜로 자동으로 넣는다.
    입력: 시험명, 과목, 단원, 문제 번호, 틀린 이유 번호(1~4)
    출력: (기록 딕셔너리, 오류 메시지)"""
    exam, subject, unit = exam.strip(), subject.strip(), unit.strip()
    number_num, reason_num = to_int(number), to_int(reason)
    if exam == "" or subject == "" or unit == "":
        return None, "시험명, 과목, 단원을 입력하세요."
    if number_num is None or number_num < 1:
        return None, "문제 번호는 1 이상의 숫자로 입력하세요."
    if reason_num not in REASONS:
        return None, "틀린 이유는 1~4 중에서 고르세요."
    record = {"기록일": date.today().strftime("%Y-%m-%d"), "시험명": exam, "과목": subject,
              "단원": unit, "문제 번호": number_num, "틀린 이유": REASONS[reason_num]}
    return record, ""


# ---------------- 3. 콘솔 입력 ----------------

# 빈 칸이 아닐 때까지 글자를 입력받는다.
#   출력: 입력한 글자
def input_text(prompt):
    """[입력] 빈 칸이 아닐 때까지 글자를 입력받는다. 출력: 입력한 글자"""
    while True:
        text = input(prompt).strip()
        if text != "":
            return text
        print("  빈 칸은 안 돼요. 다시 입력하세요.")


# low 이상 high 이하의 정수를 입력받는다.
#   입력: 안내 문구, 최솟값, 최댓값 / 출력: 정수
def input_number(prompt, low, high):
    """[입력] low 이상 high 이하의 정수를 입력받는다. 숫자가 아니거나 범위를 벗어나면 다시 입력받는다.
    입력: 안내 문구, 최솟값, 최댓값 / 출력: 정수"""
    while True:
        number = to_int(input(prompt))
        if number is None:
            print("  숫자로 입력하세요.")
        elif number < low or number > high:
            print("  " + str(low) + "부터 " + str(high) + " 사이로 입력하세요.")
        else:
            return number


# 날짜를 입력받는다.
#   출력: 날짜 문자열
def input_date(prompt):
    """[입력] 날짜를 입력받는다. 그냥 Enter를 누르면 오늘 날짜.
    출력: 날짜 문자열"""
    text = input(prompt).strip()
    if text == "":
        return date.today().strftime("%Y-%m-%d")
    return text


# 메뉴 5: 시험 기록을 입력받아 exams.txt에 추가한다.
#   입력: 없음 / 출력: 없음
def input_exam():
    """[입력][출력][파일 쓰기] 메뉴 5: 시험 기록을 입력받아 exams.txt에 추가한다."""
    print("\n시험 기록 입력 (지금까지 " + str(len(load_exams())) + "건)")
    name = input_text("  시험명 (예: 2학기 중간고사): ")
    day = input_date("  날짜 (예: 2026-10-15, Enter = 오늘): ")
    subject = input_text("  과목: ")
    total = input_number("  전체 문항 수: ", 1, 1000)
    correct = input_number("  맞은 수: ", 0, total)     # 전체 문항 수보다 크면 다시 입력
    record, error = make_exam_record(name, day, subject, str(total), str(correct))
    add_exam(record)
    print("  저장했어요:", name, subject, str(correct) + "/" + str(total))


# 메뉴 6: 오답 기록을 입력받아 wrong_answers.txt에 추가한다.
#   입력: 없음 / 출력: 없음
def input_wrong():
    """[입력][출력][파일 쓰기] 메뉴 6: 오답 기록을 입력받아 wrong_answers.txt에 추가한다."""
    print("\n오답 기록 입력 (지금까지 " + str(len(load_wrongs())) + "건)")
    exam = input_text("  시험명: ")
    subject = input_text("  과목: ")
    unit = input_text("  단원: ")
    number = input_number("  문제 번호: ", 1, 1000)
    for key in REASONS:
        print("    " + str(key) + " " + REASONS[key])
    reason = input_number("  틀린 이유 번호: ", 1, 4)
    record, error = make_wrong_record(exam, subject, unit, str(number), str(reason))
    add_wrong(record)
    print("  저장했어요:", subject, unit, str(number) + "번", "(" + REASONS[reason] + ")")


# ---------------- 4. 분석 ----------------

# 과목별 오답률을 계산한다.
#   입력: 시험 기록 리스트 / 출력: [(과목, 전체 문항 수 합, 틀린 수 합, 오답률), ...] 오답률 높은 순
def subject_wrong_rates(exams):
    """과목별 오답률을 계산한다. 같은 과목의 시험은 문항 수를 모두 합쳐서 계산한다.
    오답률 = (전체 문항 수 - 맞은 수) ÷ 전체 문항 수 × 100
    입력: 시험 기록 리스트
    출력: [(과목, 전체 문항 수 합, 틀린 수 합, 오답률), ...] 오답률 높은 순"""
    totals = {}
    wrongs = {}
    for exam in exams:
        subject = exam["과목"]
        total = int(exam["전체 문항 수"])
        wrong = total - int(exam["맞은 수"])
        totals[subject] = totals.get(subject, 0) + total
        wrongs[subject] = wrongs.get(subject, 0) + wrong
    result = []
    for subject in totals:
        rate = wrongs[subject] / totals[subject] * 100
        result.append((subject, totals[subject], wrongs[subject], rate))
    result.sort(key=lambda item: item[3], reverse=True)
    return result


# 단원별 오답 수를 센다.
#   입력: 오답 기록 리스트 / 출력: [(과목, 단원, 오답 수), ...] 많은 순
def unit_wrong_counts(wrong_list):
    """단원별 오답 수를 센다. (과목이 다르면 단원 이름이 같아도 다른 단원으로 본다)
    입력: 오답 기록 리스트
    출력: [(과목, 단원, 오답 수), ...] 많은 순"""
    counts = {}
    for item in wrong_list:
        key = (item["과목"], item["단원"])
        counts[key] = counts.get(key, 0) + 1
    result = []
    for key in counts:
        result.append((key[0], key[1], counts[key]))
    result.sort(key=lambda item: item[2], reverse=True)
    return result


# 틀린 이유별 개수와 비율을 계산한다.
#   입력: 오답 기록 리스트 / 출력: [(이유, 개수, 비율%), ...] 1~4번 순서
def reason_counts(wrong_list):
    """틀린 이유별 개수와 비율을 계산한다.
    입력: 오답 기록 리스트
    출력: [(이유, 개수, 비율%), ...] 1~4번 순서"""
    total = len(wrong_list)
    result = []
    for key in REASONS:
        reason = REASONS[key]
        count = 0
        for item in wrong_list:
            if item["틀린 이유"] == reason:
                count += 1
        percent = 0
        if total > 0:
            percent = count / total * 100
        result.append((reason, count, percent))
    return result


# schedule.txt의 "시험" 일정 중 오늘 이후 가장 가까운 것을 찾는다.
#   입력: 오늘 날짜 / 출력: (시험 제목, 남은 일수). 없으면 (None, 30)
def next_exam(today):
    """schedule.txt의 "시험" 일정 중 오늘 이후 가장 가까운 것을 찾는다.
    입력: 오늘 날짜
    출력: (시험 제목, 남은 일수). 없으면 (None, 30)"""
    upcoming = schedule.upcoming_schedules(schedule.load_schedule(), today)
    for item in upcoming:                       # 가까운 순으로 정렬되어 있다
        if item["category"] == "시험":
            return item["title"], item["dday"]
    return None, DEFAULT_DAYS


# 공부 우선순위 점수 공식. (공식을 바꾸고 싶으면 이 함수만 고치면 된다)
#   입력: 단원의 오답 수, 시험까지 남은 일수 / 출력: 점수(실수)
def priority_score(wrong_count, days_left):
    """공부 우선순위 점수 공식. (공식을 바꾸고 싶으면 이 함수만 고치면 된다)
    점수 = 오답 수 × 10 ÷ (시험까지 남은 일수 + 1)
    입력: 단원의 오답 수, 시험까지 남은 일수
    출력: 점수(실수)"""
    return wrong_count * 10 / (days_left + 1)


# 단원마다 점수를 계산해 높은 순으로 상위 5개를 고른다.
#   입력: 오답 기록 리스트, 시험까지 남은 일수 / 출력: [(과목, 단원, 오답 수, 점수), ...] 최대 5개
def study_priorities(wrong_list, days_left):
    """단원마다 점수를 계산해 높은 순으로 상위 5개를 고른다.
    입력: 오답 기록 리스트, 시험까지 남은 일수
    출력: [(과목, 단원, 오답 수, 점수), ...] 최대 5개"""
    result = []
    for subject, unit, count in unit_wrong_counts(wrong_list):
        result.append((subject, unit, count, priority_score(count, days_left)))
    result.sort(key=lambda item: item[3], reverse=True)
    return result[0:5]


# 복습 날짜(기록일로부터 1일·3일·7일 뒤)를 계산한다.
#   입력: 기록일 'YYYY-MM-DD' / 출력: 날짜 문자열 리스트
def review_dates(record_day):
    """복습 날짜(기록일로부터 1일·3일·7일 뒤)를 계산한다.
    입력: 기록일 'YYYY-MM-DD'
    출력: 날짜 문자열 리스트"""
    start = datetime.strptime(record_day, "%Y-%m-%d").date()
    result = []
    for days in REVIEW_DAYS:
        result.append((start + timedelta(days=days)).strftime("%Y-%m-%d"))
    return result


# 오답마다 복습 날짜(1·3·7일 뒤) 중 아직 안 지난 날짜를 모은다.
#   입력: 오답 기록 리스트, 오늘 날짜 / 출력: [(복습 날짜, 과목, 단원, 문제 번호), ...] 날짜순
def upcoming_reviews(wrong_list, today):
    """오답마다 복습 날짜(1·3·7일 뒤) 중 아직 안 지난 날짜를 모은다.
    입력: 오답 기록 리스트, 오늘 날짜 / 출력: [(복습 날짜, 과목, 단원, 문제 번호), ...] 날짜순"""
    result = []
    for item in wrong_list:
        for day in review_dates(item["기록일"]):
            if day >= today.strftime("%Y-%m-%d"):
                result.append((day, item["과목"], item["단원"], item["문제 번호"]))
    result.sort()
    return result


# 시험·오답 기록을 불러와 모든 분석을 한 번에 계산한다.
#   입력: 없음 / 출력: 분석 결과 딕셔너리
def analyze():
    """시험·오답 기록을 불러와 모든 분석을 한 번에 계산한다.
    출력: 분석 결과 딕셔너리"""
    today = date.today()
    exams = load_exams()
    wrong_list = load_wrongs()
    exam_title, days_left = next_exam(today)
    return {
        "today": today,
        "exam_count": len(exams),
        "wrong_count": len(wrong_list),
        "rates": subject_wrong_rates(exams),
        "units": unit_wrong_counts(wrong_list),
        "reasons": reason_counts(wrong_list),
        "exam_title": exam_title,
        "days_left": days_left,
        "priorities": study_priorities(wrong_list, days_left),
        "reviews": upcoming_reviews(wrong_list, today),
        "wrongs": wrong_list,
    }


# ---------------- 5. 보고서·그래프·복습 일정 저장 ----------------

# 분석 결과를 보고서 글자로 만든다.
#   입력: analyze()의 결과 / 출력: 보고서 문자열
def make_report_text(result):
    """분석 결과를 보고서 글자로 만든다.
    입력: analyze()의 결과 / 출력: 보고서 문자열"""
    lines = []
    lines.append("오답 분석 보고서 (" + result["today"].strftime("%Y-%m-%d") + ")")
    lines.append("시험 기록 " + str(result["exam_count"]) + "건, 오답 기록 " + str(result["wrong_count"]) + "건")
    lines.append("")
    lines.append("[과목별 오답률]")
    for subject, total, wrong, rate in result["rates"]:
        lines.append("  " + subject + ": " + str(wrong) + "/" + str(total) + "문항 틀림 → " + format(rate, ".1f") + "%")
    lines.append("")
    lines.append("[단원별 오답 수]")
    for subject, unit, count in result["units"]:
        lines.append("  " + subject + " · " + unit + ": " + str(count) + "개")
    lines.append("")
    lines.append("[틀린 이유]")
    for reason, count, percent in result["reasons"]:
        lines.append("  " + reason + ": " + str(count) + "개 (" + format(percent, ".1f") + "%)")
    lines.append("")
    if result["exam_title"] is None:
        lines.append("[공부 우선순위] 다가오는 시험 일정이 없어 남은 일수를 " + str(DEFAULT_DAYS) + "일로 계산")
    else:
        lines.append("[공부 우선순위] 다음 시험: " + result["exam_title"] + " (D-" + str(result["days_left"]) + ")")
    lines.append("  점수 = 오답 수 × 10 ÷ (남은 일수 + 1)")
    rank = 1
    for subject, unit, count, score in result["priorities"]:
        lines.append("  " + str(rank) + ". " + subject + " · " + unit + "  (오답 " + str(count) + "개, 점수 " + format(score, ".2f") + ")")
        rank += 1
    lines.append("")
    lines.append("[복습 날짜] 기록일로부터 1일·3일·7일 뒤")
    if len(result["reviews"]) == 0:
        lines.append("  남은 복습이 없어요.")
    for day, subject, unit, number in result["reviews"]:
        lines.append("  " + day + "  " + subject + " · " + unit + " " + number + "번")
    return "\n".join(lines) + "\n"


# 보고서를 data/reports/분석보고서_날짜.txt로 저장한다.
#   입력: 보고서 문자열, 날짜 / 출력: 저장한 파일 경로
def save_report(text, today):
    """[파일 쓰기] 보고서를 data/reports/분석보고서_날짜.txt로 저장한다.
    입력: 보고서 문자열, 날짜 / 출력: 저장한 파일 경로"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, "분석보고서_" + today.strftime("%Y-%m-%d") + ".txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


# 과목별 오답률 막대그래프를 data/reports/과목별오답률_날짜.png로 저장한다.
#   입력: subject_wrong_rates()의 결과, 날짜 / 출력: 저장한 파일 경로 (그릴 자료가 없으면 None)
def save_chart(rates, today):
    """[파일 쓰기] 과목별 오답률 막대그래프를 data/reports/과목별오답률_날짜.png로 저장한다.
    입력: subject_wrong_rates()의 결과, 날짜
    출력: 저장한 파일 경로 (그릴 자료가 없으면 None)"""
    if len(rates) == 0:
        print("그래프: 시험 기록이 없어 그리지 않았어요.")
        return None
    try:
        import matplotlib
        matplotlib.use("Agg")                      # 화면 없이 그림 파일만 만든다
        import matplotlib.pyplot as plt
    except ImportError:
        # matplotlib가 없는 컴퓨터에서도 프로그램이 멈추지 않고 보고서·복습 일정은 저장되게 한다
        print("그래프: matplotlib가 설치되어 있지 않아 그리지 않았어요. (설치: pip install matplotlib)")
        return None
    plt.rcParams["font.family"] = "Malgun Gothic"  # 한글 글꼴 (윈도우 맑은 고딕)
    plt.rcParams["axes.unicode_minus"] = False     # 한글 글꼴에서 마이너스(-) 깨짐 방지

    subjects = []
    values = []
    labels = []
    for subject, total, wrong, rate in rates:
        subjects.append(subject)
        values.append(rate)
        labels.append(format(rate, ".1f") + "%")

    fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
    bars = ax.bar(subjects, values, color="#4f6bff", width=0.6)
    ax.bar_label(bars, labels=labels, padding=3)
    ax.set_title("과목별 오답률 (" + today.strftime("%Y-%m-%d") + ")")
    ax.set_ylabel("오답률 (%)")
    ax.set_ylim(0, max(100, max(values) * 1.15))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, "과목별오답률_" + today.strftime("%Y-%m-%d") + ".png")
    fig.savefig(path)
    plt.close(fig)
    return path


# 오답마다 복습 날짜(1일·3일·7일 뒤)를 계산해 data/reports/복습일정.txt(메모장)로 저장한다.
#   입력: 오답 기록 리스트 / 출력: 저장한 파일 경로
def save_review_schedule(wrong_list):
    """[파일 쓰기] 오답마다 복습 날짜(1일·3일·7일 뒤)를 계산해 data/reports/복습일정.txt(메모장)로 저장한다.
    입력: 오답 기록 리스트 / 출력: 저장한 파일 경로"""
    keys = ["기록일", "시험명", "과목", "단원", "문제 번호", "1일 뒤", "3일 뒤", "7일 뒤"]
    rows = []
    for item in wrong_list:
        row = dict(item)
        dates = review_dates(item["기록일"])
        row["1일 뒤"] = dates[0]
        row["3일 뒤"] = dates[1]
        row["7일 뒤"] = dates[2]
        rows.append(row)
    path = os.path.join(REPORT_DIR, "복습일정.txt")
    textdb.write_table(path, keys, keys, rows)
    return path


# 메뉴 7: 분석 결과를 출력하고 보고서·그래프·복습 일정을 저장한다.
#   입력: 없음 / 출력: analyze()의 결과 (앱 화면에서 다시 쓰기 위해)
def analyze_and_save():
    """[출력][파일 쓰기] 메뉴 7: 분석 결과를 출력하고 보고서·그래프·복습 일정을 저장한다.
    출력: analyze()의 결과 (앱 화면에서 다시 쓰기 위해)"""
    result = analyze()
    text = make_report_text(result)
    print(text)
    print("보고서 저장:", save_report(text, result["today"]))
    chart = save_chart(result["rates"], result["today"])     # 못 그리면 이유는 save_chart가 출력한다
    if chart is not None:
        print("그래프 저장:", chart)
    print("복습 일정 저장:", save_review_schedule(result["wrongs"]))
    return result


# 이 파일만 따로 실행했을 때: python python/wrong_notes.py
if __name__ == "__main__":
    analyze_and_save()
