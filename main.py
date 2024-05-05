from manager import log_manager

from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc 
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium_stealth import stealth
from datetime import datetime
import time

# pyinstaller -n "HOOPCITY_KASINA_MONITORING_PROGRAM_1.3" --clean --onefile main.py

def get_chrome_driver(logger: log_manager.Logger):
    # Chrome driver Manager를 통해 크롬 드라이버 자동 설치 > 최신 버전을 설치 > Service에 저장
    service = Service(excutable_path=ChromeDriverManager().install())
    chrome_options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    chrome_options.add_argument('user-agent=' + user_agent)
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-blink-features=AnimationControlled")
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--log-level=3') # 브라우저 로그 레벨을 낮춤
    chrome_options.add_argument('--disable-loging') # 로그를 남기지 않음
    #chrome_options.add_argument("headless")
    driver = webdriver.Chrome(options=chrome_options, service=service)
    return driver

def get_item_links(logger: log_manager.Logger, url, start_date, end_date):
    driver = get_chrome_driver(logger)
    driver.implicitly_wait(10)
    driver.get(url)
    
    #한 페이지에 표시되는 제품을 50개로 설정
    show_cnt = Select(driver.find_element(By.ID, 'show_cnt'))
    show_cnt.select_by_value("50")
    driver.find_element(By.ID, 'show_cnt-btn').click()
    time.sleep(5)
    
    is_found_end_date = False
    
    while(not is_found_end_date):
        table_contents = driver.find_element(By.CLASS_NAME, "mobile_table").find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
        for table_content in table_contents:
            upload_date = table_content.find_elements(By.TAG_NAME, "td")[4].find_element(By.CLASS_NAME, "table_txt").text
            upload_date = time.strptime(upload_date, "%Y-%m-%d")
            if end_date >= upload_date:
                print("종료 일자 찾음")
                table_content.click()
                time.sleep(5)
                is_found_end_date = True
        if not is_found_end_date:
            driver.find_element(By.CLASS_NAME, "page-link.next").click()
            time.sleep(5)

if __name__ == '__main__':
    logger = log_manager.Logger(log_manager.LogType.DEBUG)
    url = "https://www.foodsafetykorea.go.kr/portal/healthyfoodlife/searchHomeHF.do?menu_grp=MENU_NEW01&menu_no=2823"
    start_date = input("검색 시작 날짜 : ")
    end_date = input("검색 종료 날짜 : ")
    
    start_date = time.strptime(start_date, "%Y-%m-%d")
    end_date = time.strptime(end_date, "%Y-%m-%d")
    
    get_item_links(logger, url, start_date, end_date)
    pass