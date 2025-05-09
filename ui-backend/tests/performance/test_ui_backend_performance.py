# tests/performance/test_ui_backend_performance.py

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest # pytest 사용 시 테스트 함수로 정의

# 테스트 대상 API URL (로컬에서 실행 시)
API_URL = "http://127.0.0.1:8000"

# 성능 테스트 설정
NUM_CONCURRENT_USERS = 10 # 동시에 요청을 보낼 스레드 수
NUM_REQUESTS_PER_USER = 50 # 각 스레드가 보낼 요청 수
TEST_PROMPT = "최근 이상 거래 조회" # 테스트에 사용할 Prompt

def send_prompt_request(prompt: str):
    """Prompt 처리 요청을 보내고 응답 시간을 측정하는 함수."""
    start_time = time.time()
    try:
        response = requests.post(f"{API_URL}/process_prompt", json={"prompt": prompt}, timeout=10) # 10초 타임아웃
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        end_time = time.time()
        return (end_time - start_time, response.status_code, None) # 응답 시간, 상태 코드, 오류 없음
    except requests.exceptions.RequestException as e:
        end_time = time.time()
        return (end_time - start_time, None, e) # 응답 시간, 상태 코드 (없음), 오류

def send_cached_results_request(limit: int):
    """캐시 결과 조회 요청을 보내고 응답 시간을 측정하는 함수."""
    start_time = time.time()
    try:
        response = requests.get(f"{API_URL}/cached_results", params={"limit": limit}, timeout=10)
        response.raise_for_status()
        end_time = time.time()
        return (end_time - start_time, response.status_code, None)
    except requests.exceptions.RequestException as e:
        end_time = time.time()
        return (end_time - start_time, None, e)


# pytest 테스트 함수로 정의
# @pytest.mark.skip(reason="성능 테스트는 별도로 실행") # 필요시 주석 해제하여 pytest 실행에서 제외
def test_process_prompt_performance():
    print(f"\n--- 성능 테스트 시작: /process_prompt ({NUM_CONCURRENT_USERS} 사용자, 각 {NUM_REQUESTS_PER_USER} 요청) ---")

    request_times = []
    successful_requests = 0
    failed_requests = 0

    # ThreadPoolExecutor를 사용하여 동시 요청 시뮬레이션
    with ThreadPoolExecutor(max_workers=NUM_CONCURRENT_USERS) as executor:
        # 모든 요청을 제출
        future_to_request = {
            executor.submit(send_prompt_request, TEST_PROMPT): i
            for i in range(NUM_CONCURRENT_USERS * NUM_REQUESTS_PER_USER)
        }

        # 요청 완료를 기다리고 결과 처리
        for future in as_completed(future_to_request):
            request_index = future_to_request[future]
            try:
                elapsed_time, status_code, error = future.result()
                if error:
                    failed_requests += 1
                    print(f"  요청 {request_index} 실패: {error}")
                else:
                    successful_requests += 1
                    request_times.append(elapsed_time)
                    # print(f"  요청 {request_index} 완료: {elapsed_time:.4f} 초 (상태: {status_code})")
            except Exception as exc:
                failed_requests += 1
                print(f"  요청 {request_index} 처리 중 예외 발생: {exc}")

    print("\n--- 성능 테스트 결과 ---")
    total_requests = NUM_CONCURRENT_USERS * NUM_REQUESTS_PER_USER
    print(f"총 요청 수: {total_requests}")
    print(f"성공 요청 수: {successful_requests}")
    print(f"실패 요청 수: {failed_requests}")
    if successful_requests > 0:
        print(f"평균 응답 시간: {sum(request_times) / successful_requests:.4f} 초")
        print(f"최소 응답 시간: {min(request_times):.4f} 초")
        print(f"최대 응답 시간: {max(request_times):.4f} 초")
        # 중앙값, 90분위수 등 추가 통계 계산 가능
        # 초당 처리량 (요청/초) 계산: 성공 요청 수 / (전체 테스트 시간) - 실제 부하 도구가 더 정확
        # 대략적인 처리량: total_requests / max(request_times) if max(request_times) > 0 else 0
    else:
        print("성공한 요청이 없어 통계 계산 불가.")

    assert failed_requests == 0 # 모든 요청이 성공했는지 확인 (엄격한 기준)
    assert successful_requests == total_requests


# TODO: /cached_results 엔드포인트에 대한 성능 테스트 함수 추가
# def test_cached_results_performance():
#    # 유사한 방식으로 구현
#    pass

# 이 파일을 직접 실행하여 테스트할 수도 있습니다 (pytest 없이).
# if __name__ == "__main__":
#     # FastAPI 애플리케이션을 별도의 터미널에서 먼저 실행해야 합니다.
#     # uvicorn ui_backend.api:app --reload
#     test_process_prompt_performance()
