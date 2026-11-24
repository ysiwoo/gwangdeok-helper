# share.py : 공유 (웹 주소·QR코드)
# - 앱의 8개 탭(플래너·일정·급식·교실·시험 자료·오답 노트·3D 캠퍼스·방문객)을 앱과 같은 모양의 웹 페이지로 docs/ 폴더에 만든다
# - 프로그램 폴더 전체를 GitHub에 올리면, GitHub Pages가 docs/ 폴더를 웹 주소로 보여 준다 (git 명령 사용)
# - 웹 주소로 QR코드(docs/qr.svg)를 만든다
#
# 외부 라이브러리: qrcode (QR코드 만들기)   설치: pip install qrcode
# 설정 파일 config.txt 에 SHARE_URL(웹 주소), GITHUB_REPO(올릴 저장소 주소)를 적는다.

import os
import re
import html
import shutil
import subprocess
from datetime import datetime
from urllib.parse import urlencode

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

# 앱과 같은 탭 (주소 파일 이름, 탭 이름). 첫 화면(index.html)은 앱처럼 스터디 플래너
TABS = [("index.html", "planner", "스터디 플래너"), ("schedule.html", "schedule", "학교 일정"), ("meal.html", "meal", "급식"),
        ("rooms.html", "rooms", "교실 찾기"), ("exams.html", "exams", "시험 자료"), ("notes.html", "notes", "오답 노트"),
        ("campus.html", "campus", "3D 캠퍼스"), ("guide.html", "guide", "방문객")]

# 웹에서만 더하는 모양: 탭 링크, 「앱에서만 쓸 수 있어요」 알림
WEB_STYLE = """
a.tab { text-decoration: none; }
a.place, a.btn { text-decoration: none; color: inherit; }
.web-toast { position: fixed; left: 50%; bottom: 28px; transform: translateX(-50%); z-index: 10; max-width: calc(100% - 32px);
  background: var(--ink); color: var(--paper); padding: 12px 18px; border-radius: 12px; font-size: 0.92rem;
  box-shadow: 0 6px 24px rgba(16, 24, 40, 0.25); text-align: center; }
"""

# 웹에는 파이썬 서버가 없으므로, 파이썬이 필요한 버튼(저장·AI·업데이트 등)을 누르면 알림만 보여 준다
WEB_SCRIPT = """<script>
// 이 스크립트는 알림을 보여 주는 일만 한다. (계산·저장은 파이썬 앱에서 한다)
var toastTimer = null;
function showAppOnly() {
  var box = document.querySelector(".web-toast");
  if (!box) { box = document.createElement("div"); box.className = "web-toast"; box.setAttribute("role", "status"); document.body.appendChild(box); }
  box.textContent = "이 기능은 내 컴퓨터의 「학교생활 도우미」 앱에서만 쓸 수 있어요. 웹 공유 페이지는 보기만 할 수 있어요.";
  box.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(function () { box.hidden = true; }, 3200);
}
document.addEventListener("submit", function (e) {
  if (e.target.closest("form[data-action]")) { e.preventDefault(); showAppOnly(); }
});
document.addEventListener("click", function (e) {
  var button = e.target.closest("button[data-action]");
  if (button && !button.form) { e.preventDefault(); showAppOnly(); }
});
</script>"""


# app.html에서 화면 모양(CSS)만 꺼낸다.
#   입력: 없음 / 출력: CSS 글자
def app_style():
    """[파일 읽기] 앱 화면 틀(app.html)의 <style> 안쪽 글자를 꺼낸다. (웹 페이지도 앱과 같은 모양이 되게)
    출력: CSS 글자"""
    with open(os.path.join(BASE_DIR, "app.html"), "r", encoding="utf-8") as f:
        text = f.read()
    return text[text.index("<style>") + len("<style>"):text.index("</style>")]


# 앱 화면의 버튼 중 웹에서도 쓸 수 있는 것을 링크로 바꾼다.
#   입력: 화면 HTML / 출력: 웹용 HTML
def web_links(page):
    """「3D에서 보기」·방문 목적 버튼을 3D 캠퍼스 링크로 바꾸고, 그림 주소를 웹 폴더에 맞춘다.
    입력: 화면 HTML / 출력: 웹용 HTML"""
    page = re.sub(r'<button class="([^"]*)" data-room="([^"]*)">(.*?)</button>',
                  r'<a class="\1" href="campus.html#\2">\3</a>', page, flags=re.S)
    page = page.replace('src="docs/qr.svg', 'src="qr.svg')
    return page


