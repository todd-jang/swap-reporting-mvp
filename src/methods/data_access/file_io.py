# swap_reporting_mvp/data_access/file_io.py

# 이 파일은 가상 파일 시스템 상호작용 함수를 정의합니다.
# 실제 프로젝트에서는 os, shutil 등 사용 또는 클라우드 스토리지 SDK 사용
import os
import datetime

# 가상 파일 저장소 (실제 파일 시스템 아님)
_file_contents = {}

def read_incoming_file(file_path):
    """가상 입력 파일 읽기."""
    print(f"파일: 입력 파일 읽기 시도 - {file_path}")
    # 실제 파일 시스템에서 읽기
    # try:
    #     with open(file_path, 'r') as f:
    #         content = f.read()
    #     print("파일: 입력 파일 읽기 완료")
    #     return content
    # except FileNotFoundError:
    #     print("파일: 입력 파일 찾을 수 없음")
    #     raise

    # 가상 파일 시스템에서 읽기
    if file_path in _file_contents:
         print("파일: 가상 입력 파일 읽기 완료")
         return _file_contents[file_path]
    else:
         print("파일: 가상 입력 파일 찾을 수 없음")
         raise FileNotFoundError(f"가상 파일 찾을 수 없음: {file_path}")


def append_to_raw_file(file_path, content):
    """가상 원본 데이터 파일에 내용 추가 (TainTube -> /data/.../rec)."""
    print(f"파일: 원본 파일에 추가 시도 - {file_path}")
    # 실제 파일 시스템에서 추가 모드 열기
    # with open(file_path, 'a') as f:
    #     f.write(content)
    _file_contents[file_path] = _file_contents.get(file_path, "") + content
    print("파일: 원본 파일에 추가 완료")


def write_cftc_send_file(process_date: datetime.date, report_content):
    """가상 CFTC 보고 파일 쓰기 (TainBat -> /data/.../send)."""
    dir_path = f"/data/{process_date.strftime('%Y%m%d')}/send"
    file_path = f"{dir_path}/report.txt" # 가상 파일 경로
    print(f"파일: 보고 파일 쓰기 시도 - {file_path}")
    # 실제 디렉터리 생성 및 파일 쓰기
    # os.makedirs(dir_path, exist_ok=True)
    # with open(file_path, 'w') as f:
    #     f.write(report_content)
    _file_contents[file_path] = report_content
    print("파일: 보고 파일 쓰기 완료")
    return file_path

def read_send_file(process_date: datetime.date):
    """가상 전송할 보고 파일 읽기 (Vo fep <- /data/.../send)."""
    file_path = f"/data/{process_date.strftime('%Y%m%d')}/send/report.txt" # 가상 파일 경로
    return read_incoming_file(file_path) # 가상 읽기 함수 재사용

# TODO: 다른 필요한 파일 시스템 상호작용 함수 추가
