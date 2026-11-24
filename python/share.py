# share.py : 공유 (웹 주소·QR코드)
# - 일정·급식·교실·방문 장소·시험 목록으로 휴대폰에서도 볼 수 있는 공유 페이지(HTML)와 메모장 파일을 docs/ 폴더에 만든다
# - 프로그램 폴더 전체를 GitHub에 올리면, GitHub Pages가 docs/ 폴더를 웹 주소로 보여 준다 (git 명령 사용)
# - 웹 주소로 QR코드(docs/qr.svg)를 만든다
#
# 외부 라이브러리: qrcode (QR코드 만들기)   설치: pip install qrcode
# 설정 파일 config.txt 에 SHARE_URL(웹 주소), GITHUB_REPO(올릴 저장소 주소)를 적는다.

import os
import html
import shutil
import subprocess
from datetime import date, datetime

import schedule
import meal
import rooms
import visitors
import exam_finder

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARE_DIR = os.path.join(BASE_DIR, "docs")      # GitHub Pages가 보여 주는 폴더
QR_PATH = os.path.join(SHARE_DIR, "qr.svg")

# 공유 폴더에 같이 올릴 메모장 파일 (원본 경로)
SHARE_FILES = [schedule.SCHEDULE_PATH, meal.MEAL_PATH, rooms.ROOMS_PATH, visitors.PLACES_PATH, exam_finder.EXAM_LIST_PATH]

# 공유 페이지 공통 모양 (휴대폰 화면에 맞게)
SHARE_STYLE = """
body { margin: 0; background: #f3f6f4; color: #1c2a23; font-family: "Malgun Gothic", sans-serif; }
main { max-width: 720px; margin: 0 auto; padding: 20px 16px 40px; }
h1 { margin: 0 0 4px; font-size: 24px; }
h2 { margin: 24px 0 8px; font-size: 18px; }
.sub { margin: 0 0 16px; color: #4f6158; font-size: 14px; }
a { color: #2f7d4f; font-weight: bold; }
.menu a { display: block; background: white; border-radius: 10px; padding: 14px 16px; margin: 8px 0; text-decoration: none; }
.box { background: white; border-radius: 10px; padding: 12px 14px; margin: 8px 0; }
.box p { margin: 4px 0; }
small, .muted { color: #6b7570; }
table { width: 100%; border-collapse: collapse; background: white; font-size: 14px; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #e3e8e5; }
"""


# 공유 페이지 한 장(HTML 문서 전체)을 만든다.
#   입력: 제목, 본문 HTML / 출력: HTML 문자열
def make_page(title, body):
    """공유 페이지 한 장(HTML 문서 전체)을 만든다.
    입력: 제목, 본문 HTML / 출력: HTML 문자열"""
    back_link = "<p><a href=\"index.html\">← 광덕고 학교생활 도우미</a></p>\n"
    if title == "광덕고 학교생활 도우미":        # 첫 페이지에는 돌아가기 링크가 필요 없다
        back_link = ""
    return ("<!doctype html>\n<html lang=\"ko\">\n<head>\n<meta charset=\"utf-8\">\n"
            + "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            + "<title>" + html.escape(title) + "</title>\n<style>" + SHARE_STYLE + "</style>\n</head>\n<body>\n<main>\n"
            + back_link
            + "<h1>" + html.escape(title) + "</h1>\n"
            + "<p class=\"sub\">" + datetime.now().strftime("%Y-%m-%d %H:%M") + " 기준 · 파이썬 share.py가 만든 페이지</p>\n"
            + body + "\n</main>\n</body>\n</html>\n")


# docs/ 폴더에 페이지 파일 하나를 저장한다.
#   입력: 파일 이름, 내용 / 출력: 없음
def write_page(name, text):
    """[파일 쓰기] docs/ 폴더에 페이지 파일 하나를 저장한다. 입력: 파일 이름, 내용"""
    with open(os.path.join(SHARE_DIR, name), "w", encoding="utf-8") as f:
        f.write(text)


# 이번 달 급식 페이지 본문.
#   입력: 없음 / 출력: HTML
def meal_body():
    """이번 달 급식 페이지 본문. 출력: HTML"""
    body = ""
    for day, day_meals in meal.meals_by_day(meal.load_meals()[0]):
        body += "<div class=\"box\"><p><b>" + day + "</b></p>"
        for item in day_meals:
            dishes = []
            for dish in item["dishes"]:
                text = html.escape(dish["name"])
                if len(dish["allergies"]) > 0:
                    text += " <small>(" + html.escape(meal.allergy_text(dish["allergies"])) + ")</small>"
                dishes.append(text)
            body += ("<p>[" + html.escape(item["type"]) + "] <small>" + html.escape(item["calorie"]) + "</small><br>"
                     + ", ".join(dishes) + "</p>")
        body += "</div>"
    if body == "":
        body = "<p class=\"muted\">이번 달 급식 정보가 없어요.</p>"
    return body


