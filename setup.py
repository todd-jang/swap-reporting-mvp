from setuptools import setup, find_packages

# requirements.txt 파일에서 의존성 목록을 읽어오는 함수 (필요시)
def parse_requirements(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith('#')]

setup(
    name='swap_reporting_mvp_ui_backend', # 패키지 이름
    version='0.1.0', # 패키지 버전
    packages=find_packages(where='.'), # 현재 디렉터리 기준으로 패키지 탐색
    include_package_data=True, # MANIFEST.in에 정의된 비코드 파일 포함
    install_requires=parse_requirements('requirements.txt'), # 의존성 설치

    # 패키지 메타데이터
    author='Your Name',
    author_email='your.email@example.com',
    description='Backend API service for Swap Reporting MVP UI',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='http://your-project-url.com', # 프로젝트 URL (선택 사항)
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9', # 사용하는 Python 버전
        'License :: OSI Approved :: MIT License', # 라이선스
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9', # 요구하는 Python 최소 버전

    # 실행 가능한 스크립트 또는 콘솔 진입점을 만들 경우 (선택 사항)
    # entry_points={
    #     'console_scripts': [
    #         'run-ui-backend=ui_backend.api:main', # 예: ui_backend.api 모듈의 main 함수 실행
    #     ],
    # },
)
