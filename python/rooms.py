# rooms.py : 교실 데이터 만들기 · 교실 검색
# - 3D 캠퍼스의 src/data.js(자바스크립트)를 파이썬으로 읽어 모든 건물의 방 목록을 뽑는다
# - 길 안내에 의미 없는 방(계단·복도·화장실 등)은 빼고, 같은 건물·층의 같은 이름은 하나로 합친다
# - data/rooms.txt으로 저장하고, 건물별·층별 방 개수를 출력한다
# - 검색어로 방을 찾아 "건물 이름 몇 층 방 이름" 형식으로 출력한다
#
# data.js에서 방이 만들어지는 방법 (모두 처리해야 빠지는 방이 없다)
#   RM('이름','종류',...)                    방 하나
#   CLS(['이름1','이름2',...],...)           교실 여러 개 (종류는 'class')
#   ...D_SVC                                 미리 만들어 둔 방 묶음(상수)을 펼침
#   ...J_SVC(2)                              방 묶음을 만드는 함수를 불러서 펼침
#   ...[0,1,2,3,4].map(i=>RM(f+'0'+(i+1)+'호 기숙사',...))   번호를 바꿔 가며 방 여러 개
#   [2,3,4].forEach(f=>DEOKRIN[f].push(RM(...)))              나중에 여러 층에 방 추가

import os
import re

import textdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JS_PATH = os.path.join(BASE_DIR, "src", "data.js")
ROOMS_PATH = os.path.join(BASE_DIR, "data", "rooms.txt")

# 메모장 표 파일(rooms.txt)의 칸
ROOM_KEYS = ["building", "floor", "floor_name", "name", "type", "building_id", "dong"]
ROOM_LABELS = ["건물", "층", "층 이름", "방 이름", "종류", "건물 id", "동"]

# 길 안내에 의미 없는 방 종류: 계단, 복도·홀·전실, 화장실·샤워실, 뚫린 공간, 연결복도
SKIP_TYPES = ["stair", "hall", "toilet", "void", "conn"]


# ---------------- 1. 글자 다루기 도우미 ----------------