# 교실 목록 페이지 본문 (건물·층·방 이름 표).
#   입력: 없음 / 출력: HTML
def rooms_body():
    """교실 목록 페이지 본문 (건물·층·방 이름 표). 출력: HTML"""
    rows = ""
    for room in rooms.load_rooms():
        rows += ("<tr><td>" + html.escape(room["building"]) + "</td><td>" + html.escape(room["floor_name"]) + "</td><td>"
                 + html.escape(room["name"]) + "</td></tr>")
    return "<table><thead><tr><th>건물</th><th>층</th><th>방 이름</th></tr></thead><tbody>" + rows + "</tbody></table>"


# 방문 장소 페이지 본문.
#   입력: 없음 / 출력: HTML
def places_body():
    """방문 장소 페이지 본문. 출력: HTML"""
    body = ""
    for place in visitors.load_places():
        body += ("<div class=\"box\"><p><b>" + html.escape(place["목적"]) + "</b></p>"
                 + "<p>" + html.escape(place["건물"] + " " + place["층"] + "층 " + place["방 이름"]) + "</p>"
                 + "<p><small>" + html.escape(place["설명"]) + "</small></p></div>")
    return body


# 시험 목록 페이지 본문 (기출문제 받는 사이트 링크).
#   입력: 없음 / 출력: HTML
def exams_body():
    """시험 목록 페이지 본문 (기출문제 받는 사이트 링크). 출력: HTML"""
    today = date.today()
    body = ""
    for exam in exam_finder.load_exam_list():
        body += ("<div class=\"box\"><p><b>" + html.escape(exam["시험명"]) + "</b></p>"
                 + "<p><small>" + html.escape(exam_finder.exam_line(exam, today)) + "</small></p>"
                 + "<p><a href=\"" + html.escape(exam["링크"]) + "\">" + exam_finder.link_label(exam, today) + " ↗</a></p></div>")
    return body


# 공유 첫 페이지 (메뉴).
#   입력: 없음 / 출력: HTML
def index_page():
    """공유 첫 페이지 (메뉴). 출력: HTML"""
    menu = ("<div class=\"menu\">"
            + "<a href=\"schedule.html\">📅 학교 일정 · D-day</a>"
            + "<a href=\"meal.html\">🍚 이번 달 급식</a>"
            + "<a href=\"rooms.html\">🏫 교실 목록</a>"
            + "<a href=\"places.html\">🧭 방문 안내</a>"
            + "<a href=\"exams.html\">📝 시험 자료</a></div>"
            + "<h2>메모장 파일</h2><p class=\"muted\">")
    for path in SHARE_FILES:
        name = os.path.basename(path)
        menu += "<a href=\"data/" + name + "\">" + name + "</a> &nbsp;"
    return make_page("광덕고 학교생활 도우미", menu + "</p>")


# 공유 폴더(docs/)에 공유 페이지 6장과 메모장 파일들을 만든다.
#   입력: 없음 / 출력: 없음
def make_share_pages():
    """[파일 읽기][파일 쓰기][출력] 공유 폴더(docs/)에 공유 페이지 6장과 메모장 파일들을 만든다.
    출력: 없음"""
    os.makedirs(os.path.join(SHARE_DIR, "data"), exist_ok=True)
    # 학교 일정 페이지는 schedule.py가 만드는 일정 페이지를 그대로 쓴다 (분류별 색·D-day)
    write_page("schedule.html", schedule.make_schedule_page(schedule.load_schedule(), date.today()))
    write_page("meal.html", make_page("이번 달 급식", meal_body()))
    write_page("rooms.html", make_page("교실 목록", rooms_body()))
    write_page("places.html", make_page("방문 안내", places_body()))
    write_page("exams.html", make_page("시험 자료", exams_body()))
    write_page("index.html", index_page())
    for path in SHARE_FILES:
        if os.path.exists(path):
            shutil.copy(path, os.path.join(SHARE_DIR, "data", os.path.basename(path)))
    print("공유 페이지를 만들었습니다:", SHARE_DIR)


