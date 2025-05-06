# tests/test_e2e_ui.py

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager # ChromeDriver 자동 설치/업데이트

# 테스트 대상 웹 애플리케이션 URL
BASE_URL = "http://localhost:8080" # TainWeb 웹 서버 URL (실제 URL로 교체)

# pytest fixture를 사용하여 웹드라이버 인스턴스를 설정/해제
@pytest.fixture(scope="session") # 세션 스코프: 전체 테스트 세션 동안 한 번만 실행
def browser():
    """Selenium WebDriver (Chrome) 인스턴스를 제공."""
    # Chrome WebDriver 설정
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # GUI 없이 백그라운드 실행 (CI 환경 등에서 유용)
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')

    # WebDriverManager를 사용하여 ChromeDriver 자동 설치/업데이트
    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
    driver.implicitly_wait(10) # 요소를 찾을 때까지 최대 10초 대기
    yield driver # 테스트 함수에 driver 객체 제공
    driver.quit() # 테스트 세션 완료 후 브라우저 닫기


class TestFrontendE2E:
    """
    TainWeb (웹 UI) 에 대한 End-to-End 기능 테스트.
    (아키텍처 다이어그램의 'TainWeb' 관련)
    """

    def test_user_login_and_access_report_page(self, browser):
        """일반 사용자 로그인 후 보고서 페이지에 접근 가능한지 테스트."""
        browser.get(BASE_URL + "/login") # 로그인 페이지 URL

        # 로그인 폼 요소 찾기 및 값 입력
        # TODO: 실제 HTML 요소 ID/이름에 맞게 수정
        username_input = browser.find_element(By.ID, "username")
        password_input = browser.find_element(By.ID, "password")
        login_button = browser.find_element(By.XPATH, "//button[text()='Login']") # 버튼 텍스트로 찾기 예시

        username_input.send_keys("testuser") # 가상 사용자 이름
        password_input.send_keys("password123") # 가상 비밀번호
        login_button.click()

        # 로그인 성공 후 리다이렉트될 페이지의 요소가 나타날 때까지 대기
        # TODO: 로그인 성공 후 이동하는 페이지의 실제 요소 ID/클래스에 맞게 수정
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "report-dashboard"))
        )

        # 보고서 페이지 URL로 이동 (또는 클릭을 통해 이동)
        browser.get(BASE_URL + "/reports") # 보고서 페이지 URL

        # 보고서 페이지 내용 또는 요소가 올바르게 표시되는지 확인
        # TODO: 보고서 페이지의 실제 요소 ID/클래스/텍스트에 맞게 수정
        report_title = browser.find_element(By.TAG_NAME, "h1")
        assert report_title.text == "CFTC Swap Reports"

        # 특정 보고서 목록 요소가 로드되었는지 확인
        report_list_item = browser.find_element(By.CLASS_NAME, "report-item")
        assert report_list_item.is_displayed() # 요소가 화면에 표시되는지 확인

        pass # TODO: 실제 테스트 코드 구현

    @pytest.mark.xfail(reason="Admin access test may fail if admin UI is separate or logic is different") # 실패 예상 표시
    def test_admin_user_login_and_access_admin_page(self, browser):
        """관리자 사용자 로그인 후 관리자 전용 페이지에 접근 가능한지 테스트."""
        # 일반 사용자 로그인 테스트와 유사하게 진행
        browser.get(BASE_URL + "/login")

        username_input = browser.find_element(By.ID, "username")
        password_input = browser.find_element(By.ID, "password")
        login_button = browser.find_element(By.XPATH, "//button[text()='Login']")

        username_input.send_keys("admin") # 가상 관리자 사용자 이름
        password_input.send_keys("admin123") # 가상 관리자 비밀번호
        login_button.click()

        # 관리자 전용 페이지로 이동 (로그인 후 자동 이동 또는 수동 이동)
        # TODO: 관리자 전용 페이지의 실제 URL에 맞게 수정
        browser.get(BASE_URL + "/admin/dashboard")

        # 관리자 전용 페이지의 내용 또는 요소가 올바르게 표시되고, 일반 사용자는 볼 수 없는 요소가 보이는지 확인
        # TODO: 실제 요소에 맞게 수정
        admin_panel_title = browser.find_element(By.TAG_NAME, "h1")
        assert admin_panel_title.text == "Admin Dashboard"

        # 예: 보고서 생성 트리거 버튼이 보이는지 확인 (관리자만 볼 수 있는 기능 가정)
        # report_trigger_button = browser.find_element(By.ID, "trigger-report-button")
        # assert report_trigger_button.is_displayed()

        pass # TODO: 실제 테스트 코드 구현

    # TODO: 여기에 다른 E2E 기능 테스트 추가 (예: 보고서 생성 요청 시도, 데이터 업로드 UI 테스트 등)
