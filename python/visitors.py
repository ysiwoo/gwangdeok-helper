# visitors.py : 방문객 안내 (자주 찾는 곳 · 방문 목적별 안내)
# - data/places.txt(목적, 건물, 층, 방 이름, 설명)를 읽는다. 학교 사정이 바뀌면 이 메모장 파일만 고치면 된다
# - rooms.txt(교실 목록)에서 그 방을 찾아, 실제로 있는 방인지 확인하고 위치를 알려준다
# - 앱에서는 버튼을 누르면 3D 캠퍼스에서 그 방으로 이동한다

import os

import rooms
import textdb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLACES_PATH = os.path.join(BASE_DIR, "data", "places.txt")
PLACE_KEYS = ["목적", "건물", "층", "방 이름", "설명"]


# data/places.txt를 읽는다.
#   입력: 없음 / 출력: [{"목적", "건물", "층", "방 이름", "설명"}, ...] (파일이 없으면 빈 리스트)
def load_places():
    """[파일 읽기] data/places.txt를 읽는다.
    출력: [{"목적", "건물", "층", "방 이름", "설명"}, ...] (파일이 없으면 빈 리스트)"""
    if not os.path.exists(PLACES_PATH):
        return []
    return textdb.read_table(PLACES_PATH, PLACE_KEYS, PLACE_KEYS)


# 안내 장소가 교실 목록(rooms.txt)에 있는지 찾는다.
#   입력: 장소 딕셔너리, 교실 목록 / 출력: 찾은 방 딕셔너리, 없으면 None
def find_room(place, all_rooms):
    """안내 장소가 교실 목록(rooms.txt)에 있는지 찾는다.
    입력: 장소 딕셔너리, 교실 목록
    출력: 찾은 방 딕셔너리, 없으면 None"""
    for room in all_rooms:
        if (room["building"] == place["건물"] and str(room["floor"]) == place["층"]
                and room["name"] == place["방 이름"]):
            return room
    return None


# 안내 장소마다 실제 방 정보를 붙인 목록을 만든다.
#   입력: 없음 / 출력: [{"purpose", "text", "desc", "room"}, ...]  (room이 None이면 교실 목록에 없는 방)
def place_list():
    """안내 장소마다 실제 방 정보를 붙인 목록을 만든다.
    출력: [{"purpose", "text", "desc", "room"}, ...]  (room이 None이면 교실 목록에 없는 방)"""
    all_rooms = rooms.load_rooms()
    result = []
    for place in load_places():
        room = find_room(place, all_rooms)
        text = place["건물"] + " " + place["층"] + "층 " + place["방 이름"]
        result.append({"purpose": place["목적"], "text": text, "desc": place["설명"], "room": room})
    return result


# 메뉴 8: 방문 목적 목록을 보여주고, 번호를 고르면 위치와 설명을 출력한다.
#   입력: 없음 / 출력: 없음
def show_places():
    """[입력][출력] 메뉴 8: 방문 목적 목록을 보여주고, 번호를 고르면 위치와 설명을 출력한다. Enter면 끝."""
    places = place_list()
    if len(places) == 0:
        print("data/places.txt에 안내 장소가 없습니다.")
        return
    while True:
        print("\n어떤 일로 오셨나요?")
        number = 1
        for place in places:
            print("  " + str(number).rjust(2) + ". " + place["purpose"])
            number += 1
        text = input("번호 (그만하려면 Enter): ").strip()
        if text == "":
            return
        if not text.isdigit() or not (1 <= int(text) <= len(places)):
            print("  1부터 " + str(len(places)) + " 사이의 번호를 입력하세요.")
            continue
        place = places[int(text) - 1]
        print("\n  → " + place["text"])
        print("    " + place["desc"])
        if place["room"] is None:
            print("    (교실 목록에 없는 방이에요. places.txt의 건물·층·방 이름을 확인하세요)")
        else:
            print("    앱의 「교사·방문객」 탭에서 누르면 3D 캠퍼스로 위치를 볼 수 있어요.")


# 이 파일만 따로 실행했을 때: python python/visitors.py
if __name__ == "__main__":
    show_places()
