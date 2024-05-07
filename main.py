from manager import log_manager

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
import time
import pandas as pd
from openpyxl import load_workbook
import os
import sys

# pyinstaller -n "식품안전나라_크롤링_프로그램_ver1.2" --clean --onefile main.py

def get_urls_from_cvs(path):
    webpage_names = []
    webpage_urls = []
    
    data = pd.read_csv(path)
    
    webpage_names = data["이름"].to_list()
    webpage_urls = data["링크"].to_list()
    
    return webpage_names, webpage_urls
    
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
    # chrome_options.add_argument("headless")
    driver = webdriver.Chrome(options=chrome_options, service=service)
    return driver

def find_items(logger: log_manager.Logger, driver: WebDriver, url, end_date):
    
    logger.log_info(f"URL 주소 {url}의 크롤링을 시작하였습니다.")
    
    driver.implicitly_wait(10)
    driver.get(url)
    
    time.sleep(5)
    
    #한 페이지에 표시되는 제품을 50개로 설정
    show_cnt = Select(driver.find_element(By.ID, 'show_cnt'))
    show_cnt.select_by_value("50")
    show_btn = driver.find_element(By.ID, 'show_cnt-btn')
    actions = ActionChains(driver).move_to_element(show_btn)
    actions.perform()
    show_btn.click()
    
    time.sleep(5)
    
    is_found_end_date = False
    
    while(not is_found_end_date):
        
        logger.log_info("이 페이지에서 제품 크롤링 시작 지점을 찾는 중입니다.")
        
        table_contents = driver.find_element(By.CLASS_NAME, "mobile_table").find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
        for table_content in table_contents:
            upload_date = table_content.find_elements(By.TAG_NAME, "td")[4].find_element(By.CLASS_NAME, "table_txt").text
            upload_date = time.strptime(upload_date, "%Y-%m-%d")
            if end_date >= upload_date:
                actions = ActionChains(driver).move_to_element(table_content)
                actions.perform()
                table_content.click()
                time.sleep(5)
                logger.log_info("크롤링 시작 제품을 찾아서 크롤링을 시작합니다.")
                return
        
        driver.find_element(By.CLASS_NAME, "page-link.next").click()
        time.sleep(5)

def find_item_by_id(logger: log_manager.Logger, driver: WebDriver, url, item_id):

    driver.get(url)
    
    time.sleep(5)
    
    #한 페이지에 표시되는 제품을 50개로 설정
    show_cnt = Select(driver.find_element(By.ID, 'show_cnt'))
    show_cnt.select_by_value("50")
    show_btn = driver.find_element(By.ID, 'show_cnt-btn')
    actions = ActionChains(driver).move_to_element(show_btn)
    actions.perform()
    show_btn.click()
    
    time.sleep(5)
    
    while(True):
        
        table_contents = driver.find_element(By.CLASS_NAME, "mobile_table").find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
        for table_content in table_contents:
            id = table_content.find_elements(By.TAG_NAME, "td")[3].find_element(By.CLASS_NAME, "table_txt").text
            if item_id == id:
                actions = ActionChains(driver).move_to_element(table_content)
                actions.perform()
                table_content.click()
                logger.log_debug("크롤링 중단점 발견 및 클릭 완료.")
                logger.log_info("크롤링 시작 제품을 찾아서 크롤링을 시작합니다.")
                time.sleep(5)
                return
        
        driver.find_element(By.CLASS_NAME, "page-link.next").click()
        time.sleep(5)
        logger.log_info("이 페이지에서 제품을 발견 하지 못하여 다음 페이지를 로드합니다.")

def get_item_info(logger: log_manager.Logger, driver: WebDriver, url, start_date):
    
    datas = list()
    
    is_found_start_date = False
    
    while(not is_found_start_date):
        data = []
        
        article_element = driver.find_element(By.TAG_NAME, "article")
        
        #건강 기능 식품 정보 테이블
        table_rows = article_element.find_element(By.TAG_NAME, "table").find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
        for row in table_rows:
            text = row.find_element(By.TAG_NAME, "td").text
            data.append(text)
        
        #기능성 원재료 정보
        first_div_rows = article_element.find_elements(By.TAG_NAME, "div")[0].find_element(By.TAG_NAME, "table").find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
        
        text = ""
        for row in first_div_rows:
            tds = row.find_elements(By.TAG_NAME, 'td')
            if len(tds) > 1:
                if row != first_div_rows[-1]:
                    text += f"{tds[1].text};"
                else:
                    text += f"{tds[1].text}"
        data.append(text)
        #기타 원재료 정보
        second_div_rows = article_element.find_elements(By.TAG_NAME, "div")[1].find_element(By.TAG_NAME, "table").find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")
        text = ""
        for row in second_div_rows:
            tds = row.find_elements(By.TAG_NAME, 'td')
            if len(tds) > 1:
                if row != second_div_rows[-1]:
                    text += f"{tds[1].text};"
                else:
                    text += f"{tds[1].text}"
        data.append(text)
        
        if start_date > time.strptime(data[3], "%Y-%m-%d"):
            is_found_start_date = True
        
        if not is_found_start_date:
            datas.append(data)
            logger.log_info(f"{data[1]} ({data[3]}) 정보 수집 완료!")
            driver.find_element(By.CLASS_NAME, "prev-btn-wrap").find_elements(By.TAG_NAME, "a")[1].click()
            time.sleep(5)
            
            try:
                alert = driver.switch_to.alert
                alert.accept()
                
                logger.log_debug("알림창을 감지 하였습니다.")
                
                find_item_by_id(logger=logger, driver=driver, url=url, item_id=data[2])
                driver.find_element(By.CLASS_NAME, "prev-btn-wrap").find_elements(By.TAG_NAME, "a")[1].click()
            
            except NoAlertPresentException:
                pass
            except Exception as e:
                logger.log_error(e)
                
    return datas

