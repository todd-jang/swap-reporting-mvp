테스트 실행 방법:

가상 구성 요소 모듈 파일(vb_api_svr.py 등)을 프로젝트에 추가합니다. 실제 구현체로 교체해야 합니다.

tests/ 디렉터리 안에 생성된 테스트 파일들을 추가합니다.

프로젝트 루트 디렉터리에서 터미널을 열고 다음 명령어를 실행하여 pytest 테스트를 실행합니다.

Bash

pytest
또는 특정 파일만 실행:

Bash

pytest tests/test_unit.py
pytest tests/test_integration.py
pytest tests/test_data_process.py
Selenium 테스트를 실행하려면 웹 서버(TainWeb)가 실행 중이어야 합니다.

Selenium 테스트를 위해 ChromeDriver가 필요합니다. webdriver-manager를 사용하면 자동으로 관리됩니다. --headless 옵션을 사용하지 않으면 브라우저 창이 열립니다.