# src/data.js 파일을 읽는다.
#   입력: 없음 / 출력: 파일 내용 전체(문자열)
def read_data_js():
    """[파일 읽기] src/data.js 파일을 읽는다.
    입력: 없음
    출력: 파일 내용 전체(문자열)"""
    with open(DATA_JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


# 괄호나 따옴표 '안'에 있는 구분자는 무시하고, 바깥에 있는 구분자로만 나눈다.
#   입력: 문자열, 구분자(기본 쉼표) / 출력: 나눈 조각들의 리스트 (앞뒤 공백 제거, 빈 조각 제외)
def split_top_level(text, separator=","):
    """괄호나 따옴표 '안'에 있는 구분자는 무시하고, 바깥에 있는 구분자로만 나눈다.
    예) "RM('a',1,2),RM('b',3,4)" → ["RM('a',1,2)", "RM('b',3,4)"]
    입력: 문자열, 구분자(기본 쉼표)
    출력: 나눈 조각들의 리스트 (앞뒤 공백 제거, 빈 조각 제외)"""
    parts = []
    depth = 0          # 지금 괄호가 몇 겹 열려 있는지
    in_quote = False   # 지금 따옴표 안인지
    current = ""
    for ch in text:
        if ch == "'":
            in_quote = not in_quote
        elif not in_quote and ch in "([{":
            depth += 1
        elif not in_quote and ch in ")]}":
            depth -= 1
        if ch == separator and depth == 0 and not in_quote:
            parts.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip() != "":
        parts.append(current.strip())
    return parts


# text[start]에 있는 여는 괄호의 짝이 되는 닫는 괄호 위치를 찾는다.
#   입력: 문자열, 여는 괄호 위치 / 출력: 닫는 괄호 위치(정수)
def find_closing(text, start):
    """text[start]에 있는 여는 괄호의 짝이 되는 닫는 괄호 위치를 찾는다.
    입력: 문자열, 여는 괄호 위치
    출력: 닫는 괄호 위치(정수)"""
    depth = 0
    in_quote = False
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "'":
            in_quote = not in_quote
        elif not in_quote and ch in "([{":
            depth += 1
        elif not in_quote and ch in ")]}":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("괄호 짝을 찾지 못했습니다: " + text[start:start + 30])


# 맨 바깥 괄호 한 겹을 벗긴다.
#   입력: 괄호로 둘러싸인 문자열 / 출력: 괄호 안쪽 문자열
def inside(text):
    """맨 바깥 괄호 한 겹을 벗긴다. 예) "[a,b]" → "a,b"
    입력: 괄호로 둘러싸인 문자열
    출력: 괄호 안쪽 문자열"""
    return text.strip()[1:-1]


# data.js에서 'const 이름=값' 의 값 부분을 찾아 돌려준다.
#   입력: data.js 내용, 상수 이름 / 출력: 값 문자열 (예: "[RM(...),RM(...)]" 또는 "f=>[...]")
def get_const(text, name):
    """data.js에서 'const 이름=값' 의 값 부분을 찾아 돌려준다.
    입력: data.js 내용, 상수 이름
    출력: 값 문자열 (예: "[RM(...),RM(...)]" 또는 "f=>[...]")"""
    match = re.search(r"const " + name + r"=", text)
    if match is None:
        raise ValueError("data.js에 없는 이름입니다: " + name)
    start = match.end()
    # 함수로 정의된 경우: f=>[...]  →  매개변수 이름과 몸통을 함께 돌려준다
    arrow = re.match(r"(\w+)=>", text[start:])
    if arrow is not None:
        body_start = start + arrow.end()
        body_end = find_closing(text, body_start)
        return text[start:body_end + 1]
    end = find_closing(text, start)
    return text[start:end + 1]


# ---------------- 2. 방 이름 계산 ----------------

# 'i+1', '18-i', '3' 같은 간단한 계산을 한다.
#   입력: 계산식 문자열, 변수 딕셔너리(예: {"i": 2}) / 출력: 정수
def calc_number(expr, variables):
    """'i+1', '18-i', '3' 같은 간단한 계산을 한다.
    입력: 계산식 문자열, 변수 딕셔너리(예: {"i": 2})
    출력: 정수"""
    expr = expr.strip()
    for op in ["+", "-"]:
        if op in expr:
            left, right = expr.split(op, 1)
            a = calc_number(left, variables)
            b = calc_number(right, variables)
            if op == "+":
                return a + b
            return a - b
    if expr in variables:
        return variables[expr]
    return int(expr)


# 방 이름 식을 계산해 글자로 만든다.
#   입력: 이름 식 문자열, 변수 딕셔너리 / 출력: 방 이름(문자열)
def eval_name(expr, variables):
    """방 이름 식을 계산해 글자로 만든다.
    예) "'가우스1실 1-8'" → 가우스1실 1-8
        "f+'0'+(i+1)+'호 기숙사'" (f=3, i=0) → 301호 기숙사
    입력: 이름 식 문자열, 변수 딕셔너리
    출력: 방 이름(문자열)"""
    name = ""
    for part in split_top_level(expr, "+"):
        if part.startswith("'"):                       # 'abc' → abc
            name += part[1:-1]
        elif part.startswith("String("):               # String(18-i) → 숫자를 글자로
            name += str(calc_number(part[len("String("):-1], variables))
        elif part.startswith("("):                     # (i+1) → 계산
            name += str(calc_number(inside(part), variables))
        else:                                          # f → 변수 값
            name += str(variables[part])
    return name


# ---------------- 3. 방 목록 읽기 ----------------

# 방 목록 식 "[...]" 을 읽어 (이름, 종류) 리스트로 만든다.
#   입력: data.js 내용, 목록 식 문자열, 변수 딕셔너리 / 출력: [(방 이름, 방 종류), ...]
def parse_room_items(text, expr, variables):
    """방 목록 식 "[...]" 을 읽어 (이름, 종류) 리스트로 만든다.
    입력: data.js 내용, 목록 식 문자열, 변수 딕셔너리
    출력: [(방 이름, 방 종류), ...]"""
    rooms = []
    for item in split_top_level(inside(expr)):
        if item.startswith("..."):
            item = item[3:]                            # 펼침(...) 표시 떼기

        if item.startswith("RM("):                     # 방 하나
            args = split_top_level(inside(item[2:]))
            rooms.append((eval_name(args[0], variables), eval_name(args[1], variables)))

        elif item.startswith("CLS("):                  # 교실 여러 개
            args = split_top_level(inside(item[3:]))
            for name in split_top_level(inside(args[0])):
                rooms.append((eval_name(name, variables), "class"))

        elif item.startswith("[") and ".map(" in item:  # [0,1,2].map(i=>RM(...))
            close = find_closing(item, 0)
            numbers = split_top_level(inside(item[:close + 1]))
            arrow = re.match(r"\.map\((\w+)=>", item[close + 1:])
            var_name = arrow.group(1)
            template = "[" + item[close + 1 + arrow.end():-1] + "]"
            for number in numbers:
                new_vars = dict(variables)
                new_vars[var_name] = int(number)
                rooms += parse_room_items(text, template, new_vars)

        elif "(" in item:                              # J_SVC(2), dorm(3) 같은 함수 부르기
            func_name = item[:item.index("(")]
            arg = calc_number(inside(item[len(func_name):]), variables)
            rooms += call_room_function(text, func_name, arg)

        else:                                          # D_SVC 같은 상수
            rooms += parse_room_items(text, get_const(text, item), variables)
    return rooms


# 'const J_SVC=f=>[...]' 같은 함수를 arg 값으로 불러서 방 목록을 만든다.
#   입력: data.js 내용, 함수 이름, 넘겨줄 값(층 번호) / 출력: [(방 이름, 방 종류), ...]
def call_room_function(text, func_name, arg):
    """'const J_SVC=f=>[...]' 같은 함수를 arg 값으로 불러서 방 목록을 만든다.
    입력: data.js 내용, 함수 이름, 넘겨줄 값(층 번호)
    출력: [(방 이름, 방 종류), ...]"""
    definition = get_const(text, func_name)
    param = definition[:definition.index("=>")]
    body = definition[definition.index("=>") + 2:]
    return parse_room_items(text, body, {param: arg})


# 'const DEOKRIN={1:[...],2:[...]}' 같은 건물 층 정보를 읽는다.
#   입력: data.js 내용, 상수 이름 / 출력: {층 번호: [(방 이름, 방 종류), ...]}
def parse_floors(text, const_name):
    """'const DEOKRIN={1:[...],2:[...]}' 같은 건물 층 정보를 읽는다.
    입력: data.js 내용, 상수 이름
    출력: {층 번호: [(방 이름, 방 종류), ...]}"""
    floors = {}
    for item in split_top_level(inside(get_const(text, const_name))):
        key, value = item.split(":", 1)
        floor = int(key)
        if value.startswith("["):
            floors[floor] = parse_room_items(text, value, {})
        else:                                          # 3:dorm(3) 처럼 함수로 만든 층
            floors[floor] = parse_room_items(text, "[" + value + "]", {})

    # [2,3,4].forEach(f=>DEOKRIN[f].push(RM(...)))  → 여러 층에 방 추가
    pattern = r"\[([\d,]+)\]\.forEach\((\w+)=>" + const_name + r"\[\w+\]\.push\("
    for match in re.finditer(pattern, text):
        push_start = match.end() - 1
        added = "[" + inside(text[push_start:find_closing(text, push_start) + 1]) + "]"
        for number in match.group(1).split(","):
            floors[int(number)] += parse_room_items(text, added, {match.group(2): int(number)})
    return floors


# BLD 배열에서 건물마다 id, 이름(n), 동(dong), 층 정보 상수 이름(floors)을 뽑는다.
#   입력: data.js 내용 / 출력: [{"id", "n", "dong", "floors"}, ...]
def parse_buildings(text):
    """BLD 배열에서 건물마다 id, 이름(n), 동(dong), 층 정보 상수 이름(floors)을 뽑는다.
    입력: data.js 내용
    출력: [{"id", "n", "dong", "floors"}, ...]"""
    buildings = []
    for item in split_top_level(inside(get_const(text, "BLD"))):
        building = {}
        for key in ["id", "n", "dong"]:
            building[key] = re.search(r"[{,]" + key + r":'([^']*)'", item).group(1)
        building["floors"] = re.search(r"[{,]floors:(\w+)", item).group(1)
        buildings.append(building)
    return buildings


# ---------------- 4. 교실 목록 만들기 ----------------

# 층을 화면에 보여줄 이름으로 바꾼다.
#   입력: 건물 id, 층 번호, 그 층의 방 개수 / 출력: 예) "4층", "옥탑"
def floor_label(building_id, floor, room_count):
    """층을 화면에 보여줄 이름으로 바꾼다. (3D 캠퍼스 model.js의 floorName과 같은 규칙)
    - 체육관: 1층, 2층은 "2층 관람석"
    - 2층 이상인데 그 층의 방(계단 포함)이 2개 이하면 계단실·물탱크실만 있는 "옥탑"
    입력: 건물 id, 층 번호, 그 층의 방 개수 / 출력: 예) "4층", "옥탑" """
    if building_id == "gym":
        if floor == 1:
            return "1층"
        return "2층 관람석"
    if floor > 1 and room_count <= 2:
        return "옥탑"
    return str(floor) + "층"


# data.js 내용에서 길 안내에 쓸 방 목록을 만든다.
#   입력: data.js 내용 / 출력: [{"name", "type", "building_id", "building", "dong", "floor", "floor_name"}, ...]
def extract_rooms(text):
    """data.js 내용에서 길 안내에 쓸 방 목록을 만든다.
    - 계단·복도·화장실·뚫린 공간·연결복도는 뺀다
    - 같은 건물·같은 층의 같은 이름은 하나로 합친다
    입력: data.js 내용
    출력: [{"name", "type", "building_id", "building", "dong", "floor", "floor_name"}, ...]"""
    rooms = []
    for building in parse_buildings(text):
        floors = parse_floors(text, building["floors"])
        for floor in sorted(floors):
            seen = []                                  # 이 층에서 이미 넣은 방 이름
            floor_name = floor_label(building["id"], floor, len(floors[floor]))
            for name, room_type in floors[floor]:
                if room_type in SKIP_TYPES or name in seen:
                    continue
                seen.append(name)
                rooms.append({"name": name, "type": room_type, "building_id": building["id"],
                              "building": building["n"], "dong": building["dong"], "floor": floor,
                              "floor_name": floor_name})
    return rooms


# 방 목록을 data/rooms.txt(메모장)로 저장한다.
#   입력: 방 딕셔너리 리스트 / 출력: 없음
def save_rooms(rooms):
    """[파일 쓰기] 방 목록을 data/rooms.txt(메모장)로 저장한다.
    입력: 방 딕셔너리 리스트
    출력: 없음"""
    textdb.write_table(ROOMS_PATH, ROOM_KEYS, ROOM_LABELS, rooms)
    print("저장 완료:", ROOMS_PATH, "(" + str(len(rooms)) + "개)")


# 건물별·층별 방 개수를 센다.
#   입력: 방 딕셔너리 리스트 / 출력: [(건물 이름, {층 이름: 개수}), ...] (data.js에 나온 건물·층 순서)
def count_rooms(rooms):
    """건물별·층별 방 개수를 센다.
    입력: 방 딕셔너리 리스트
    출력: [(건물 이름, {층 이름: 개수}), ...] (data.js에 나온 건물·층 순서)"""
    result = []
    for room in rooms:
        if len(result) == 0 or result[-1][0] != room["building"]:
            result.append((room["building"], {}))
        counts = result[-1][1]
        counts[room["floor_name"]] = counts.get(room["floor_name"], 0) + 1
    return result


# 건물별·층별 방 개수를 출력한다.
#   입력: 방 딕셔너리 리스트 / 출력: 없음
def print_room_counts(rooms):
    """[출력] 건물별·층별 방 개수를 출력한다. (data.js와 맞는지 확인용)
    입력: 방 딕셔너리 리스트
    출력: 없음"""
    print("건물별·층별 방 개수")
    for building, counts in count_rooms(rooms):
        floor_texts = []
        for floor_name in counts:
            floor_texts.append(floor_name + " " + str(counts[floor_name]))
        print("  " + building.ljust(10), "합계", str(sum(counts.values())).rjust(3), " | ", ", ".join(floor_texts))
    print("  전체", len(rooms), "개")


# ---------------- 5. 교실 검색 ----------------

# data/rooms.txt(메모장)를 읽는다.
#   입력: 없음 / 출력: 방 딕셔너리 리스트 (파일이 없으면 빈 리스트)
def load_rooms():
    """[파일 읽기] data/rooms.txt(메모장)를 읽는다.
    입력: 없음
    출력: 방 딕셔너리 리스트 (파일이 없으면 빈 리스트)"""
    if not os.path.exists(ROOMS_PATH):
        return []
    rooms = textdb.read_table(ROOMS_PATH, ROOM_KEYS, ROOM_LABELS)
    for room in rooms:
        room["floor"] = int(room["floor"])     # 파일에서 읽은 값은 글자라서 층은 숫자로 바꾼다
    return rooms


# 검색어가 '2-3' 같은 반 이름인지 확인한다.
#   입력: 검색어 / 출력: True / False
def is_class_number(query):
    """검색어가 '2-3' 같은 반 이름인지 확인한다.
    입력: 검색어
    출력: True / False"""
    return re.fullmatch(r"\d-\d{1,2}", query) is not None


# 검색어로 방을 찾는다.
#   입력: 방 딕셔너리 리스트, 검색어 / 출력: 찾은 방 리스트
def search_rooms(rooms, query):
    """검색어로 방을 찾는다.
    - 반 이름(예: 2-3)이면 방 이름 속 반 번호가 정확히 같은 방만 찾는다 (2-1을 찾을 때 2-10이 나오지 않게)
    - 그 밖에는 방 이름에 검색어가 들어 있는 방을 찾는다 (띄어쓰기·대소문자 무시)
    입력: 방 딕셔너리 리스트, 검색어
    출력: 찾은 방 리스트"""
    query = query.strip()
    found = []
    if query == "":
        return found
    for room in rooms:
        if is_class_number(query):
            if query in re.findall(r"\d-\d{1,2}", room["name"]):
                found.append(room)
        else:
            name = room["name"].replace(" ", "").lower()
            if query.replace(" ", "").lower() in name:
                found.append(room)
    return found


# 방 하나를 "건물 이름 몇 층 방 이름" 글자로 만든다.
#   입력: 방 딕셔너리 / 출력: 예) "덕린관 4층 Lincoln 2-3", "만대관 옥탑 물탱크실"
def room_text(room):
    """방 하나를 "건물 이름 몇 층 방 이름" 글자로 만든다.
    입력: 방 딕셔너리
    출력: 예) "덕린관 4층 Lincoln 2-3", "만대관 옥탑 물탱크실" """
    floor_name, name = room["floor_name"], room["name"]
    if name.startswith(floor_name):          # 예) 옥탑 + "옥탑 창고" → "옥탑 창고"만
        return room["building"] + " " + name
    if floor_name.endswith(name):            # 예) "2층 관람석" + 관람석 → "2층 관람석"만
        return room["building"] + " " + floor_name
    return room["building"] + " " + floor_name + " " + name


# ---------------- main.py 메뉴에서 부르는 함수 ----------------

# 메뉴 3: data.js를 읽어 rooms.txt를 만들고 건물별·층별 개수를 출력한다.
#   입력: 없음 / 출력: 없음
def make_rooms():
    """[출력] 메뉴 3: data.js를 읽어 rooms.txt를 만들고 건물별·층별 개수를 출력한다."""
    print("data.js 읽는 중:", DATA_JS_PATH)
    if not os.path.exists(DATA_JS_PATH):
        print("  3D 캠퍼스 데이터(src/data.js)가 없어 새로 만들지 못했습니다. 저장해 둔 교실 목록을 그대로 씁니다.")
        return
    rooms = extract_rooms(read_data_js())
    save_rooms(rooms)
    print_room_counts(rooms)


# 메뉴 4: 검색어를 입력받아 찾은 방을 출력한다.
#   입력: 없음 / 출력: 없음
def search_menu():
    """[입력][출력] 메뉴 4: 검색어를 입력받아 찾은 방을 출력한다. 빈 칸을 입력하면 끝낸다."""
    rooms = load_rooms()
    if len(rooms) == 0:
        print("교실 목록이 없습니다. 먼저 '3 교실 목록 만들기'를 실행하세요.")
        return
    while True:
        query = input("찾을 교실 (예: 과학실, 2-3 / 그만하려면 Enter): ").strip()
        if query == "":
            return
        found = search_rooms(rooms, query)
        if len(found) == 0:
            print("  '" + query + "'(이)가 들어간 교실을 찾지 못했어요.")
        for room in found:
            print("  " + room_text(room))


# 이 파일만 따로 실행했을 때: python python/rooms.py
if __name__ == "__main__":
    make_rooms()
    search_menu()
