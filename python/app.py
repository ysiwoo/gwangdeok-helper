# app.py : 광덕고 학교생활 도우미 - 앱 창 모드
# 1) 내 컴퓨터 안에서만 쓰는 작은 웹 서버를 켠다 (표준 라이브러리 http.server)
# 2) Edge를 주소창 없는 "앱 창"으로 연다 → 프로그램처럼 보인다
# 3) 화면의 버튼을 누르면 이 서버가 파이썬 함수를 실행하고, 결과 화면(HTML)을 screens.py가 만들어 돌려준다
# 4) 앱 창을 닫으면 (화면이 보내던 신호가 끊기면) 서버도 스스로 꺼진다
# 콘솔 모드(input/print 메뉴)는 main.py 에 그대로 있다.

import os
import time
import threading
import subprocess
import webbrowser
import json
import urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import screens
import rooms

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8765               # 항상 같은 번호를 써야 플래너에 저장한 내용이 유지된다
URL = "http://127.0.0.1:" + str(PORT) + "/"
QUIT_AFTER = 150          # 화면에서 신호가 이만큼(초) 안 오면 서버를 끈다

last_ping = time.time()   # 화면이 마지막으로 신호를 보낸 시각


# 브라우저 요청을 처리한다.
class AppHandler(SimpleHTTPRequestHandler):
    """브라우저 요청을 처리한다.
    /api/... 로 오면 파이썬 기능을 실행하고, 나머지는 프로젝트 폴더의 파일을 보내 준다."""

    # 파일 종류를 직접 정해 둔다. (Windows가 .js 종류를 잘못 알려주는 경우가 있고,
    # charset=utf-8을 붙이지 않으면 <meta charset>이 없는 3D 캠퍼스 페이지의 한글이 깨진다)
    extensions_map = dict(SimpleHTTPRequestHandler.extensions_map)
    extensions_map[".html"] = "text/html; charset=utf-8"
    extensions_map[".js"] = "text/javascript; charset=utf-8"
    extensions_map[".json"] = "application/json; charset=utf-8"
    extensions_map[".csv"] = "text/csv; charset=utf-8"
    extensions_map[".txt"] = "text/plain; charset=utf-8"

    # 프로젝트 폴더의 파일을 보내 주는 서버로 준비한다.
    #   입력: 없음 / 출력: 없음
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    # 요청 기록은 출력하지 않는다.
    #   입력: 없음 / 출력: 없음
    def log_message(self, *args):
        """요청 기록은 출력하지 않는다. (창 없이 실행할 때 출력할 곳이 없어서)"""
        pass

    # 파일을 고치면 바로 보이도록, 브라우저가 옛 내용을 저장해 두지 않게 한다.
    #   입력: 없음 / 출력: 없음
    def end_headers(self):
        """파일을 고치면 바로 보이도록, 브라우저가 옛 내용을 저장해 두지 않게 한다."""
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    # HTML 글자를 브라우저로 보낸다.
    #   입력: HTML 문자열 / 출력: 없음
    def send_html(self, text):
        """HTML 글자를 브라우저로 보낸다.
        입력: HTML 문자열"""
        data = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # 파이썬 값(리스트·딕셔너리)을 JSON 글자로 바꿔 브라우저로 보낸다.
    #   입력: 리스트 또는 딕셔너리 / 출력: 없음
    def send_json(self, value):
        """파이썬 값(리스트·딕셔너리)을 JSON 글자로 바꿔 브라우저로 보낸다.
        입력: 리스트 또는 딕셔너리"""
        data = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # 브라우저가 주소를 열 때(GET): 첫 화면이면 app.html, /api/ 이면 파이썬 기능, 나머지는 파일을 보낸다.
    #   입력: 없음 / 출력: 없음
    def do_GET(self):
        """브라우저가 주소를 열 때(GET): 첫 화면이면 app.html, /api/ 이면 파이썬 기능, 나머지는 파일을 보낸다."""
        url = urlparse(self.path)
        if url.path == "/":
            self.path = "/app.html"
        elif url.path.startswith("/python/"):
            self.send_error(404)          # 파이썬 코드·설정(인증키) 파일은 보내지 않는다
            return
        elif url.path.startswith("/api/"):
            self.handle_api(url, {})
            return
        super().do_GET()

    # 버튼·입력 칸에서 보낼 때(POST): 입력값을 딕셔너리로 바꿔 파이썬 기능에 넘긴다.
    #   입력: 없음 / 출력: 없음
    def do_POST(self):
        """버튼·입력 칸에서 보낼 때(POST): 입력값을 딕셔너리로 바꿔 파이썬 기능에 넘긴다."""
        url = urlparse(self.path)
        if not url.path.startswith("/api/"):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        form = {}
        if self.headers.get("Content-Type", "").startswith("application/json"):
            form["json"] = json.loads(body)          # 플래너는 JSON으로 보낸다
        else:
            for key, values in parse_qs(body).items():
                form[key] = values[0]
        self.handle_api(url, form)

    # /api/ 요청을 처리한다.
    #   출력: 없음
    def handle_api(self, url, form):
        """/api/ 요청을 처리한다.
        /api/ping            : 화면이 아직 열려 있다는 신호
        /api/screen?tab=rooms : 그 탭의 화면 HTML
        /api/rooms/find?q=2-3 : 교실 검색 결과 (JSON, 3D 캠퍼스 화면이 씀)
        /api/<기능>?from=탭  : 기능 실행 후 결과 화면 HTML"""
        global last_ping
        query = parse_qs(url.query)
        name = url.path[len("/api/"):]
        from_tab = query.get("from", ["schedule"])[0]
        last_ping = time.time()

        if name == "ping":
            self.send_html("ok")
        elif name == "quit":
            # 새로 켜지는 앱이 "꺼 달라"고 할 때: 응답을 보낸 뒤 서버를 끈다
            self.send_html("bye")
            threading.Thread(target=self.server.shutdown).start()
        elif name == "rooms/find":
            # 3D 캠퍼스 화면의 검색창: rooms.py로 찾고, 결과를 JSON으로 돌려준다
            found = rooms.search_rooms(rooms.load_rooms(), query.get("q", [""])[0])
            result = []
            for room in found:
                result.append({"building_id": room["building_id"], "floor": room["floor"],
                               "name": room["name"], "text": rooms.room_text(room)})
            self.send_json(result)
        elif name == "screen":
            self.send_html(screens.get_screen(query.get("tab", ["schedule"])[0]))
        else:
            try:
                self.send_html(screens.run_action(name, from_tab, form))
            except Exception as error:
                self.send_html(screens.card("ERROR", "실행 중 오류가 났어요",
                                            "<pre>" + screens.html.escape(str(error)) + "</pre>"))