# 앱과 같은 모양의 웹 페이지 한 장을 만든다.
#   입력: 탭 이름, 내용 HTML / 출력: HTML 문서 전체
def make_page(tab, content):
    """앱과 같은 모양(위쪽 탭 줄 + 카드)의 웹 페이지 한 장을 만든다.
    파이썬이 필요한 버튼을 누르면 「앱에서만 쓸 수 있어요」 알림이 뜬다.
    입력: 탭 이름(예: "meal"), 내용 HTML / 출력: HTML 문서 전체"""
    nav = ""
    for file_name, name, label in TABS:
        active = ""
        if name == tab:
            active = " active"
        nav += '<a class="tab' + active + '" href="' + file_name + '">' + label + "</a>"
    if tab == "campus":
        body = '<div id="frames"><iframe id="campus" src="3d/index.html" title="3D 캠퍼스"></iframe></div>'
    else:
        body = '<main id="view">' + content + "</main>"
    script = WEB_SCRIPT
    if tab == "campus":   # 주소 끝(#b=건물&f=층&r=방)을 3D 화면에 넘겨 그 교실로 이동시킨다
        script = ('<script>if (location.hash) document.getElementById("campus").src = "3d/index.html" + location.hash;</script>')
    return ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
            + '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + "<title>광덕고 학교생활 도우미</title>\n"
            + '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap">\n'
            + '<link rel="stylesheet" href="app.css">\n</head>\n<body>\n'
            + '<header class="topbar"><div class="brand"><span class="brand-mark"></span>광덕고 학교생활 도우미</div>'
            + '<nav class="view-tabs" aria-label="화면 선택">' + nav + "</nav></header>\n"
            + "<!-- " + datetime.now().strftime("%Y-%m-%d %H:%M") + " 기준 · 파이썬 share.py가 앱 화면을 그대로 만든 공유 페이지 -->\n"
            + '<div class="stage">' + body + "</div>\n" + script + "\n</body>\n</html>\n")


# docs/ 폴더에 파일 하나를 저장한다.
#   입력: 파일 이름, 내용 / 출력: 없음
def write_page(name, text):
    """[파일 쓰기] docs/ 폴더에 파일 하나를 저장한다. 입력: 파일 이름, 내용"""
    with open(os.path.join(SHARE_DIR, name), "w", encoding="utf-8") as f:
        f.write(text)


# 웹의 교실 찾기 탭에 붙일 전체 교실 목록 (웹에서는 검색 대신 목록에서 고른다).
#   입력: 없음 / 출력: HTML
def all_rooms_card():
    """웹의 「교실 찾기」 탭에 붙일 전체 교실 목록. 누르면 3D 캠퍼스에서 그 교실로 이동한다.
    (웹에는 파이썬 서버가 없어 검색 대신 목록을 미리 만들어 둔다) 출력: HTML"""
    import screens
    rows = ""
    for room in rooms.load_rooms():
        target = urlencode({"b": room["building_id"], "f": room["floor"], "r": room["name"]})
        rows += ('<li><span class="place">' + html.escape(room["building"] + " " + room["floor_name"]) + "</span>"
                 + '<span class="room-name">' + html.escape(room["name"]) + "</span>"
                 + '<button class="btn small" data-room="' + html.escape(target) + '">3D에서 보기</button></li>')
    return screens.card("ALL ROOMS", "전체 교실 목록 · " + str(len(rooms.load_rooms())) + "개", '<ul class="room-list">' + rows + "</ul>")


# 공유 폴더(docs/)에 앱과 같은 모양의 웹 페이지 8장과 메모장 파일들을 만든다.
#   입력: 없음 / 출력: 없음
def make_share_pages():
    """[파일 읽기][파일 쓰기][출력] 공유 폴더(docs/)에 앱의 8개 탭을 앱과 같은 모양의 웹 페이지로 만든다.
    탭 화면은 앱과 똑같이 screens.py가 만들고, 3D 캠퍼스와 메모장 파일도 함께 복사한다.
    출력: 없음"""
    import screens                       # screens.py도 share.py를 쓰므로, 필요할 때 불러온다
    os.makedirs(os.path.join(SHARE_DIR, "data", "reports"), exist_ok=True)
    os.makedirs(os.path.join(SHARE_DIR, "3d"), exist_ok=True)
    write_page("app.css", app_style() + WEB_STYLE)
    for file_name, tab, label in TABS:
        content = ""
        if tab != "campus":
            content = screens.get_screen(tab)          # 앱과 똑같이 「AI에게 물어보기」 카드까지
        if tab == "rooms":
            content += all_rooms_card()
        write_page(file_name, make_page(tab, web_links(content)))
    shutil.copy(os.path.join(BASE_DIR, "index.html"), os.path.join(SHARE_DIR, "3d", "index.html"))
    for path in SHARE_FILES:
        if os.path.exists(path):
            shutil.copy(path, os.path.join(SHARE_DIR, "data", os.path.basename(path)))
    reports = os.path.join(BASE_DIR, "data", "reports")
    if os.path.exists(reports):           # 오답 노트의 오답률 그래프 그림
        for name in os.listdir(reports):
            if name.endswith(".png"):
                shutil.copy(os.path.join(reports, name), os.path.join(SHARE_DIR, "data", "reports", name))
    for old in ["places.html"]:           # 예전 공유 페이지 이름 정리
        if os.path.exists(os.path.join(SHARE_DIR, old)):
            os.remove(os.path.join(SHARE_DIR, old))
    print("공유 페이지를 만들었습니다:", SHARE_DIR, "(앱과 같은 탭 8개)")


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
