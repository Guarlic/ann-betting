import requests
import time

# --- 설정 값 ---
BASE_URL = "http://yh6un.ddns.net:8000"
API_KEY = "booth-api-key"

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def get_queue():
    """현재 승부 예측 참가자 목록을 불러옵니다."""
    try:
        response = requests.get(f"{BASE_URL}/api/queue", headers=HEADERS)
        data = response.json()
        if data.get("success"):
            return data.get("queue", [])
        else:
            print("Queue 조회 실패:", data)
            return []
    except Exception as e:
        print(f"Queue API 통신 오류: {e}")
        return []

def calculate_multiplier(selected_team, winner_team, red_pool, blue_pool):
    """
    팀별 누적 포인트(Pool)에 비례하여 승리 팀의 배율을 계산합니다.
    """
    # 선택한 팀이 졌을 경우 배율은 0
    if selected_team != winner_team:
        return 0.0

    total_pool = red_pool + blue_pool
    winner_pool = red_pool if winner_team == "red" else blue_pool
    
    # 승리팀에 베팅한 포인트가 0일 경우 (0으로 나누기 방지)
    if winner_pool == 0:
        return 1.0 

    # 전체 베팅 포인트를 승리 팀의 총 베팅 포인트로 나눔 (소수점 2자리 반올림)
    multiplier = round(total_pool / winner_pool, 2)
    return multiplier

def apply_points(nickname, multiplier):
    """계산된 배율을 API 서버로 보내 포인트를 정산합니다."""
    payload = {
        "nickname": nickname,
        "multiplier": multiplier
    }
    try:
        response = requests.post(f"{BASE_URL}/api/points/apply", json=payload, headers=HEADERS)
        return response.json()
    except Exception as e:
        print(f"포인트 정산 API 통신 오류 ({nickname}): {e}")
        return None

def clear_queue():
    """정산이 모두 끝난 후 Queue를 초기화합니다."""
    try:
        response = requests.delete(f"{BASE_URL}/api/queue", headers=HEADERS)
        return response.json()
    except Exception as e:
        print(f"Queue 초기화 API 통신 오류: {e}")
        return None

def process_match_end(winner_team):
    """경기가 종료되었을 때 실행되는 메인 정산 프로세스"""
    print(f"\n=== 경기 종료! 승리 팀: [{winner_team.upper()}] ===")

    # 1. Queue 조회
    queue = get_queue()
    if not queue:
        print("이번 경기에 참가한 유저가 없습니다.")
        return

    # 2. 팀별 총 베팅 포인트(Pool) 계산
    red_pool = sum(player.get("investment_points", 0) for player in queue if player.get("selected_team") == "red")
    blue_pool = sum(player.get("investment_points", 0) for player in queue if player.get("selected_team") == "blue")
    total_pool = red_pool + blue_pool
    
    print(f"💰 [베팅 현황] RED팀: {red_pool}P / BLUE팀: {blue_pool}P (총 {total_pool}P)")

    # 3. 개별 참가자 정산
    print(f"총 {len(queue)}명의 참가자 정산을 시작합니다...")
    for player in queue:
        nickname = player["nickname"]
        
        # 이미 정산 처리된 유저면 건너뜀 (중복 정산 방지)
        if player.get("settled"):
            continue

        # Pool 비례 배율 계산
        multiplier = calculate_multiplier(
            player["selected_team"], 
            winner_team,
            red_pool,
            blue_pool
        )

        result = apply_points(nickname, multiplier)
        
        if result and result.get("success"):
            after_points = result.get("after")
            print(f" ✅ [{nickname}] 정산 완료! (적용 배율: {multiplier}배) -> 남은 포인트: {after_points}")
        else:
            print(f" ❌ [{nickname}] 정산 실패!")

    # 4. Queue 초기화
    print("\nQueue 초기화를 진행합니다...")
    clear_result = clear_queue()
    if clear_result and clear_result.get("success"):
        deleted_count = clear_result.get('deleted', 0)
        print(f"완료: {deleted_count}건의 데이터가 삭제되었습니다. 다음 판 준비 완료!")
    else:
        print("Queue 초기화에 실패했습니다. 수동 확인이 필요합니다.")


# --- 실제 실행 부분 (테스트) ---
if __name__ == "__main__":
    while True:
        # 편의성을 위해 입력값의 공백 제거 및 소문자 변환(strip, lower)을 추가했습니다.
        actual_winner = input('승리 팀 입력(red/blue) : ').strip().lower()
        
        if actual_winner not in ['red', 'blue']:
            print('승리 팀 이름 잘못됨; 오탈자 확인 바람.')
            continue
            
        # assumed_win_rate 입력은 배팅 포인트 비례 방식이므로 제거했습니다.
        break
    
    process_match_end(actual_winner)