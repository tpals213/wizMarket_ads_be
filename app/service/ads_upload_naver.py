from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyperclip
import pyautogui
import time
from PIL import ImageGrab, Image
import os
import cv2
from dotenv import load_dotenv


load_dotenv()

def upload_naver_ads(content, store_name, tag, file_path):
    naver_id = os.getenv("NAVER_PID")
    naver_pw = os.getenv("NAVER_PPW")

    driver = login_to_naver(naver_id, naver_pw)
    formatted_tag = f"#{tag.strip()}"  
    
    contents = {
        "Title": store_name,
        "Contents": content,
        "Hashtags": formatted_tag
    }
    publish_blog_post(driver, contents, file_path)
    # print(type(store_name))
    if os.path.exists(file_path):
        os.remove(file_path)

# 이미지 클립보드 복사 함수
def copy_image_to_clipboard(image_path):
    image = Image.open(image_path)  # 이미지 열기
    image.show()  # 클립보드에 복사되도록 열기 (Windows 기본 이미지 뷰어)
    time.sleep(0.5) 
    pyautogui.hotkey("ctrl", "c")  # Ctrl + C 입력
    pyautogui.hotkey("alt", "f4")  # 활성 창 닫기
    image.close() 
    

def login_to_naver(username, password):
    # 크롬 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized") 
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")  # 브라우저 창 숨기기
    # chrome_options.add_argument("--disable-gpu")  # GPU 가속 비활성화 (일부 환경에서 필요)
    # chrome_options.add_argument("--disable-dev-shm-usage")  # /dev/shm 용량 문제 해결
    

    # 크롬 드라이버 초기화
    chrome_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    driver.set_window_position(3000, 3000)
    # 자동 로그인할 웹사이트 열기
    driver.get('https://nid.naver.com/nidlogin.login')

    # 로딩 대기
    time.sleep(2)

    # 아이디 입력 필드 찾기
    id_field = driver.find_element(By.XPATH, "//*[@id='id']")

    # 아이디 입력
    pyperclip.copy(username)
    id_field.click()
    id_field.send_keys(Keys.CONTROL, 'v')
    time.sleep(1)  # 로딩 대기

    # 패스워드 입력 필드 찾기
    password_field = driver.find_element(By.XPATH, "//*[@id='pw']")

    # 패스워드 입력
    pyperclip.copy(password)
    password_field.click()
    password_field.send_keys(Keys.CONTROL, 'v')
    time.sleep(1)  # 로딩 대기

    # 로그인 버튼 클릭
    login_button = driver.find_element(By.XPATH, '//*[@id="log.login"]')
    login_button.click()

    # 로그인 후의 추가적인 처리가 필요한 경우를 위해 대기
    time.sleep(1)

    return driver

# 함수 사용 예:
# driver = login_to_naver('your_naver_username', 'your_naver_password')


