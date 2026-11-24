# textdb.py : 메모장(.txt) 표 파일 읽기·쓰기
# 이 프로그램의 데이터는 모두 메모장으로 열어 볼 수 있는 .txt 파일에 저장한다.
#
# 파일 모양 (칸 사이는 Tab 키 한 번)
#   날짜        과목    내용              ← 첫 줄: 제목
#   2026-11-20  한국사  근현대사 보고서   ← 둘째 줄부터: 한 줄에 한 건
#
# 메모장에서 직접 고쳐도 된다. (칸을 나눌 때는 Tab 키)

import os

SEP = "\t"   # 칸을 나누는 글자 (Tab)


# 값 안에 Tab이나 줄바꿈이 있으면 표가 깨지므로 빈칸으로 바꾼다.
#   입력: 값(문자열·숫자) / 출력: 문자열
def clean(value):
    """값 안에 Tab이나 줄바꿈이 있으면 표가 깨지므로 빈칸으로 바꾼다.
    입력: 값(문자열·숫자) / 출력: 문자열"""
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


# 값 리스트를 Tab으로 이은 한 줄로 만든다.
#   입력: 값 리스트 / 출력: 줄 문자열(끝에 줄바꿈)
def make_line(values):
    """값 리스트를 Tab으로 이은 한 줄로 만든다. 입력: 값 리스트 / 출력: 줄 문자열(끝에 줄바꿈)"""
    parts = []
    for value in values:
        parts.append(clean(value))
    return SEP.join(parts) + "\n"


# 메모장 표 파일을 읽는다.
#   입력: 파일 경로, 프로그램에서 쓸 이름 리스트(keys), 파일 첫 줄에 보일 제목 리스트(labels) / 출력: 한 줄씩 딕셔너리로 바꾼 리스트 (칸 순서대로 keys에 연결)
def read_table(path, keys, labels):
    """[파일 읽기] 메모장 표 파일을 읽는다. 파일이 없으면 제목 줄만 있는 새 파일을 만든다.
    입력: 파일 경로, 프로그램에서 쓸 이름 리스트(keys), 파일 첫 줄에 보일 제목 리스트(labels)
    출력: 한 줄씩 딕셔너리로 바꾼 리스트 (칸 순서대로 keys에 연결)"""
    if not os.path.exists(path):
        write_table(path, keys, labels, [])
        return []
    with open(path, "r", encoding="utf-8-sig") as f:   # 메모장이 BOM을 붙여 저장해도 읽을 수 있게
        lines = f.readlines()
    rows = []
    for line in lines[1:]:                             # 첫 줄은 제목이라 건너뛴다
        if line.strip() == "":
            continue
        values = line.rstrip("\r\n").split(SEP)
        row = {}
        for i in range(len(keys)):
            if i < len(values):
                row[keys[i]] = values[i].strip()
            else:
                row[keys[i]] = ""                      # 칸이 모자라면 빈칸으로
        rows.append(row)
    return rows


# 메모장 표 파일을 새로 쓴다.
#   입력: 파일 경로, 이름 리스트(keys), 제목 리스트(labels), 딕셔너리 리스트 / 출력: 없음
def write_table(path, keys, labels, rows):
    """[파일 쓰기] 메모장 표 파일을 새로 쓴다. (원래 내용은 지워진다)
    입력: 파일 경로, 이름 리스트(keys), 제목 리스트(labels), 딕셔너리 리스트
    출력: 없음"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(make_line(labels))
        for row in rows:
            values = []
            for key in keys:
                values.append(row.get(key, ""))
            f.write(make_line(values))


# 메모장 표 파일 끝에 한 줄을 덧붙인다.
#   입력: 파일 경로, 이름 리스트, 제목 리스트, 딕셔너리 / 출력: 없음
def append_row(path, keys, labels, row):
    """[파일 쓰기] 메모장 표 파일 끝에 한 줄을 덧붙인다. (원래 내용은 그대로, "a" 모드)
    입력: 파일 경로, 이름 리스트, 제목 리스트, 딕셔너리
    출력: 없음"""
    if not os.path.exists(path):
        write_table(path, keys, labels, [])
    # 메모장에서 고친 뒤 마지막 줄에 줄바꿈 없이 저장했으면, 새 줄이 이어 붙지 않게 줄바꿈부터 넣는다
    with open(path, "r", encoding="utf-8-sig") as f:
        text = f.read()
    values = []
    for key in keys:
        values.append(row.get(key, ""))
    with open(path, "a", encoding="utf-8") as f:
        if text != "" and not text.endswith("\n"):
            f.write("\n")
        f.write(make_line(values))