# 웹 주소로 QR코드를 만들어 docs/qr.svg로 저장하고, 콘솔에도 그려 준다.
#   입력: 웹 주소 / 출력: 저장한 파일 경로 (qrcode 라이브러리가 없으면 "")
def make_qr(url):
    """[파일 쓰기][출력] 웹 주소로 QR코드를 만들어 docs/qr.svg로 저장하고, 콘솔에도 그려 준다.
    입력: 웹 주소 / 출력: 저장한 파일 경로 (qrcode 라이브러리가 없으면 "")"""
    try:
        import qrcode
        import qrcode.image.svg
    except ImportError:
        print("QR코드를 만들려면 qrcode 라이브러리가 필요합니다: pip install qrcode")
        return ""
    os.makedirs(SHARE_DIR, exist_ok=True)
    image = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathFillImage)
    image.save(QR_PATH)
    print("QR코드 저장:", QR_PATH)
    code = qrcode.QRCode(border=1)
    code.add_data(url)
    code.print_ascii(invert=True)      # 콘솔 화면에 QR코드 그리기
    return QR_PATH


# 프로그램 폴더에서 git 명령을 실행하고 결과를 출력한다.
#   입력: git 뒤에 붙일 말 리스트 / 출력: 성공하면 True
def run_git(args):
    """[출력] 프로그램 폴더에서 git 명령을 실행하고 결과를 출력한다.
    입력: git 뒤에 붙일 말 리스트 / 출력: 성공하면 True"""
    try:
        result = subprocess.run(["git"] + args, cwd=BASE_DIR, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=180)
    except FileNotFoundError:
        print("git이 설치되어 있지 않습니다.")
        return False
    except subprocess.TimeoutExpired:
        print("git", args[0], "시간이 너무 오래 걸려 멈췄습니다.")
        return False
    output = (result.stdout + result.stderr).strip()
    if output != "":
        print(output)
    return result.returncode == 0


# 프로그램 폴더(공유 페이지 docs/ 포함)를 GitHub 저장소(repo_url)의 main 브랜치에 올린다.
#   입력: 저장소 주소 / 출력: 성공하면 True
def upload_share(repo_url):
    """[출력] 프로그램 폴더를 GitHub 저장소(repo_url)의 main 브랜치에 올린다. (GitHub Pages가 docs/를 웹 주소로 보여 줌)
    인증키가 든 config.txt는 .gitignore에 있어 올라가지 않는다.
    처음이면 프로그램 폴더를 git 저장소로 만든다. 입력: 저장소 주소 / 출력: 성공하면 True"""
    if not os.path.exists(os.path.join(BASE_DIR, ".git")):
        run_git(["init", "-b", "main"])
        run_git(["remote", "add", "origin", repo_url])
    run_git(["remote", "set-url", "origin", repo_url])
    run_git(["add", "-A"])
    run_git(["-c", "user.name=gwangdeok-helper", "-c", "user.email=helper@localhost",
             "commit", "-m", "공유 페이지 업데이트 " + datetime.now().strftime("%Y-%m-%d %H:%M")])
    if run_git(["push", "-u", "origin", "main"]):
        print("웹에 올렸습니다. 1~2분 뒤 웹 주소에서 볼 수 있어요.")
        return True
    print("올리지 못했습니다. GITHUB_REPO 주소와 GitHub 로그인을 확인하세요.")
    return False


# 공유 페이지·파일 만들기 → (upload면) 웹에 올리기 → 웹 주소 QR코드 만들기
#   입력: 웹에 올릴지 / 출력: 없음
def update_share(upload=False):
    """[출력][파일 쓰기] 공유 페이지·파일 만들기 → (upload면) 웹에 올리기 → 웹 주소 QR코드 만들기
    입력: 웹에 올릴지 / 출력: 없음"""
    config = schedule.load_config()
    make_share_pages()
    if upload:
        if config.get("GITHUB_REPO", "") == "":
            print("config.txt에 GITHUB_REPO(올릴 저장소 주소)를 적어 주세요.")
        else:
            upload_share(config["GITHUB_REPO"])
    url = config.get("SHARE_URL", "")
    if url == "":
        print("config.txt에 SHARE_URL(웹 주소)을 적으면 QR코드를 만들어 드려요.")
        return
    print("웹 주소:", url)
    make_qr(url)


# 메뉴 12: 공유 페이지를 만들고, 웹에 올릴지 물어본 뒤 웹 주소와 QR코드를 보여준다.
#   입력: 없음 / 출력: 없음
def share_menu():
    """[입력][출력] 메뉴 12: 공유 페이지를 만들고, 웹에 올릴지 물어본 뒤 웹 주소와 QR코드를 보여준다."""
    answer = input("공유 페이지를 만든 뒤 웹(GitHub)에 올릴까요? (y/n): ").strip().lower()
    update_share(answer == "y")


# 이 파일만 따로 실행했을 때: python python/share.py
if __name__ == "__main__":
    share_menu()