def publish_blog_post(driver, contents, file_path):
    try:
        # # 네이버 메인 페이지로 이동
        # driver.get('https://www.naver.com')

        # 블로그 버튼 클릭
        blog_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[2]/div/div[2]/div/div[1]/div[1]/div[2]/div/div/ul/li[3]/a/span[1]"))
        )
        blog_button.click()
        time.sleep(1)

        # 글쓰기 버튼 클릭
        write_post_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[2]/div/div[2]/div/div[1]/div[1]/div[3]/div[2]/div[2]/a'))
        )
        write_post_button.click()
        time.sleep(1)
        
        # 새 창 전환
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[1])

        # iframe 전환
        WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'mainFrame')))
        time.sleep(1)

        # "작성 중인 글이 있습니다." 팝업 처리
        try:
            cancel_button = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[3]/div/div/div[1]/div/div[4]/div[2]/div[3]/button[1]')))
            cancel_button.click()
        except Exception as e:
            print("* No draft popup appeared.")


        # 닫기 버튼 클릭
        try:
            close_button = driver.find_element(By.XPATH, "//button[@type='button' and contains(@class, 'se-help-panel-close-button')]")
            close_button.click()
        except Exception as e:
            print("No right side popup appeared.")

        title_field_xpath = "//span[contains(@class, 'se-placeholder') and text()='제목']"
        content_field_xpath = '/html/body/div[1]/div/div[3]/div/div/div[1]/div/div[1]/div[2]/section/article/div[2]/div/div/div/div/p'
        publish_button_xpath = '//*[@id="root"]/div/div[1]/div/div[3]/div[2]/button'
        option1_xpath = '//*[@id="root"]/div/div[1]/div/div[3]/div[2]/div/div/div/div[4]/div/div/ul/li[1]/span/label'
        option2_xpath = '//*[@id="root"]/div/div[1]/div/div[3]/div[2]/div/div/div/div[4]/div/div/ul/li[2]/span/label'
        option3_xpath = '//*[@id="root"]/div/div[1]/div/div[3]/div[2]/div/div/div/div[4]/div/div/ul/li[3]/span/label'
        option4_xpath = '//*[@id="root"]/div/div[1]/div/div[3]/div[2]/div/div/div/div[4]/div/div/ul/li[4]/span/label'
        option5_xpath = '//*[@id="root"]/div/div[1]/div/div[3]/div[2]/div/div/div/div[4]/div/div/ul/li[5]/span/label'
        category_list_xpath = '//*[@id="root"]/div/div[1]/div/div[3]/div[2]/div/div/div/div[1]/div/div/button/span'
        category1_xpath = '//*[@id="root"]/div/div[1]/div/div[3]/div[2]/div/div/div/div[1]/div/div/div[2]/div/ul/li[1]/span/label'
        category2_xpath = '//*[@id="root"]/div/div[1]/div/div[3]/div[2]/div/div/div/div[1]/div/div/div[2]/div/ul/li[2]/span/label'
        
        confirm_button_xpath = '//*[@id="root"]/div/div[1]/div/div[3]/div[2]/div/div/div/div[8]/div/button'


        # 제목 입력
        try:
            title_field = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, title_field_xpath)))
            pyperclip.copy(contents['Title'])
            # print(contents['Title'])
            time.sleep(1)
            title_field.click()
            pyautogui.hotkey('ctrl', 'v')  # 클립보드 내용 붙여넣기
            time.sleep(1)
        except Exception as e:
            print(e)
        # driver.save_screenshot("title.png")

        # 이미지 복사
        image_path = file_path
        copy_image_to_clipboard(image_path)  # 이미지 클립보드에 복사
        
        # 이미지 붙여넣기
        content_field = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, content_field_xpath)))
        content_field.click()
        pyautogui.hotkey('ctrl', 'v')  # 이미지 붙여넣기
        time.sleep(1)
        # driver.save_screenshot("IMAGE.png")
        # 내용 입력
        # content_field = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, content_field_xpath)))
        pyperclip.copy(contents['Contents'])
        # time.sleep(1)
        # content_field.click()
        pyautogui.press('enter')
        pyautogui.press('enter')
        pyautogui.hotkey('ctrl', 'v')  # 클립보드 내용 붙여넣기
        # driver.save_screenshot("CONTENT.png")
        pyautogui.press('enter')
        time.sleep(1)
        pyautogui.press('enter')
        pyautogui.press('enter')
        pyautogui.press('enter')
        pyperclip.copy(contents['Hashtags'])
        pyautogui.hotkey('ctrl', 'v')  # 클립보드 내용 붙여넣기
        # driver.save_screenshot("TAG.png")

        # "발행" 버튼 클릭
        publish_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, publish_button_xpath)))
        publish_button.click()
        # driver.save_screenshot("PUBLISH.png")

        # 발행 후의 처리가 필요한 경우를 위해 대기
        time.sleep(1)

        # 카테고리 선택
        category_list_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, category_list_xpath)))
        category_list_button.click()

        # 두번째 선택
        category2_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, category2_xpath)))
        category2_button.click()

        # 발행 옵션 값 선택
        option1_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, option1_xpath)))
        option1_button.click()
        option2_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, option2_xpath)))
        option2_button.click()
        option3_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, option3_xpath)))
        option3_button.click()
        option4_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, option4_xpath)))
        option4_button.click()
        option5_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, option5_xpath)))
        option5_button.click()

        # "확인" 버튼 클릭"
        confirm_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, confirm_button_xpath)))
        confirm_button.click()
        time.sleep(1)

        print("글쓰기 및 발행 성공")
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        driver.quit()
        if os.path.exists(file_path):
            os.remove(file_path)