# 같은 번호(포트)에 서버가 두 개 켜지지 않게 한 앱 서버.
class AppServer(ThreadingHTTPServer):
    """앱 서버. 윈도우에서는 기본 설정이면 같은 번호(포트)에 서버가 두 개 켜질 수 있어서 그것을 막는다."""
    allow_reuse_address = False


# 서버를 켠다.
#   입력: 없음 / 출력: 서버 객체. 이미 다른 서버가 그 번호를 쓰고 있으면 None
def start_server():
    """서버를 켠다.
    출력: 서버 객체. 이미 다른 서버가 그 번호를 쓰고 있으면 None"""
    try:
        return AppServer(("127.0.0.1", PORT), AppHandler)
    except OSError:
        return None


# Edge 실행 파일 위치를 찾는다.
#   입력: 없음 / 출력: 경로 문자열, 없으면 None
def find_edge():
    """Edge 실행 파일 위치를 찾는다.
    출력: 경로 문자열, 없으면 None"""
    places = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
    for place in places:
        if os.path.exists(place):
            return place
    return None


# 앱 창을 연다.
#   입력: 없음 / 출력: 없음
def open_window():
    """앱 창을 연다. Edge가 있으면 주소창 없는 앱 창으로, 없으면 기본 브라우저로 연다."""
    edge = find_edge()
    if edge is None:
        webbrowser.open(URL)
    else:
        subprocess.Popen([edge, "--app=" + URL, "--window-size=1280,860"])


# 화면에서 신호가 오래 안 오면(앱 창을 닫으면) 서버를 끈다.
#   입력: 서버 객체 / 출력: 없음
def watch_and_quit(server):
    """화면에서 신호가 오래 안 오면(앱 창을 닫으면) 서버를 끈다.
    입력: 서버 객체"""
    while True:
        time.sleep(5)
        if time.time() - last_ping > QUIT_AFTER:
            server.shutdown()
            return


# 서버를 켜고(이미 켜져 있으면 예전 것을 끄고 새로 켬), 앱 창을 연 뒤, 창이 닫힐 때까지 요청을 처리한다.
#   입력: 없음 / 출력: 없음
def main():
    """서버를 켜고(이미 켜져 있으면 예전 것을 끄고 새로 켬), 앱 창을 연 뒤, 창이 닫힐 때까지 요청을 처리한다."""
    server = start_server()
    if server is None:
        # 이미 켜져 있는 앱은 고치기 전 코드일 수 있으므로, 꺼 달라고 한 뒤 새로 켠다
        try:
            urllib.request.urlopen(URL + "api/quit", timeout=3)
        except Exception:
            pass
        for i in range(10):
            time.sleep(0.5)
            server = start_server()
            if server is not None:
                break
    if server is None:
        open_window()          # 그래도 안 되면 켜져 있는 앱의 창만 연다
        return
    threading.Thread(target=watch_and_quit, args=(server,), daemon=True).start()
    open_window()
    server.serve_forever()


if __name__ == "__main__":
    main()
