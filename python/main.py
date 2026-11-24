# main.py : 광덕고 학교생활 도우미 - 메뉴 프로그램
# 실행하면 메뉴를 보여주고, 번호를 입력받아 해당 기능을 실행한다. 0번이면 종료한다.

import schedule
import rooms
import wrong_notes
import visitors
import meal
import exam_finder
import share
import planner

LAST_MENU = 13   # 가장 큰 메뉴 번호


# 메뉴를 화면에 보여준다.
#   입력: 없음 / 출력: 없음
def show_menu():
    """[출력] 메뉴를 화면에 보여준다.
    입력: 없음
    출력: 없음"""
    print()
    print("========== 광덕고 학교생활 도우미 ==========")
    print(" [학생]")
    print("  1 학교 일정 업데이트      5 시험 기록 입력")
    print("  2 D-day 보기              6 오답 기록 입력")
    print("  3 교실 목록 만들기        7 오답 분석·보고서 저장")
    print("  4 교실 검색              11 시험 자료 찾기")
    print(" [방문객 · 교사 · 모두]")
    print("  8 방문 안내 (어디로 가야 하나요?)")
    print("  9 수행평가 등록")
    print(" 10 이번 달 급식")
    print(" 12 공유 (웹 주소·QR코드)")
    print(" 13 스터디 플래너 (할 일·공부 시간)")
    print("  0 종료")
    print("============================================")


# 메뉴 번호를 입력받는다.
#   입력: 없음 (키보드로 입력) / 출력: 메뉴 번호(정수)
def input_menu_number():
    """[입력] 메뉴 번호를 입력받는다. 0~13이 아닌 값이면 다시 입력받는다.
    입력: 없음 (키보드로 입력)
    출력: 메뉴 번호(정수)"""
    while True:
        text = input("번호를 입력하세요: ").strip()
        if text.isdigit() and 0 <= int(text) <= LAST_MENU:
            return int(text)
        print("0부터 " + str(LAST_MENU) + " 사이의 숫자를 입력하세요.")


# 메뉴 프로그램을 시작하고, Ctrl+C를 눌러도 오류 화면 없이 끝낸다.
#   입력: 없음 / 출력: 없음
def main():
    """메뉴를 반복해서 보여주고, 고른 번호의 기능을 실행한다. 0이면 끝낸다.
    Ctrl+C를 누르거나 입력이 끝나면(Ctrl+Z) 오류 화면 없이 종료한다."""
    try:
        run_menu()
    except (KeyboardInterrupt, EOFError):
        print("\n프로그램을 종료합니다.")


# 메뉴를 반복해서 보여주고, 고른 번호의 기능을 실행한다.
#   입력: 없음 / 출력: 없음
def run_menu():
    """[입력][출력] 메뉴를 반복해서 보여주고, 고른 번호의 기능을 실행한다. 0이면 끝낸다."""
    while True:
        show_menu()
        number = input_menu_number()
        if number == 0:
            print("프로그램을 종료합니다.")
            break
        elif number == 1:
            schedule.update_schedule()
        elif number == 2:
            schedule.show_dday()
        elif number == 3:
            rooms.make_rooms()
        elif number == 4:
            rooms.search_menu()
        elif number == 5:
            wrong_notes.input_exam()
        elif number == 6:
            wrong_notes.input_wrong()
        elif number == 7:
            wrong_notes.analyze_and_save()
        elif number == 8:
            visitors.show_places()
        elif number == 9:
            schedule.input_performance()
        elif number == 10:
            meal.show_meals()
        elif number == 11:
            exam_finder.search_exams_menu()
        elif number == 12:
            share.share_menu()
        elif number == 13:
            planner.planner_menu()



if __name__ == "__main__":
    main()