def save_datas_to_excel_file(logger: log_manager.Logger, datas: list, output_name, start_date, end_date):
    
    path = f"./output/{output_name}.xlsx"
    
    data = dict()
    data["업소명"] = list()
    data["제품명"] = list()
    data["신고번호"] = list()
    data["등록일자"] = list()
    data["소비기한"] = list()
    data["성상"] = list()
    data["섭취량/섭취 방법"] = list()
    data["포장재질"] = list()
    data["포장방법"] = list()
    data["보존 및 유통기준"] = list()
    data["섭취시주의사항"] = list()
    data["기능성 내용"] = list()
    data["기준 및 규격"] = list()
    data["기능성 원재료 정보"] = list()
    data["기타 원재료 정보"] = list()
    
    for item_data in datas:
        data["업소명"].append(item_data[0])
        data["제품명"].append(item_data[1])
        data["신고번호"].append(item_data[2])
        data["등록일자"].append(item_data[3])
        data["소비기한"].append(item_data[4])
        data["성상"].append(item_data[5])
        data["섭취량/섭취 방법"].append(item_data[6])
        data["포장재질"].append(item_data[7])
        data["포장방법"].append(item_data[8])
        data["보존 및 유통기준"].append(item_data[9])
        data["섭취시주의사항"].append(item_data[10])
        data["기능성 내용"].append(item_data[11])
        data["기준 및 규격"].append(item_data[12])
        data["기능성 원재료 정보"].append(item_data[13])
        data["기타 원재료 정보"].append(item_data[14])
    
    data_frame = pd.DataFrame(data)
    data_frame.to_excel(path, index=False, startrow=2)
    
    workbook = load_workbook(path , data_only=True )
    worksheet = workbook.active
    worksheet["A1"] = "검색기간(시작)"
    worksheet["A2"] = "검색기간(종료)"
    worksheet["B1"] = start_date
    worksheet["B2"] = end_date
    workbook.save(path)
    
    logger.log_info(f"엑셀 파일 {output_name} 저장 완료!")

if __name__ == '__main__':
    try:
        logger = log_manager.Logger(log_manager.LogType.BUILD)
        os.makedirs("./output", exist_ok=True)
        
        webpage_names, webpage_urls = get_urls_from_cvs("./setting.csv")
        
        logger.log_info(f"크롤링 대상 웹사이트 {len(webpage_urls)}개를 발견하였습니다.")
        
        driver = get_chrome_driver(logger)
        
        for i in range(len(webpage_urls)):
            logger.log_info("기간 설정을 위해 시작과 종료 날짜를 입력해주세요.")
            logger.log_info("반드시 YYYY-MM-DD의 양식으로 입력 해주세요.")
            
            start_date = input("검색 시작 날짜 : ")
            end_date = input("검색 종료 날짜 : ")
            
            logger.log_info(f"{start_date}~{end_date}로 기간 설정을 완료하였습니다.")
            
            file_name = f"{webpage_names[i]}_{start_date}~{end_date}_검색결과"
            start_date_time = time.strptime(start_date, "%Y-%m-%d")
            end_date_time = time.strptime(end_date, "%Y-%m-%d")
        
            find_items(logger, driver, webpage_urls[i], end_date_time)
            
            datas = get_item_info(logger, driver, webpage_urls[i], start_date_time)
            
            save_datas_to_excel_file(logger, datas, file_name, start_date, end_date)
    except Exception as e:
        logger.log_error(f"다음과 같은 오류로 프로그램을 종료합니다. 프로그램을 재실행 해주세요.: {e}")
    finally:
        driver.quit()
        program_exit = input("프로그램 종료를 위해 엔터키를 눌러주세요.")
        sys.exit()