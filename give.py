import requests
import main
import sys

BASE_URL = "http://yh6un.ddns.net:8000"
API_KEY = "booth-api-key"

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def get_user_info(nickname):
    """특정 닉네임의 유저 정보를 조회합니다."""
    try:
        response = requests.get(f"{BASE_URL}/api/users/{nickname}", headers=HEADERS)
        data = response.json()
        
        if response.status_code == 200 and data.get("success"):
            print(f"[{nickname}]님의 현재 포인트: {data['user']['points']}")
            return data
        else:
            print(f"유저 조회 실패: {data.get('message', '알 수 없는 오류')}")
            return None
    except Exception as e:
        print(f"API 통신 오류: {e}")
        return None

def give_points(nickname, delta):
    """
    특정 유저에게 일정량의 포인트를 지급하거나 차감합니다.
    (amount가 양수면 지급, 음수면 차감)
    """
    payload = {
        "delta": delta
    }

    try:
        names = []
        for user in main.get_queue():
            names.append(user['nickname'])
        if nickname in names:
            print('Error; 현재 베팅 중인 플레이어입니다.')
            sys.exit()
        requests.post(f'{BASE_URL}/api/users/{nickname}/points/adjust', json=payload, headers=HEADERS)
        print(f'성공적으로 {nickname}님의 포인트를 조정했습니다! (변화율: {delta})')
    except Exception as e:
        print(f"포인트 수정 API 통신 오류: {e}")
        return False

if __name__ == "__main__":
    while True:
        target_user = input('유저 입력(" ;;exit " 입력 시 종료) : ')

        if target_user == ';;exit':
            break
        
        # 1. 유저 정보 먼저 확인
        if get_user_info(target_user) == None:
            sys.exit()

        delta = int(input('조정 포인트 입력(+지급, -차감) : '))

        give_points(target_user, delta)